// Unit tests for web/calc.js (the page's numbers). Run: node --test tests/calc.test.js
// Timezone is fixed so "today" and date labels do not depend on the machine.
process.env.TZ = 'Asia/Taipei';
const test = require('node:test');
const assert = require('node:assert');
const Calc = require('../web/calc.js');

const NOW = Date.parse('2026-09-09T12:00:00Z'); // 20:00 in Taipei
const post = (time, tickers = [], extra = {}) => ({ time, tickers, paywalled: false, ...extra });
const tk = (t, stance, reason_zh = '') => ({ t, stance, reason_zh });

test('stanceOf: unknown or missing stance is neutral', () => {
  assert.strictEqual(Calc.stanceOf('bullish'), 'bullish');
  assert.strictEqual(Calc.stanceOf('mixed'), 'neutral');
  assert.strictEqual(Calc.stanceOf(undefined), 'neutral');
});

test('windowStart: all time, today = local midnight, n days = rolling', () => {
  assert.strictEqual(Calc.windowStart(0, NOW), -Infinity);
  assert.strictEqual(Calc.windowStart(1, NOW), Date.parse('2026-09-08T16:00:00Z')); // 00:00 Taipei
  assert.strictEqual(Calc.windowStart(7, NOW), NOW - 7 * 864e5);
  assert.strictEqual(Calc.windowStart(28, NOW), NOW - 28 * 864e5);
});

test('inWindow: edges are included, older posts are not', () => {
  assert.ok(Calc.inWindow(post('2026-09-08T16:00:00Z'), 1, NOW), 'exactly midnight counts as today');
  assert.ok(!Calc.inWindow(post('2026-09-08T15:59:59Z'), 1, NOW), '23:59 yesterday is not today');
  assert.ok(Calc.inWindow(post('2026-09-02T12:00:00Z'), 7, NOW), 'exactly 7 days ago counts');
  assert.ok(!Calc.inWindow(post('2026-09-02T11:59:59Z'), 7, NOW));
  assert.ok(Calc.inWindow(post('2000-01-01T00:00:00Z'), 0, NOW));
});

test('esc: all five HTML characters', () => {
  assert.strictEqual(Calc.esc(`<a href="x" onclick='y'>&</a>`), '&lt;a href=&quot;x&quot; onclick=&#39;y&#39;&gt;&amp;&lt;/a&gt;');
  assert.strictEqual(Calc.esc(null), '');
});

test('date and time labels use local time', () => {
  assert.strictEqual(Calc.dateLabel('2026-09-08T17:30:00Z'), '9 月 9 日（週三）');
  assert.strictEqual(Calc.timeLabel('2026-09-08T17:05:00Z'), '01:05');
  assert.strictEqual(Calc.dateKey('2026-09-08T15:59:00Z'), '2026-9-8');
  assert.strictEqual(Calc.dateKey('2026-09-08T16:00:00Z'), '2026-9-9');
});

test('cleanText: cashtags on their own line are joined, blank lines squeezed', () => {
  assert.strictEqual(Calc.cleanText('Long\n$SIVE\nhere'), 'Long $SIVE here');
  assert.strictEqual(Calc.cleanText('a\n\n\n\nb'), 'a\n\nb');
  assert.strictEqual(Calc.cleanText(undefined), '');
});

test('isXLink: only https://x.com/', () => {
  assert.ok(Calc.isXLink('https://x.com/a/status/1'));
  assert.ok(!Calc.isXLink('javascript:alert(1)'));
  assert.ok(!Calc.isXLink('https://x.com.evil.example/'));
  assert.ok(!Calc.isXLink(undefined));
});

test('briefKey and postsHeading', () => {
  assert.deepStrictEqual([1, 7, 28, 0].map(Calc.briefKey), ['7', '7', '28', '7']);
  assert.deepStrictEqual([1, 7, 28, 0].map(Calc.postsHeading), ['貼文（今天）', '貼文（7 天）', '貼文（28 天）', '貼文（全部）']);
});

test('tickerRows: counts, sort order, latest non-paywalled reason', () => {
  const posts = [ // newest first, as on the page
    post('2026-09-09T05:00:00Z', [tk('MU', 'bullish', '付費的理由')], { paywalled: true }),
    post('2026-09-08T05:00:00Z', [tk('MU', 'bearish', '最新的理由'), tk('AAOI', 'weird')]),
    post('2026-09-07T05:00:00Z', [tk('MU', 'bullish', '舊理由'), tk('NVDA', 'neutral')]),
  ];
  const rows = Calc.tickerRows(posts);
  assert.deepStrictEqual(rows.map(r => r.t), ['MU', 'AAOI', 'NVDA'], 'most mentioned first, then A to Z');
  const mu = rows[0];
  assert.deepStrictEqual([mu.n, mu.bullish, mu.bearish, mu.neutral], [3, 2, 1, 0]);
  assert.strictEqual(mu.lastReason, '最新的理由', 'paywalled post skipped for the reason');
  assert.strictEqual(mu.lastStance, 'bearish', 'stance comes from the same post as the reason');
  assert.strictEqual(rows[1].neutral, 1, 'unknown stance counted as neutral');
  assert.strictEqual(rows[1].lastStance, 'neutral');
});

test('tickerRows: falls back to newest mention when no post has a usable reason', () => {
  const rows = Calc.tickerRows([post('2026-09-09T05:00:00Z', [tk('X', 'bullish', '')], { paywalled: true }),
                                post('2026-09-08T05:00:00Z', [tk('X', 'bearish', '')])]);
  assert.strictEqual(rows[0].lastStance, 'bullish');
  assert.strictEqual(rows[0].lastReason, '');
  assert.deepStrictEqual(Calc.tickerRows([]), []);
});

test('stockSummary: all-time counts for one ticker', () => {
  const data = [post('a', [tk('MU', 'bullish')]), post('b', [tk('MU', 'bearish')]), post('c', [tk('MU', '?')]), post('d', [tk('NVDA', 'bullish')])];
  const s = Calc.stockSummary(data, 'MU');
  assert.deepStrictEqual([s.list.length, s.bull, s.bear, s.neu], [3, 1, 1, 1]);
  assert.strictEqual(Calc.stockSummary(data, 'NONE').list.length, 0);
});
