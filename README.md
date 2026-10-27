# Tint review comparisons

Visual evidence for [Passenger PR 572](https://github.com/Zaneris/passenger/pull/572).

These previews reconstruct recorded TextMateSharp 2.0.4 and Tint 0.1.2 token streams with Passenger's Nightjar dark palette. They are not screenshots of the running Passenger editor. The lower panels show diagnostic scope differences; amber is not an editor highlighting colour. Tint matches vscode-textmate 9.3.2 / vscode-oniguruma 2.0.1 on each shown line.

- `razor.png`: SVG attribute names and values.
- `markdown.png`: YAML front matter in Markdown.
- `shell.png`: function/body scopes, with identical Passenger colours.

Recorded comparison: 2026-10-27. These files live on a separate reference branch and are not included in the replacement PR.
