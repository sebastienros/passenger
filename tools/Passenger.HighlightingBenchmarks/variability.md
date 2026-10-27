# Full-pass timing variability

Each cell lists the three process medians in execution-round order, in milliseconds. These are observed ranges, not confidence intervals. Tiered compilation was left enabled; seven measured passes do not guarantee steady state.

| Workload | TextMateSharp process medians (ms) | Tint process medians (ms) |
|---|---:|---:|
| xml.props | 61.86, 113.51, 125.75 | 75.48, 76.33, 86.74 |
| json.json | 84.69, 50.79, 61.38 | 61.57, 78.21, 64.87 |
| yaml.yml | 195.10, 201.74, 210.21 | 138.62, 120.94, 122.99 |
| markdown.md | 148.22, 151.82, 152.96 | 43.23, 145.94, 138.01 |
| html.html | 201.89, 209.85, 209.39 | 50.94, 51.18, 51.70 |
| css.css | 4,108.49, 4,161.36, 4,117.25 | 311.40, 305.56, 307.50 |
| javascript.js | 1,676.53, 1,695.85, 1,678.45 | 235.91, 235.39, 233.46 |
| shell.sh | 451.16, 456.70, 450.01 | 63.97, 62.42, 66.28 |
| scss.scss | 1,178.74, 1,189.31, 1,155.16 | 77.14, 77.99, 76.51 |
| less.less | 169.40, 169.57, 169.13 | 79.28, 36.30, 49.27 |
