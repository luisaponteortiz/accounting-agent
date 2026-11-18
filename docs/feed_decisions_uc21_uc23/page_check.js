// Syntax-check the page script and exercise the one changed line with stub DOM helpers.
var source = read(arguments[0]);
new Function(source);                       // throws SyntaxError if the script does not parse
var line = source.split('\n').filter(function (l) { return l.indexOf("$('source-exceptions')") >= 0; });
if (line.length !== 1) throw new Error('expected one source-exceptions line, found ' + line.length);
var shown = [];
function el(tag, text, cls) { return { tag: tag, text: text, cls: cls }; }
function $(id) { return { replaceChildren: function () { shown = Array.prototype.slice.call(arguments); } }; }
function render(state) { eval(line[0]); return shown.map(function (n) { return n.text; }); }
var none = render({ source_exceptions: [] });
var legacyState = render({ source_exceptions: [{ source_key: 'card:A', reason: 'UNASSIGNED_ACCOUNTING_PERIOD', period_id: null }] });
var both = render({ source_exceptions: [{ source_key: 'card:A', reason: 'SOURCE_MOVED_FROM_LOCKED_PERIOD', period_id: '2026-11' }],
                    feed_anomalies: [{ source_key: 'card:Q', reason: 'SOURCE_ORDER_MIXED', meaning: 'A message with no order value was kept as evidence; it does not govern this row.' }] });
print(JSON.stringify({ parses: true, no_anomaly_key: none, state_without_the_new_key: legacyState, with_anomaly: both }, null, 1));
