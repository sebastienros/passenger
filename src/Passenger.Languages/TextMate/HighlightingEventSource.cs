using System.Diagnostics;
using System.Diagnostics.Tracing;

namespace Passenger.Languages.TextMate;

/// <summary>Opt-in pass diagnostics. No source text or file paths are emitted. Enable the Passenger-Highlighting
/// EventSource with EventPipe or an EventListener; no per-line events are written.</summary>
[EventSource(Name = "Passenger-Highlighting")]
internal sealed class HighlightingEventSource : EventSource
{
    public static readonly HighlightingEventSource Log = new();

    [Event(1, Level = EventLevel.Verbose)]
    public void Pass(long passId, long documentId, int version, int initial, long frequency,
        long workerQueueTicks, long workerTicks, long workerAllocatedBytes,
        long grammarTicks, long grammarAllocatedBytes, long lockWaitTicks,
        long tokenizerTicks, long tokenizerAllocatedBytes, long linePreparationTicks, long linePreparationAllocatedBytes,
        long otherWorkerTicks, long otherWorkerAllocatedBytes, int readLines, int skippedLines, int stoppedLines,
        int unknownStopStatusLines, int documentLines, int staleFrom, int complete) =>
        WriteEvent(1, passId, documentId, version, initial, frequency, workerQueueTicks, workerTicks, workerAllocatedBytes,
            grammarTicks, grammarAllocatedBytes, lockWaitTicks, tokenizerTicks, tokenizerAllocatedBytes,
            linePreparationTicks, linePreparationAllocatedBytes, otherWorkerTicks, otherWorkerAllocatedBytes,
            readLines, skippedLines, stoppedLines, unknownStopStatusLines, documentLines, staleFrom, complete);

    [Event(2, Level = EventLevel.Verbose)]
    public void Publication(long passId, long documentId, int version, int final, long frequency,
        long queueTicks, long callbackTicks, long callbackAllocatedBytes, long sinceScheduledTicks) =>
        WriteEvent(2, passId, documentId, version, final, frequency, queueTicks, callbackTicks, callbackAllocatedBytes, sinceScheduledTicks);
}

/// <summary>One synchronous worker pass's counters, allocated only while diagnostics are enabled. Time values are
/// Stopwatch ticks (Frequency is emitted with each event); allocations count only the executing worker thread.</summary>
internal sealed class HighlightingPass(long documentId, int version, bool initial)
{
    private static long nextId;
    private readonly long id = Interlocked.Increment(ref nextId);
    private readonly long scheduled = Stopwatch.GetTimestamp();
    private long workerStart;
    private long workerBytes;
    private long grammarTicks;
    private long grammarBytes;
    private long tokenizerStart;
    private long tokenizerBytesStart;
    private long tokenizerTicks;
    private long tokenizerBytes;
    private long lockTicks;
    private long lineStarted;
    private long lineBytesStart;
    private long lineTicks;
    private long lineBytes;
    private int readLines;
    private int skippedLines;
    private int stoppedLines;
    private int unknownStopStatusLines;

    public void Start()
    {
        workerStart = Stopwatch.GetTimestamp();
        workerBytes = GC.GetAllocatedBytesForCurrentThread();
    }

    public void GrammarLoaded()
    {
        grammarTicks = Stopwatch.GetTimestamp() - workerStart;
        grammarBytes = GC.GetAllocatedBytesForCurrentThread() - workerBytes;
    }

    public void LockAcquired(long started) => lockTicks += Stopwatch.GetTimestamp() - started;

    public void Reading()
    {
        lineBytesStart = GC.GetAllocatedBytesForCurrentThread();
        lineStarted = Stopwatch.GetTimestamp();
    }

    public void LineRead()
    {
        lineTicks += Stopwatch.GetTimestamp() - lineStarted;
        lineBytes += GC.GetAllocatedBytesForCurrentThread() - lineBytesStart;
    }

    public void SkipLine()
    {
        readLines++;
        skippedLines++;
    }

    public void Tokenizing()
    {
        tokenizerBytesStart = GC.GetAllocatedBytesForCurrentThread();
        tokenizerStart = Stopwatch.GetTimestamp();
    }

    public void Tokenized(bool? stoppedEarly)
    {
        tokenizerTicks += Stopwatch.GetTimestamp() - tokenizerStart;
        tokenizerBytes += GC.GetAllocatedBytesForCurrentThread() - tokenizerBytesStart;
        readLines++;
        if (stoppedEarly is null)
        {
            unknownStopStatusLines++;
        }
        if (stoppedEarly == true)
        {
            stoppedLines++;
        }
    }

    public void Finish(int documentLines, int staleFrom)
    {
        long elapsed = Stopwatch.GetTimestamp() - workerStart;
        long allocated = GC.GetAllocatedBytesForCurrentThread() - workerBytes;
        // Snapshot counters before constructing and emitting the event: the event's own allocations are excluded.
        HighlightingEventSource.Log.Pass(id, documentId, version, initial ? 1 : 0, Stopwatch.Frequency,
            workerStart - scheduled, elapsed, allocated, grammarTicks, grammarBytes, lockTicks,
            tokenizerTicks, tokenizerBytes, lineTicks - tokenizerTicks, lineBytes - tokenizerBytes,
            elapsed - grammarTicks - lockTicks - lineTicks, allocated - grammarBytes - lineBytes,
            readLines, skippedLines, stoppedLines, unknownStopStatusLines, documentLines, staleFrom, staleFrom == documentLines ? 1 : 0);
    }

    /// <summary>Measure a callback on the highlighter's captured context; queue delay excludes the worker itself.</summary>
    public Action Publication(Action action, bool final)
    {
        long queued = Stopwatch.GetTimestamp();
        return () =>
        {
            long started = Stopwatch.GetTimestamp();
            long allocated = GC.GetAllocatedBytesForCurrentThread();
            try
            {
                action();
            }
            finally
            {
                long ticks = Stopwatch.GetTimestamp() - started;
                long bytes = GC.GetAllocatedBytesForCurrentThread() - allocated;
                HighlightingEventSource.Log.Publication(id, documentId, version, final ? 1 : 0, Stopwatch.Frequency,
                    started - queued, ticks, bytes, Stopwatch.GetTimestamp() - scheduled);
            }
        };
    }
}
