## Full-file time

| Workload | Total time: TMS → Tint (ratio) | Tokenizer time¹: TMS → Tint (ratio) |
|---|---:|---:|
| XML | 113.51 → 76.33 ms (**0.67**) | 76.55 → 65.11 ms (**0.85**) |
| CSS | 4,117.25 → 307.50 ms (**0.07**) | 4,111.73 → 300.20 ms (**0.07**) |
| JavaScript | 1,678.45 → 235.39 ms (**0.14**) | 1,668.65 → 230.66 ms (**0.14**) |
| Less | 169.40 → 49.27 ms (**0.29**) | 163.54 → 81.12 ms (**0.50**) |

**Legend:** TMS = TextMateSharp. Ratio = Tint ÷ TMS; **0.33** means 33% of TMS’s time, or 67% less. Total time includes tokenization, line preparation, cache updates and background dispatch, excluding UI rendering. ¹Tokenizer time comes from separate instrumented runs, with measurement overhead. Columns are not additive and must not be subtracted to estimate overhead.

## Allocations per edit

| Workload | Total allocations/edit: TMS → Tint (ratio) | Tokenizer allocations/edit¹: TMS → Tint (ratio) |
|---|---:|---:|
| XML | 18,252 → 17,636 B (**0.97**) | 944 → 328 B (**0.35**) |
| CSS | 21,164 → 15,572 B (**0.74**) | 936 → 336 B (**0.36**) |
| JavaScript | 17,730 → 15,556 B (**0.88**) | 1,928 → 328 B (**0.17**) |
| Less | 17,620 → 16,716 B (**0.95**) | 976 → 72 B (**0.07**) |

**Legend:** TMS = TextMateSharp. Ratio = Tint ÷ TMS. Total allocations cover the complete edit/highlighting operation, excluding UI rendering. ¹Tokenizer allocations come from separate instrumented runs. These are allocated managed bytes, not retained RAM. This table measures **one-character edits**, not full-file passes.

## Full-file CPU, allocations and working set

| Workload | Process CPU: TMS → Tint (ratio) | Allocated: TMS → Tint (ratio) | Working set: TMS → Tint (ratio) |
|---|---:|---:|---:|
| XML | 130.52 → 90.32 ms (**0.69**) | 32.85 → 4.83 MiB (**0.15**) | 79.94 → 73.66 MiB (**0.92**) |
| JSON | 74.13 → 67.46 ms (**0.91**) | 27.63 → 4.85 MiB (**0.18**) | 82.03 → 72.20 MiB (**0.88**) |
| YAML | 211.60 → 134.64 ms (**0.64**) | 24.37 → 2.77 MiB (**0.11**) | 83.31 → 73.33 MiB (**0.88**) |
| Markdown | 156.03 → 147.65 ms (**0.95**) | 16.33 → 2.77 MiB (**0.17**) | 91.34 → 93.64 MiB (**1.03**) |
| HTML | 214.85 → 53.91 ms (**0.25**) | 75.10 → 4.15 MiB (**0.06**) | 90.39 → 92.03 MiB (**1.02**) |
| CSS | 4,206.95 → 315.11 ms (**0.07**) | 76.01 → 4.44 MiB (**0.06**) | 96.22 → 87.30 MiB (**0.91**) |
| JavaScript | 1,714.76 → 240.77 ms (**0.14**) | 146.22 → 3.99 MiB (**0.03**) | 114.86 → 87.06 MiB (**0.76**) |
| Shell | 461.33 → 68.61 ms (**0.15**) | 68.37 → 4.77 MiB (**0.07**) | 84.06 → 87.59 MiB (**1.04**) |
| SCSS | 1,203.18 → 80.78 ms (**0.07**) | 32.86 → 2.10 MiB (**0.06**) | 97.80 → 84.16 MiB (**0.86**) |
| Less | 175.45 → 98.83 ms (**0.56**) | 43.57 → 2.40 MiB (**0.06**) | 83.22 → 84.17 MiB (**1.01**) |

**Legend:** CPU is process CPU consumed during a full pass, summed across threads. Allocated is managed allocation during that pass. Working set is sampled after forced GC and includes runtime, JIT, heaps and native libraries; it is not the highlighter’s retained memory. All ratios are Tint ÷ TMS. These measurements exclude IDE rendering and language-server activity.
