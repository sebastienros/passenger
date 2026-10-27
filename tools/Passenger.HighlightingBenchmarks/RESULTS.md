# Results: Passenger with Tint

Measured on an Apple M4 Pro with 48 GiB RAM, macOS 15.8 arm64, .NET 11 RC3, Release. See [methodology](README.md), [raw samples](results), and [summary data](summary.json).

Tint reduced managed allocation by **76–97%** for full-file highlighting. Median full-pass speedups ranged from **1.09× to 15.34×**; CSS, SCSS, JavaScript and shell showed the largest gains. Process CPU time fell **11–93%** across these workloads. These are highlighter results, not whole-IDE improvements.

All ten expanded inputs produced **identical complete colour-span hashes** across both engines and all three fresh processes. Each measured edit batch restored the original colour spans; each small edit converged after one line in both engines.

| Workload (~10k lines) | Baseline ms | Tint ms | Speedup | CPU reduction | Allocation reduction | Baseline / Tint allocated MiB |
|---|---:|---:|---:|---:|---:|---:|
| xml.props | 87.76 | 80.36 | 1.09× | 27.0% | 80.9% | 34.02 / 6.48 |
| json.json | 88.40 | 75.76 | 1.17× | 11.4% | 80.3% | 30.09 / 5.92 |
| yaml.yml | 201.55 | 105.99 | 1.90× | 42.4% | 84.3% | 25.68 / 4.04 |
| markdown.md | 152.68 | 55.72 | 2.74× | 31.2% | 76.4% | 17.84 / 4.22 |
| html.html | 208.97 | 52.86 | 3.95× | 74.4% | 92.7% | 76.52 / 5.55 |
| css.css | 4141.73 | 307.37 | 13.47× | 92.5% | 92.9% | 77.09 / 5.49 |
| javascript.js | 1686.04 | 235.57 | 7.16× | 85.9% | 96.6% | 147.28 / 5.02 |
| shell.sh | 458.21 | 63.22 | 7.25× | 85.5% | 91.5% | 69.57 / 5.94 |
| scss.scss | 1175.51 | 76.64 | 15.34× | 93.2% | 92.0% | 33.45 / 2.67 |
| less.less | 170.30 | 34.76 | 4.90× | 61.2% | 93.3% | 44.16 / 2.95 |

| Workload | First use ms (base / Tint) | Working set MiB (base / Tint) | Edit µs (base / Tint) | Edit allocated bytes (base / Tint) | Lines per edit (base / Tint) |
|---|---:|---:|---:|---:|---:|
| xml.props | 170.4 / 138.6 | 79.8 / 77.2 | 22.1 / 25.2 | 18252 / 17636 | 1.0 / 1.0 |
| json.json | 161.6 / 116.6 | 82.0 / 74.2 | 24.3 / 21.4 | 19516 / 15492 | 1.0 / 1.0 |
| yaml.yml | 315.3 / 182.0 | 79.3 / 74.3 | 19.8 / 14.4 | 17100 / 15620 | 1.0 / 1.0 |
| markdown.md | 332.6 / 307.2 | 90.2 / 97.2 | 34.5 / 20.3 | 16100 / 15508 | 1.0 / 1.0 |
| html.html | 557.1 / 377.3 | 87.2 / 93.0 | 24.3 / 16.7 | 17196 / 15620 | 1.0 / 1.0 |
| css.css | 4311.8 / 1307.9 | 96.5 / 87.9 | 10.5 / 10.1 | 21164 / 15572 | 1.0 / 1.0 |
| javascript.js | 1948.2 / 1048.2 | 115.0 / 89.4 | 108.8 / 35.7 | 17732 / 15556 | 1.0 / 1.0 |
| shell.sh | 658.9 / 412.9 | 84.1 / 88.4 | 19.1 / 11.7 | 17628 / 15140 | 1.0 / 1.0 |
| scss.scss | 1396.5 / 689.4 | 97.2 / 84.3 | 23.5 / 17.7 | 16028 / 17068 | 1.0 / 1.0 |
| less.less | 411.7 / 262.4 | 83.0 / 84.2 | 13.2 / 16.5 | 17620 / 16716 | 1.0 / 1.0 |

## Tradeoffs and uncertainty

- Working set was not uniformly lower: Markdown rose from 90.2 to 97.2 MiB, HTML from 87.2 to 93.0 MiB, shell from 84.1 to 88.4 MiB, and Less from 83.0 to 84.2 MiB. JavaScript fell from 115.0 to 89.4 MiB. Do not describe the allocation reduction as a 76–97% RAM reduction.
- Small XML edits were about 14% slower and Less edits about 25% slower at these very short times. SCSS edit allocations increased from about 16.0 to 17.1 KB. This replacement is not a universal incremental-edit win.
- XML, JSON and Markdown warm-pass times varied across processes. Default tiered compilation is enabled; these short runs include JIT/tiering effects and should not be read as tightly bounded steady-state estimates. Strong gains on the heavier grammars are more consistent. The table below exposes the process medians rather than hiding their spread.
- The first-use result includes lazy tokenizer work, not file I/O, process startup, window creation, or language-server startup. No assertion is made about whole-IDE startup or perceived input latency.
- Runtime loading was deliberately retained for this first replacement. Source-generated grammars and kernels may change cold cost, binary size and throughput and need a separate comparison.

| Workload | Baseline warm process medians (ms) | Tint warm process medians (ms) |
|---|---:|---:|
| xml.props | 87.76, 73.48, 95.87 | 80.36, 77.63, 82.59 |
| json.json | 104.59, 68.05, 88.40 | 65.10, 75.76, 83.21 |
| yaml.yml | 201.55, 203.59, 199.38 | 100.33, 105.99, 120.81 |
| markdown.md | 152.68, 152.96, 151.30 | 55.72, 167.83, 53.76 |
| html.html | 208.07, 210.33, 208.97 | 52.86, 56.04, 52.72 |
| css.css | 4169.30, 4140.69, 4141.73 | 319.46, 307.37, 303.48 |
| javascript.js | 1730.32, 1686.04, 1670.60 | 240.55, 235.57, 233.78 |
| shell.sh | 465.31, 452.61, 458.21 | 62.88, 63.54, 63.22 |
| scss.scss | 1179.31, 1170.65, 1175.51 | 76.42, 76.83, 76.64 |
| less.less | 170.30, 170.30, 169.26 | 33.95, 34.76, 56.35 |

## Validation

- Full `dotnet build Passenger.slnx -c Release`: passed, zero warnings/errors.
- The same filter (`FullyQualifiedName~FileColours|FullyQualifiedName~RazorTests`) on baseline and Tint: **14 passed, 5 failed** in both. All selected FileColours and FileColoursResponsiveness tests passed. All five Razor failures occurred in fixture initialization: `dotnet new blazor --framework net10.0` saw only the .NET 11 Blazor template. These tests did not exercise the tokenizer; they remain unvalidated here.
- `python3 -I tools/check-notices.py` with the pinned SDK on PATH: passed, all 377 packages named.
- All 60 fresh-process benchmark invocations passed, including repeatability and incremental restoration checks; cross-engine colour and input hashes match for every workload.
- Headless real-Skia HTML screenshot at scale 2: generated and visually inspected ([image](tint-html.png)).
- `git diff --check`: passed. No upstream grammar file bytes changed. Production lock-file changes replace TextMateSharp/Onigwrap with Tint/GregsEx.
- Complete cross-platform tests, packaging and CI workflows were not run.
