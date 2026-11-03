// Pure calculations for the page: no DOM, so tests/calc.test.js can run them in Node.
// `now` is a millisecond timestamp; the page passes Date.now().
const Calc = (() => {
  const STANCE_CLASS = { bullish: 'bull', bearish: 'bear', neutral: 'neu' };
  const STANCE_ZH = { bullish: '看多', bearish: '看空', neutral: '中立' };
  const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六'];
  const TOP_N = 15; // tickers shown before "顯示全部"
  const DAY_MS = 864e5;

  // Unknown or missing stance counts as neutral.
  function stanceOf(s) { return STANCE_CLASS[s] ? s : 'neutral'; }

  // Start of a tab's time window. 0 = all time, 1 = today (local calendar day), n = last n x 24 hours.
  function windowStart(days, now) {
    if (!days) return -Infinity;
    if (days === 1) { const t = new Date(now); t.setHours(0, 0, 0, 0); return t.getTime(); }
    return now - days * DAY_MS;
  }
  function inWindow(post, days, now) { return new Date(post.time).getTime() >= windowStart(days, now); }

  function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  // Local-time labels.
  function dateLabel(iso) {
    const d = new Date(iso);
    return (d.getMonth() + 1) + ' 月 ' + d.getDate() + ' 日（週' + WEEKDAYS[d.getDay()] + '）';
  }
  function timeLabel(iso) {
    const d = new Date(iso);
    return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
  }
  function dateKey(iso) { const d = new Date(iso); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); }

  // X puts cashtags on their own line when scraped ("text\n$NVDA\nmore"); join them back, and squeeze blank lines.
  function cleanText(text) {
    return String(text || '').replace(/\n\$([A-Z.]+)\n/g, ' $$$1 ').replace(/\n{3,}/g, '\n\n');
  }

  function isXLink(link) { return /^https:\/\/x\.com\//.test(link || ''); }

  // Which summary goes with a tab: 7 and 28 have their own, the others borrow the 7-day one.
  function briefKey(days) { return (days === 7 || days === 28) ? String(days) : '7'; }

  function postsHeading(days) { return days ? `貼文（${days === 1 ? '今天' : days + ' 天'}）` : '貼文（全部）'; }

  // One row per ticker: mentions, stance counts, and the latest reason
  // (newest non-paywalled post with a reason, else the newest mention). `posts` must be newest first.
  function tickerRows(posts) {
    const agg = {};
    for (const p of posts) for (const k of p.tickers) {
      const a = agg[k.t] ??= { t: k.t, n: 0, bullish: 0, bearish: 0, neutral: 0 };
      a.n++; a[stanceOf(k.stance)]++;
    }
    for (const t in agg) {
      let found = null, fallback = null;
      for (const p of posts) {
        const k = p.tickers.find(x => x.t === t);
        if (!k) continue;
        if (!fallback) fallback = { reason: k.reason_zh, stance: k.stance };
        if (!p.paywalled && k.reason_zh) { found = { reason: k.reason_zh, stance: k.stance }; break; }
      }
      const use = found || fallback;
      agg[t].lastReason = use ? (use.reason || '') : '';
      agg[t].lastStance = stanceOf(use && use.stance);
    }
    return Object.values(agg).sort((a, b) => b.n - a.n || a.t.localeCompare(b.t));
  }

  // All-time posts about one ticker, with stance counts.
  function stockSummary(data, sym) {
    const list = data.filter(p => p.tickers.some(k => k.t === sym));
    let bull = 0, bear = 0, neu = 0;
    for (const p of list) {
      const st = stanceOf(p.tickers.find(x => x.t === sym).stance);
      if (st === 'bullish') bull++; else if (st === 'bearish') bear++; else neu++;
    }
    return { list, bull, bear, neu };
  }

  return { STANCE_CLASS, STANCE_ZH, TOP_N, stanceOf, windowStart, inWindow, esc, dateLabel, timeLabel, dateKey,
    cleanText, isXLink, briefKey, postsHeading, tickerRows, stockSummary };
})();
if (typeof module !== 'undefined') module.exports = Calc;
