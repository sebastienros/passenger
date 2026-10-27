#!/usr/bin/env python3
"""Apply identical measurement boundaries to the baseline or Tint highlighter (once)."""
import pathlib,sys
root=pathlib.Path(sys.argv[1])
p=root/'src/Passenger.Languages/TextMate/TextMateHighlighter.cs'
s=p.read_text()
if 'HighlightingPass?' in s: raise SystemExit('Already instrumented')
s=s.replace('    private long workTicks;','    private long workTicks;\n    private static long nextDiagnosticId;\n    private long diagnosticId;')
s=s.replace('        int passVersion = version;', '''        int passVersion = version;
        HighlightingPass? telemetry = null;
        if (HighlightingEventSource.Log.IsEnabled(System.Diagnostics.Tracing.EventLevel.Verbose, System.Diagnostics.Tracing.EventKeywords.None))
        {
            if (diagnosticId == 0)
            {
                diagnosticId = Interlocked.Increment(ref nextDiagnosticId);
            }
            telemetry = new HighlightingPass(diagnosticId, passVersion, old is null);
        }''')
s=s.replace('Pass(old, text, first, tail, passVersion)', 'Pass(old, text, first, tail, passVersion, telemetry)')
s=s.replace('        }), TaskScheduler.Default));','        }, telemetry, final: true), TaskScheduler.Default));')
s=s.replace('int tail, int passVersion)\n', 'int tail, int passVersion, HighlightingPass? telemetry)\n')
s=s.replace('        long began = Stopwatch.GetTimestamp();', '        telemetry?.Start();\n        long began = Stopwatch.GetTimestamp();')
s=s.replace('        int count = text.LineCount;', '        telemetry?.GrammarLoaded();\n        int count = text.LineCount;')
s=s.replace('            lock (grammar.Gate)', '            long lockStarted = telemetry is null ? 0 : Stopwatch.GetTimestamp();\n            lock (grammar.Gate)')
s=s.replace('                for (; line < until; line++)', '                telemetry?.LockAcquired(lockStarted);\n                for (; line < until; line++)')
s=s.replace('Read(rules, text, line, state, scratch, ref buffer)', 'Read(rules, text, line, state, scratch, ref buffer, telemetry)')
s=s.replace('                    TokenLine read = Read(', '                    telemetry?.Reading();\n                    TokenLine read = Read(').replace('                    built.Add(read);', '                    telemetry?.LineRead();\n                    built.Add(read);')
s=s.replace('OnUi(() => Show(progress, text, passVersion));', 'OnUi(() => Show(progress, text, passVersion), telemetry, final: false);')
s=s.replace('        return built.Build(staleFrom);', '        LineTable result = built.Build(staleFrom);\n        telemetry?.Finish(count, staleFrom);\n        return result;')
s=s.replace('List<SyntaxSpan> scratch, ref char[] buffer)\n', 'List<SyntaxSpan> scratch, ref char[] buffer, HighlightingPass? telemetry)\n')
s=s.replace('            return new TokenLine([], state);', '            telemetry?.SkipLine();\n            return new TokenLine([], state);')
if 'using Tint;' in s:
 s=s.replace('        ReadOnlySpan<EncodedToken> tokens = rules.TokenizeLineEncoded', '        telemetry?.Tokenizing();\n        ReadOnlySpan<EncodedToken> tokens = rules.TokenizeLineEncoded')
 s=s.replace('out StateStack next);', 'out StateStack next);\n        telemetry?.Tokenized(rules.StoppedEarly);')
else:
 s=s.replace('        ITokenizeLineResult2 result = rules.TokenizeLine2', '        telemetry?.Tokenizing();\n        ITokenizeLineResult2 result = rules.TokenizeLine2')
 s=s.replace('        int[] tokens = result.Tokens;', '        telemetry?.Tokenized(null);\n        int[] tokens = result.Tokens;')
s=s.replace('    private void OnUi(Action action)\n    {','''    private void OnUi(Action action, HighlightingPass? telemetry = null, bool final = false)
    {
        if (telemetry is not null)
        {
            action = telemetry.Publication(action, final);
        }''')
p.write_text(s)
