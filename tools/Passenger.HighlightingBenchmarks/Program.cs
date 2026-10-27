using System.Collections.Concurrent;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Passenger.Core;
using Passenger.Editor;
using Passenger.Languages;
using Passenger.Languages.TextMate;
using Passenger.Text;

if (args.Length is not (3 or 4) || (args.Length == 4 && args[3] != "--instrument"))
{
    Console.Error.WriteLine("Usage: Passenger.HighlightingBenchmarks <filename> <repeat-count> <output.json> [--instrument]");
    return 1;
}
string input = File.ReadAllText(args[0]).Replace("\r\n", "\n", StringComparison.Ordinal);
string text = string.Concat(Enumerable.Repeat(input + "\n", int.Parse(args[1], System.Globalization.CultureInfo.InvariantCulture)));
using HighlightingListener? diagnostics = args.Length == 4 ? new HighlightingListener() : null;
Language language = Language.ForPath(args[0]);
Pump context = new();
SynchronizationContext.SetSynchronizationContext(context);
using Process process = Process.GetCurrentProcess();
List<object> samples = [];
TextDocument document = new(text);
TextMateHighlighter? highlighter = null;
string? hash = null;

for (int iteration = 0; iteration < 10; iteration++)
{
    if (diagnostics is not null)
    {
        diagnostics.Phase = $"pass-{iteration}";
    }
    highlighter?.Dispose();
    highlighter = null;
    GC.Collect();
    GC.WaitForPendingFinalizers();
    GC.Collect();
    long heapBefore = GC.GetTotalMemory(false);
    int[] collections = [GC.CollectionCount(0), GC.CollectionCount(1), GC.CollectionCount(2)];
    long allocated = GC.GetTotalAllocatedBytes(true);
    TimeSpan cpu = process.TotalProcessorTime;
    long start = Stopwatch.GetTimestamp();
    highlighter = (TextMateHighlighter?)Highlighters.For(language, document)
        ?? throw new InvalidOperationException("This workload needs a TextMate language.");
    context.Drain();
    double wall = Stopwatch.GetElapsedTime(start).TotalMilliseconds;
    double cpuMs = (process.TotalProcessorTime - cpu).TotalMilliseconds;
    long bytes = GC.GetTotalAllocatedBytes(true) - allocated;
    int[] gc = [GC.CollectionCount(0) - collections[0], GC.CollectionCount(1) - collections[1], GC.CollectionCount(2) - collections[2]];
    if (highlighter.Failure is { } failure)
    {
        throw new InvalidOperationException("Highlighting failed", failure);
    }
    long retained = GC.GetTotalMemory(true) - heapBefore;
    process.Refresh();
    samples.Add(new { phase = iteration == 0 ? "cold" : iteration < 3 ? "warmup" : "warm", wallMs = wall, cpuMs, allocatedBytes = bytes,
        retainedBytes = retained, workingSetBytes = process.WorkingSet64, peakWorkingSetBytes = process.PeakWorkingSet64,
        gc, lines = highlighter.Worked.Lines, workerMs = highlighter.Worked.Time.TotalMilliseconds });
    string current = Hash(highlighter, document);
    if (hash is not null && hash != current)
    {
        throw new InvalidOperationException("Repeated highlighting changed colours");
    }
    hash = current;
}

// An ordinary character replacement, in the middle of the file: preserve its line structure.
int position = text.IndexOfAny(['a', 'e', 'i'], text.Length / 2);
if (position < 0)
{
    throw new InvalidOperationException("No edit position");
}
char original = text[position];
for (int batch = 0; batch < 6; batch++)
{
    if (diagnostics is not null)
    {
        diagnostics.Phase = $"edits-{batch}";
    }
    long lines = highlighter!.Worked.Lines;
    TimeSpan worked = highlighter.Worked.Time;
    long allocated = GC.GetTotalAllocatedBytes(true);
    TimeSpan cpu = process.TotalProcessorTime;
    long start = Stopwatch.GetTimestamp();
    for (int edit = 0; edit < 100; edit++)
    {
        document.Rewrite(position, 1, edit % 2 == 0 ? "z" : original.ToString());
        context.Drain();
        if (highlighter.Failure is { } failure)
        {
            throw new InvalidOperationException("Edit failed", failure);
        }
    }
    samples.Add(new { phase = batch == 0 ? "edit-warmup" : "edit", wallMs = Stopwatch.GetElapsedTime(start).TotalMilliseconds / 100,
        cpuMs = (process.TotalProcessorTime - cpu).TotalMilliseconds / 100,
        allocatedBytes = (GC.GetTotalAllocatedBytes(true) - allocated) / 100.0,
        lines = (highlighter.Worked.Lines - lines) / 100.0, workerMs = (highlighter.Worked.Time - worked).TotalMilliseconds / 100 });
    if (Hash(highlighter, document) != hash)
    {
        throw new InvalidOperationException("Incremental colours differ from a fresh pass");
    }
}
File.WriteAllText(args[2], JsonSerializer.Serialize(new {
    runtime = System.Runtime.InteropServices.RuntimeInformation.FrameworkDescription,
    os = System.Runtime.InteropServices.RuntimeInformation.OSDescription,
    architecture = System.Runtime.InteropServices.RuntimeInformation.ProcessArchitecture.ToString(),
    source = args[0], inputSha256 = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(text))),
    characters = text.Length, lines = document.Snapshot.LineCount, colourHash = hash, samples, diagnostics = diagnostics?.Snapshot()
}, new JsonSerializerOptions { WriteIndented = true }));
highlighter!.Dispose();
return 0;

static string Hash(TextMateHighlighter highlighter, TextDocument document)
{
    StringBuilder result = new();
    foreach (SyntaxSpan span in highlighter.GetSpans(document.Snapshot, 0, document.Snapshot.Length))
    {
        result.Append(System.Globalization.CultureInfo.InvariantCulture, $"{span.Start}:{span.Length}:{(int)span.Kind};");
    }
    return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(result.ToString())));
}

internal sealed class Pump : SynchronizationContext
{
    private readonly BlockingCollection<(SendOrPostCallback Callback, object? State)> queue = new();
    public override void Post(SendOrPostCallback d, object? state) => queue.Add((d, state));
    public void Drain()
    {
        long start = Stopwatch.GetTimestamp();
        while (BackgroundWork.Pending > 0 || queue.Count > 0)
        {
            if (queue.TryTake(out (SendOrPostCallback Callback, object? State) work, 1))
            {
                work.Callback(work.State);
            }
            if (Stopwatch.GetElapsedTime(start) > TimeSpan.FromMinutes(3))
            {
                throw new TimeoutException("Highlighter did not settle");
            }
        }
    }
}
