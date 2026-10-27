using System.Diagnostics.Tracing;
using System.Globalization;

/// <summary>Aggregates the opt-in events by benchmark phase; no per-line or per-edit trace files are retained.</summary>
internal sealed class HighlightingListener : EventListener
{
    private readonly object gate = new();
    private readonly Dictionary<string, Counters> groups = [];
    private readonly List<string> errors = [];
    public string Phase { get; set; } = "setup";

    protected override void OnEventSourceCreated(EventSource eventSource)
    {
        if (eventSource.Name == "Passenger-Highlighting")
        {
            EnableEvents(eventSource, EventLevel.Verbose);
        }
    }

    protected override void OnEventWritten(EventWrittenEventArgs eventData)
    {
        lock (gate)
        {
            if (eventData.EventId == 0)
            {
                errors.Add(string.Join(";", eventData.Payload ?? []));
                return;
            }
            string key = Phase + "/" + eventData.EventName;
            if (!groups.TryGetValue(key, out Counters? counters))
            {
                groups[key] = counters = new Counters();
            }
            counters.Count++;
            for (int i = 0; i < eventData.Payload!.Count; i++)
            {
                string rawName = eventData.PayloadNames![i];
                string name = char.ToUpperInvariant(rawName[0]) + rawName[1..];
                if (name is "PassId" or "DocumentId" or "Version" or "Frequency")
                {
                    continue;
                }
                double value = Convert.ToDouble(eventData.Payload[i], CultureInfo.InvariantCulture);
                counters.Totals[name] = counters.Totals.GetValueOrDefault(name) + value;
            }
        }
    }

    public object Snapshot()
    {
        lock (gate)
        {
            if (errors.Count != 0 || groups.Count == 0)
            {
                throw new InvalidOperationException("Highlighting diagnostics missing or failed: " + string.Join(";", errors));
            }
            foreach ((string key, Counters pass) in groups.Where(g => g.Key.EndsWith("/Pass", StringComparison.Ordinal)))
            {
                string phase = key[..^5];
                if (!groups.TryGetValue(phase + "/Publication", out Counters? publication)
                    || publication.Totals.GetValueOrDefault("Final") != pass.Count)
                {
                    throw new InvalidOperationException($"Missing final publication for {phase}");
                }
                Dictionary<string, double> t = pass.Totals;
                if (t["WorkerTicks"] != t["GrammarTicks"] + t["LockWaitTicks"] + t["TokenizerTicks"] + t["LinePreparationTicks"] + t["OtherWorkerTicks"]
                    || t["WorkerAllocatedBytes"] != t["GrammarAllocatedBytes"] + t["TokenizerAllocatedBytes"] + t["LinePreparationAllocatedBytes"] + t["OtherWorkerAllocatedBytes"]
                    || t["OtherWorkerTicks"] < 0 || t["OtherWorkerAllocatedBytes"] < 0)
                {
                    throw new InvalidOperationException($"Worker accounting does not reconcile for {phase}");
                }
                int expected = phase.StartsWith("edits-", StringComparison.Ordinal) ? 100 : 1;
                if (pass.Count != expected || t["Complete"] != expected)
                {
                    throw new InvalidOperationException($"Unexpected or incomplete passes for {phase}");
                }
            }
            return new { Frequency = System.Diagnostics.Stopwatch.Frequency, Groups = groups };
        }
    }

    internal sealed class Counters
    {
        public int Count { get; set; }
        public Dictionary<string, double> Totals { get; } = [];
    }
}
