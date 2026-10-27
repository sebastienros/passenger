# Measuring inside Passenger's highlighter

`Passenger-Highlighting` is an opt-in EventSource in the reference branch’s highlighter; it is absent from the PR’s production code. It works with an in-process EventListener and EventPipe from a running IDE. The provider emits only numeric identifiers and measurements, never source text, file paths or token contents. It is disabled unless enabled at **Verbose (5)** level. Explicit, flat event schemas with integer flags keep EventPipe payloads readable by TraceEvent 4.0.0.

## What is measured

Each scheduled pass gets a process-local pass ID, highlighter ID and document version. Successful worker passes emit one `Pass` event containing:

- Delay from scheduling to worker entry.
- Synchronous worker elapsed time and **worker-thread managed allocations** (`GC.GetAllocatedBytesForCurrentThread`). The pass does not await or change threads.
- Grammar/theme loading time and allocations. Regex compilation performed lazily during tokenization belongs to the tokenizer stage instead.
- Grammar lock acquisition/wait time.
- Time and allocations inside the exact tokenizer API call, summed across lines.
- Line preparation and mapping: obtaining/copying line text and turning encoded tokens into Passenger spans, excluding the tokenizer call.
- Remaining worker time and allocations: line-table construction/reuse, convergence checks, progress scheduling and measurement overhead. This is a residual, not a claim that all of it belongs to a single cache method.
- Read, skipped (>20,000 characters) and tokenizer-stopped line counts; total document lines; where stale data starts; and whether the pass completed the current snapshot. TextMateSharp 2.0.4 does not expose its encoded-token early-stop flag publicly, so its `unknownStopStatusLines` is recorded rather than pretending its stop count is known.

Each progress/final callback emits a `Publication` event: queue delay, callback elapsed time, allocations on the callback thread and elapsed time since pass scheduling. Callback cost includes subscribers notified by `Changed`, but not subsequent rendering. The context can be absent for a non-UI host; in that case the callback runs inline. Failed worker passes do not emit a successful `Pass`; Passenger's existing `Failure` / `Failed` reporting still applies.

All time fields are **wall-clock Stopwatch ticks**, with `frequency` included. They are not per-stage CPU counters. Process CPU remains available in the benchmark; the sampled-thread-time trace profile adds managed stack samples, which are also not precise kernel CPU accounting on macOS.

Within each successful worker event, time and allocations reconcile exactly:

```
workerTicks = grammarTicks + lockWaitTicks + tokenizerTicks + linePreparationTicks + otherWorkerTicks
workerAllocatedBytes = grammarAllocatedBytes + tokenizerAllocatedBytes + linePreparationAllocatedBytes + otherWorkerAllocatedBytes
```

The pass event's own construction/emission is after the worker counters are captured. Publication emission is after callback counters are captured. Diagnostic clocks and progress instrumentation still add overhead; use these runs for attribution, **not as replacements for the uninstrumented headline timings**. Disabled diagnostics allocate no telemetry collector and perform no additional per-line clock/allocation-counter reads; their branches and captured reference still have some cost, not claimed to be zero.

## Capture the running IDE

```sh
dotnet-trace collect --process-id PID \
  --providers Passenger-Highlighting:0xFFFFFFFFFFFFFFFF:5 \
  --profile dotnet-sampled-thread-time --output highlighting.nettrace
```

Open/edit the same files and use the same theme and viewport for baseline and candidate. Keep project loading and language-server activity comparable. The provider also works when launching the executable through `dotnet-trace collect ... -- COMMAND ARGS`.

In the historical experiment, a real headless Passenger run opened the 697-line HTML fixture and typed one character. Its trace decoded as an initial pass, a one-line incremental pass and their final publications, with zero lost events; both time/allocation equations were checked. [The historical decoded summary](https://github.com/sebastienros/passenger/blob/reference/tint-instrumentation/tools/Passenger.HighlightingBenchmarks/ide-trace-summary.json) is committed. This smoke trace was not a controlled baseline/candidate timing comparison.

## Reproduce the instrumented comparison

The candidate already contains the instrumentation. For baseline, start from upstream `fa86d9d42dbb53a8067f06f212d80d09540a3fe4`, copy the benchmark sources and `src/Passenger.Languages/TextMate/HighlightingEventSource.cs` into that checkout, then apply the same boundaries:

```sh
python3 tools/Passenger.HighlightingBenchmarks/instrument.py /path/to/baseline
```

The script supports either engine, applies once, and preserves engine-specific tokenization. Its output was checked byte-for-byte against both instrumented highlighters. Build the benchmark in both checkouts as described in [README.md](README.md), then:

```sh
python3 tools/Passenger.HighlightingBenchmarks/run.py \
  --baseline /path/to/baseline/artifacts/bin/Passenger.HighlightingBenchmarks/release/Passenger.HighlightingBenchmarks.dll \
  --candidate /path/to/candidate/artifacts/bin/Passenger.HighlightingBenchmarks/release/Passenger.HighlightingBenchmarks.dll \
  --instrument --rounds 3 --cases xml.props,css.css,javascript.js,less.less \
  --output diagnostic-results
python3 tools/Passenger.HighlightingBenchmarks/summarize-diagnostics.py
```

These attribution runs use three fresh processes per engine/workload, summarized as medians of process medians,, seven measured full passes after warmup and five batches of 100 edits. Each phase aggregates events without retaining per-edit trace objects. The listener checks event errors, successful-pass counts, complete snapshots, paired final publications and exact accounting. Full/incremental colour hashes must agree, and the diagnostic summarizer checks cross-engine colour and input hashes. No EventListener is created unless `--instrument` is supplied.

The current instrumented benchmark builds and every listener run must pass before publication. The independent EventPipe smoke test belongs to the historical experiment and was not repeated for this refresh.

## Attribution results

See [stage measurements](diagnostic-tables.md) and [machine-readable summary](diagnostic-summary.json). These measure tokenizer costs separately from preparation, line tables, dispatch and publication. [The total measurements](tables.md) come from builds without diagnostic hooks. Both current engines reuse a line buffer within each pass.
