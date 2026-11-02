"""Build index.html from data/classified.json (single file, data embedded)."""
import json, pathlib, datetime, sys

ALIAS = {'SK Hynix': 'SKHY', 'Mediatek': 'MediaTek', 'ESMT': 'ESMT (3006)', 'Sandisk': 'SNDK', 'SanDisk': 'SNDK', 'Micron': 'MU', 'Nvidia': 'NVDA'}
STANCES = ('bullish', 'bearish', 'neutral')
DASHES = ('\u2014', '\u2013')  # em dash, en dash


def warn(msg):
    print('WARN', msg, file=sys.stderr, flush=True)


def nodash(s):
    if not isinstance(s, str):
        return s
    for d in DASHES:
        s = s.replace(d, '-')
    return s


def parse_time(s):
    try:
        d = datetime.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)


def normalize(data):
    """Clean posts for the page. Bad records are dropped or fixed loudly, never silently."""
    out = []
    for p in data:
        pid = p.get('id', '?')
        if not isinstance(p.get('time'), str) or parse_time(p['time']) is None:
            warn(f'post {pid}: bad time {p.get("time")!r}, skipped')
            continue
        link = p.get('link', '')
        if not (isinstance(link, str) and link.startswith('https://x.com/')):
            warn(f'post {pid}: unexpected link {link!r}, removed')
            p['link'] = ''
        if not isinstance(p.get('text'), str):
            p['text'] = ''
        if 'zh' not in p:
            warn(f'post {pid}: no zh translation (run translate.py)')
        seen = {}
        for k in p.get('tickers') or []:
            if not isinstance(k, dict) or not isinstance(k.get('t'), str) or not k['t'].strip('$ '):
                warn(f'post {pid}: bad ticker {k!r}, skipped')
                continue
            t = k['t'].strip().lstrip('$')
            k['t'] = ALIAS.get(t, t)
            if k.get('stance') not in STANCES:
                warn(f'post {pid}: {k["t"]} unknown stance {k.get("stance")!r}, shown as neutral')
                k['stance'] = 'neutral'
            seen.setdefault(k['t'], k)
        p['tickers'] = list(seen.values())
        for k in p['tickers']:
            k['reason'] = nodash(k.get('reason', ''))
            k['reason_zh'] = nodash(k.get('reason_zh', ''))
        for field in ('text', 'quoted', 'zh', 'quoted_zh', 'theme', 'theme_zh'):
            if field in p:
                p[field] = nodash(p[field])
        p['paywalled'] = bool(p.get('paywalled'))
        out.append(p)
    out.sort(key=lambda x: parse_time(x['time']), reverse=True)
    return out


def js_json(obj):
    """JSON safe to embed inside <script>: no '</script>' breakout, no HTML comment tricks."""
    s = json.dumps(obj, ensure_ascii=False)
    return (s.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
             .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


HTML = r'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Serenity 觀點追蹤</title>
<style>
:root{--fg:#111;--mute:#6b6b6b;--line:#e4e4e4;--bg:#fff;--bull:#0a7a3f;--bear:#c0392b;--neu:#777;--hl:#f8f8f8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 "Noto Sans TC",-apple-system,BlinkMacSystemFont,"PingFang TC","Segoe UI",sans-serif}
main{max-width:1040px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:22px;margin:0 0 4px;font-weight:700}
.sub{color:var(--mute);font-size:13px;margin-bottom:18px}
.tabs{display:flex;gap:4px;margin-bottom:16px;flex-wrap:wrap}
.tabs button{border:1px solid var(--line);background:#fff;padding:6px 14px;border-radius:999px;font:inherit;font-size:14px;cursor:pointer;color:var(--fg)}
.tabs button.on{background:var(--fg);color:#fff;border-color:var(--fg)}
.brief{margin:0 0 22px}
.brief ol{margin:0;padding-left:20px}
.brief li{overflow-wrap:anywhere;font-size:16px;line-height:1.7;margin:6px 0;color:#111}
h2{font-size:17px;margin:26px 0 10px;font-weight:600}
.linkbtn{background:none;border:0;font:inherit;font-size:14px;color:var(--mute);cursor:pointer;padding:4px 0;display:inline-block}
.mute{color:var(--mute)}
.bull{color:var(--bull)}.bear{color:var(--bear)}.neu{color:var(--neu)}
.tag{display:inline-block;font-size:12px;padding:1px 7px;border-radius:4px;border:1px solid currentColor;line-height:1.6;margin-right:4px;white-space:nowrap}
.tkrow{padding:12px 4px;border-bottom:1px solid var(--line);cursor:pointer}
.tkrow:hover{background:var(--hl)}
.tkrow .l1{display:flex;justify-content:space-between;align-items:baseline}
.tkrow .sym{font-size:17px;font-weight:700}
.tkrow .l2{margin-top:5px;font-size:15px;overflow-wrap:anywhere}
.stitle{font-size:20px;font-weight:700;margin:14px 0 4px}
.ssub{color:var(--mute);font-size:14px;margin-bottom:18px}
.dhead{font-size:14px;color:var(--mute);font-weight:600;margin:20px 0 8px}
.post{padding:14px 0;border-bottom:1px solid var(--line)}
.post .meta{display:flex;justify-content:space-between;align-items:baseline;font-size:13px;color:var(--mute);margin-bottom:6px}
.post .meta a{color:var(--mute)}
.post .lab{margin:0 0 8px;font-size:14px}
.txt{white-space:pre-wrap;overflow-wrap:anywhere;color:#111;font-size:16px;line-height:1.7}
.txt.clamp{display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden}
.expand{display:block;background:none;border:0;font:inherit;font-size:13px;color:var(--mute);cursor:pointer;padding:4px 0;text-decoration:underline}
.quoted{margin-top:6px;padding-left:10px;border-left:2px solid var(--line);color:var(--mute);font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere}
details summary{cursor:pointer;color:var(--mute);font-size:13px;margin-top:4px}
.othersec{margin-top:24px}
.footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);color:var(--mute);font-size:13px}
@media(max-width:640px){main{padding-left:16px;padding-right:16px}}
</style></head><body><main>
<h1>Serenity 觀點追蹤</h1>
<div class="sub">@aleabitoreddit 的公開貼文，AI 判讀，可能有錯，不是投資建議</div>
<div class="tabs" id="tabs"><button data-d="1">今天</button><button data-d="7" class="on">7 天</button><button data-d="28">28 天</button><button data-d="0">全部</button></div>
<div class="brief" id="brief"></div>
<div id="listSec">
<h2>提到的股票</h2>
<div id="tk"></div>
<button class="linkbtn" id="moreBtn" style="display:none"></button>
</div>
<div id="stockSec" style="display:none">
<button class="linkbtn" id="backBtn">‹ 回列表</button>
<div class="stitle" id="stitle"></div>
<div class="ssub" id="ssub"></div>
<div id="stlist"></div>
</div>
<div id="tlSec">
<h2 id="tl-h">貼文</h2>
<div id="tl"></div>
<details class="othersec" id="otherSec"></details>
</div>
<div class="footer">更新 __BUILT__ UTC ・ 最新貼文 __LATEST__ UTC</div>
</main>
<script>
const DATA=__DATA__;
const BRIEF=__BRIEF__;
let days=7, sel=null, showAllTk=false;
const cls={bullish:'bull',bearish:'bear',neutral:'neu'}, zh={bullish:'看多',bearish:'看空',neutral:'中立'};
function winStart(d){
  if(!d) return -Infinity;
  if(d===1){ const t=new Date(Date.now()); t.setHours(0,0,0,0); return t.getTime(); } // 今天 = local calendar day
  return Date.now()-d*864e5;
}
function inWin(p,d){ return new Date(p.time).getTime()>=winStart(d); }
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function stanceOf(s){ return cls[s]?s:'neutral'; }
function localDateLabel(iso){
  const d=new Date(iso), wd=['日','一','二','三','四','五','六'][d.getDay()];
  return (d.getMonth()+1)+' 月 '+d.getDate()+' 日（週'+wd+'）';
}
function localTime(iso){
  const d=new Date(iso);
  return String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');
}
function dateKey(iso){ const d=new Date(iso); return d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate(); }
function post(p,focus){
  const labs=p.tickers.map(k=>{
    const reason=(focus&&k.t===focus&&k.reason_zh&&!p.paywalled)?` <span style="color:#333">${esc(k.reason_zh)}</span>`:'';
    const st=stanceOf(k.stance);
    return `<span class="${cls[st]}"><span class="tag">${esc(k.t)} ${zh[st]}</span></span>${reason}`;
  }).join(' ');
  const txt=String(p.text||'').replace(/\n\$([A-Z.]+)\n/g,' $$$1 ').replace(/\n{3,}/g,'\n\n');
  const zhText=p.zh?p.zh:txt;
  const pay=p.paywalled?' <span class="mute">付費貼文，只有開頭</span>':'';
  const meta=`<span><span class="mute">${localTime(p.time)}</span>${pay}</span>${/^https:\/\/x\.com\//.test(p.link||'')?`<a href="${esc(p.link)}" target="_blank" rel="noopener noreferrer">在 X 開啟</a>`:''}`;
  const en=p.zh?`<details><summary>英文原文</summary><div class="quoted">${esc(txt)}</div></details>`:'';
  const q=p.quoted?`<details><summary>她回應的內容</summary><div class="quoted">${esc(p.quoted_zh||p.quoted)}${p.quoted_zh?'\n\n原文：'+esc(p.quoted):''}</div></details>`:'';
  return `<div class="post"><div class="meta">${meta}</div><div class="lab">${labs}</div><div class="txt clamp">${esc(zhText)}</div><button class="expand">展開</button>${en}${q}</div>`;
}
function renderPosts(list,focus){
  let out='', lastKey=null;
  for(const p of list){
    const k=dateKey(p.time);
    if(k!==lastKey){ out+=`<div class="dhead">${localDateLabel(p.time)}</div>`; lastKey=k; }
    out+=post(p,focus);
  }
  return out;
}
function applyClamp(container){
  container.querySelectorAll('.txt.clamp').forEach(el=>{
    const btn=el.nextElementSibling;
    if(!el.clientHeight) return; // not laid out yet (e.g. inside closed <details>), measure later
    if(el.scrollHeight<=el.clientHeight+2 && btn && btn.classList.contains('expand')) btn.style.display='none';
  });
  container.querySelectorAll('.expand').forEach(btn=>{
    btn.onclick=()=>{ btn.previousElementSibling.classList.remove('clamp'); btn.style.display='none'; };
  });
}
function render(){
  if(sel){ showStock(); return; }
  document.getElementById('tabs').style.display='';
  document.getElementById('brief').style.display='';
  document.getElementById('listSec').style.display='';
  document.getElementById('tlSec').style.display='';
  document.getElementById('stockSec').style.display='none';

  const posts=DATA.filter(p=>inWin(p,days));
  const bkey=(days===7||days===28)?String(days):'7';
  const pts=BRIEF[bkey]||[];
  document.getElementById('brief').innerHTML=pts.length?('<ol>'+pts.map(t=>`<li>${esc(t)}</li>`).join('')+'</ol>'):'';

  const agg={};
  for(const p of posts) for(const k of p.tickers){
    const a=agg[k.t]??={t:k.t,n:0,bullish:0,bearish:0,neutral:0};
    a.n++; a[stanceOf(k.stance)]++;
  }
  for(const t in agg){
    let found=null, fallback=null;
    for(const p of posts){
      const k=p.tickers.find(x=>x.t===t);
      if(!k) continue;
      if(!fallback) fallback={reason:k.reason_zh,stance:k.stance};
      if(!p.paywalled && k.reason_zh){ found={reason:k.reason_zh,stance:k.stance}; break; }
    }
    const use=found||fallback;
    agg[t].lastReason=use?(use.reason||''):'';
    agg[t].lastStance=stanceOf(use&&use.stance);
  }
  const rows=Object.values(agg).sort((a,b)=>b.n-a.n||a.t.localeCompare(b.t));
  const shown=showAllTk?rows:rows.slice(0,15);
  document.getElementById('tk').innerHTML=shown.map(r=>{
    const mix=(r.bullish>0&&r.bearish>0)?`<span class="mute">多 ${r.bullish}・空 ${r.bearish}</span>`:'';
    return `<div class="tkrow" data-t="${esc(r.t)}"><div class="l1"><span class="sym">${esc(r.t)}</span><span class="mute">提到 ${r.n} 次</span></div><div class="l2"><span class="${cls[r.lastStance]}"><span class="tag">${zh[r.lastStance]}</span></span> <span style="color:#333">${esc(r.lastReason)}</span> ${mix}</div></div>`;
  }).join('')||'<div class="mute">這段時間沒有貼文</div>';
  document.querySelectorAll('.tkrow').forEach(el=>el.onclick=()=>{ sel=el.dataset.t; render(); window.scrollTo(0,0); });
  const moreBtn=document.getElementById('moreBtn');
  if(!showAllTk && rows.length>15){ moreBtn.style.display=''; moreBtn.textContent=`顯示全部 ${rows.length} 檔`; }
  else moreBtn.style.display='none';

  document.getElementById('tl-h').textContent=days?`貼文（${days===1?'今天':days+' 天'}）`:'貼文（全部）';
  const withTk=posts.filter(p=>p.tickers.length>0);
  const noTk=posts.filter(p=>p.tickers.length===0);
  document.getElementById('tl').innerHTML=renderPosts(withTk);
  const otherSec=document.getElementById('otherSec');
  otherSec.innerHTML=noTk.length?(`<summary>其他貼文（沒提到股票）${noTk.length} 則</summary><div>`+renderPosts(noTk)+'</div>'):'';
  otherSec.style.display=noTk.length?'':'none';
  applyClamp(document.getElementById('tl'));
  otherSec.ontoggle=()=>{ if(otherSec.open) applyClamp(otherSec); };
}
function showStock(){
  document.getElementById('tabs').style.display='none';
  document.getElementById('brief').style.display='none';
  document.getElementById('listSec').style.display='none';
  document.getElementById('tlSec').style.display='none';
  document.getElementById('stockSec').style.display='';
  const list=DATA.filter(p=>p.tickers.some(k=>k.t===sel));
  let bull=0,bear=0,neu=0;
  for(const p of list){ const st=stanceOf(p.tickers.find(x=>x.t===sel).stance); if(st==='bullish')bull++; else if(st==='bearish')bear++; else neu++; }
  document.getElementById('stitle').textContent=sel;
  document.getElementById('ssub').textContent=`提到 ${list.length} 次，看多 ${bull}、看空 ${bear}、中立 ${neu}（全部時間）`;
  document.getElementById('stlist').innerHTML=renderPosts(list,sel);
  applyClamp(document.getElementById('stlist'));
}
document.querySelectorAll('#tabs button').forEach(b=>{
  const d=+b.dataset.d, n=DATA.filter(p=>inWin(p,d)).length;
  b.textContent=b.textContent+' · '+n;
  b.onclick=()=>{ days=d; showAllTk=false; document.querySelectorAll('#tabs button').forEach(x=>x.classList.toggle('on',x===b)); render(); };
});
document.getElementById('moreBtn').onclick=()=>{ showAllTk=true; render(); };
document.getElementById('backBtn').onclick=()=>{ sel=null; render(); window.scrollTo(0,0); };
render();
</script></body></html>'''


def render(data, brief, built):
    latest = parse_time(data[0]['time']).astimezone(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M') if data else '-'
    brief = {k: [nodash(s) for s in v if isinstance(s, str)] for k, v in brief.items() if isinstance(v, list)}
    return (HTML.replace('__DATA__', js_json(data)).replace('__BRIEF__', js_json(brief))
            .replace('__LATEST__', latest).replace('__BUILT__', built))


def main(src='data/classified.json', brief_src='data/brief.json', dst='index.html'):
    data = normalize(json.load(open(src)))
    if not data:
        sys.exit(f'{src}: no usable posts, index.html not written')
    bp = pathlib.Path(brief_src)
    brief = json.load(open(bp)) if bp.exists() else {}
    if not bp.exists():
        warn(f'{brief_src} missing, page has no summary')
    built = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')
    out = render(data, brief, built)
    pathlib.Path(dst).write_text(out)
    print(dst, len(out), 'bytes,', len(data), 'posts')


if __name__ == '__main__':
    main()
