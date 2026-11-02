// Draws the page from DATA and BRIEF (embedded by build.py) using Calc (web/calc.js).
const { STANCE_CLASS, STANCE_ZH, esc } = Calc;
const $ = id => document.getElementById(id);
const state = { days: 7, sel: null, showAllTickers: false };

function stanceTag(stance, label) {
  return `<span class="${STANCE_CLASS[stance]}"><span class="tag">${label}</span></span>`;
}

function postHtml(p, focus) {
  const labs = p.tickers.map(k => {
    const reason = (focus && k.t === focus && k.reason_zh && !p.paywalled) ? ` <span class="reason">${esc(k.reason_zh)}</span>` : '';
    const st = Calc.stanceOf(k.stance);
    return stanceTag(st, `${esc(k.t)} ${STANCE_ZH[st]}`) + reason;
  }).join(' ');
  const txt = Calc.cleanText(p.text);
  const zhText = p.zh ? p.zh : txt;
  const pay = p.paywalled ? ' <span class="mute">付費貼文，只有開頭</span>' : '';
  const link = Calc.isXLink(p.link) ? `<a href="${esc(p.link)}" target="_blank" rel="noopener noreferrer" aria-label="在 X 開啟原貼文（另開新分頁）">在 X 開啟</a>` : '';
  const meta = `<span><time class="mute" datetime="${esc(p.time)}">${Calc.timeLabel(p.time)}</time>${pay}</span>${link}`;
  const en = p.zh ? `<details><summary>英文原文</summary><div class="quoted">${esc(txt)}</div></details>` : '';
  const q = p.quoted ? `<details><summary>她回應的內容</summary><div class="quoted">${esc(p.quoted_zh || p.quoted)}${p.quoted_zh ? '\n\n原文：' + esc(p.quoted) : ''}</div></details>` : '';
  return `<article class="post"><div class="meta">${meta}</div><div class="lab">${labs}</div><div class="txt clamp">${esc(zhText)}</div><button type="button" class="expand">展開</button>${en}${q}</article>`;
}

// Posts with a date heading whenever the local day changes.
function postsHtml(list, focus) {
  let out = '', lastKey = null;
  for (const p of list) {
    const k = Calc.dateKey(p.time);
    if (k !== lastKey) { out += `<h3 class="dhead">${Calc.dateLabel(p.time)}</h3>`; lastKey = k; }
    out += postHtml(p, focus);
  }
  return out;
}

// Hide "展開" on posts short enough to fit in 5 lines; wire up the rest.
function applyClamp(container) {
  container.querySelectorAll('.txt.clamp').forEach(el => {
    const btn = el.nextElementSibling;
    if (!el.clientHeight) return; // not laid out yet (e.g. inside closed <details>), measure later
    if (el.scrollHeight <= el.clientHeight + 2 && btn && btn.classList.contains('expand')) btn.style.display = 'none';
  });
  container.querySelectorAll('.expand').forEach(btn => {
    btn.onclick = () => { btn.previousElementSibling.classList.remove('clamp'); btn.style.display = 'none'; };
  });
}

function showSections(stockPage) {
  for (const id of ['tabs', 'brief', 'listSec', 'tlSec']) $(id).style.display = stockPage ? 'none' : '';
  $('stockSec').style.display = stockPage ? '' : 'none';
}

function tickerRowHtml(r) {
  const mix = (r.bullish > 0 && r.bearish > 0) ? `<span class="mute">多 ${r.bullish}・空 ${r.bearish}</span>` : '';
  return `<button type="button" class="tkrow" data-t="${esc(r.t)}"><span class="l1"><span class="sym">${esc(r.t)}</span><span class="mute">提到 ${r.n} 次</span></span>`
    + `<span class="l2">${stanceTag(r.lastStance, STANCE_ZH[r.lastStance])} <span class="reason">${esc(r.lastReason)}</span> ${mix}</span></button>`;
}

function renderList() {
  showSections(false);
  const posts = DATA.filter(p => Calc.inWindow(p, state.days, Date.now()));

  // Summary only when the window has posts, so an old summary never sits on an empty page.
  const pts = BRIEF[Calc.briefKey(state.days)] || [];
  $('brief').innerHTML = (pts.length && posts.length) ? ('<ol>' + pts.map(t => `<li>${esc(t)}</li>`).join('') + '</ol>') : '';

  const rows = Calc.tickerRows(posts);
  const shown = state.showAllTickers ? rows : rows.slice(0, Calc.TOP_N);
  $('tk').innerHTML = shown.map(tickerRowHtml).join('') || '<div class="mute">這段時間沒有貼文</div>';
  document.querySelectorAll('.tkrow').forEach(el => el.onclick = () => { state.sel = el.dataset.t; render(); window.scrollTo(0, 0); $('stitle').focus({ preventScroll: true }); });
  const moreBtn = $('moreBtn');
  if (!state.showAllTickers && rows.length > Calc.TOP_N) { moreBtn.style.display = ''; moreBtn.textContent = `顯示全部 ${rows.length} 檔`; }
  else moreBtn.style.display = 'none';

  $('tlHead').textContent = Calc.postsHeading(state.days);
  const withTk = posts.filter(p => p.tickers.length > 0);
  const noTk = posts.filter(p => p.tickers.length === 0);
  $('tl').innerHTML = postsHtml(withTk);
  const otherSec = $('otherSec');
  otherSec.innerHTML = noTk.length ? (`<summary>其他貼文（沒提到股票）${noTk.length} 則</summary><div>` + postsHtml(noTk) + '</div>') : '';
  otherSec.style.display = noTk.length ? '' : 'none';
  applyClamp($('tl'));
  otherSec.ontoggle = () => { if (otherSec.open) applyClamp(otherSec); };
}

function renderStock() {
  showSections(true);
  const s = Calc.stockSummary(DATA, state.sel);
  $('stitle').textContent = state.sel;
  $('ssub').textContent = `提到 ${s.list.length} 次，看多 ${s.bull}、看空 ${s.bear}、中立 ${s.neu}（全部時間）`;
  $('stlist').innerHTML = postsHtml(s.list, state.sel);
  applyClamp($('stlist'));
}

function render() { if (state.sel) renderStock(); else renderList(); }

document.querySelectorAll('#tabs button').forEach(b => {
  const d = +b.dataset.d, n = DATA.filter(p => Calc.inWindow(p, d, Date.now())).length;
  b.textContent = b.textContent + ' · ' + n;
  b.onclick = () => {
    state.days = d; state.showAllTickers = false;
    document.querySelectorAll('#tabs button').forEach(x => { x.classList.toggle('on', x === b); x.setAttribute('aria-pressed', String(x === b)); });
    render();
  };
});
$('moreBtn').onclick = () => { state.showAllTickers = true; render(); };
$('backBtn').onclick = () => {
  const was = state.sel;
  state.sel = null; render(); window.scrollTo(0, 0);
  // keyboard users land back on the stock they opened (if it is still in the list)
  const row = [...document.querySelectorAll('.tkrow')].find(el => el.dataset.t === was);
  if (row) row.focus({ preventScroll: true });
};
render();
