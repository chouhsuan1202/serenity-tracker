"""Build index.html from data/classified.json (single file, data embedded)."""
import json, pathlib, datetime
data = json.load(open('data/classified.json'))
data.sort(key=lambda x: x['time'], reverse=True)
ALIAS = {'SK Hynix': 'SKHY', 'Mediatek': 'MediaTek', 'ESMT': 'ESMT (3006)', 'Sandisk': 'SNDK', 'SanDisk': 'SNDK', 'Micron': 'MU', 'Nvidia': 'NVDA'}
for p in data:
    seen = {}
    for k in p['tickers']:
        k['t'] = ALIAS.get(k['t'].lstrip('$'), k['t'].lstrip('$'))
        seen.setdefault(k['t'], k)
    p['tickers'] = list(seen.values())
built = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
latest = max(x['time'] for x in data)[:16].replace('T', ' ')
HTML = r'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Serenity 觀點追蹤</title>
<style>
:root{--fg:#111;--mute:#6b6b6b;--line:#e4e4e4;--bg:#fff;--bull:#0a7a3f;--bear:#c0392b;--neu:#777;--hl:#f5f5f5}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 "Noto Sans TC",-apple-system,BlinkMacSystemFont,"PingFang TC","Segoe UI",sans-serif}
main{max-width:1040px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:22px;margin:0 0 4px;font-weight:700}
.sub{color:var(--mute);font-size:13px;margin-bottom:22px}
.tabs{display:flex;gap:4px;margin-bottom:18px}
.tabs button{border:1px solid var(--line);background:#fff;padding:6px 14px;border-radius:999px;font:inherit;font-size:14px;cursor:pointer;color:var(--fg)}
.tabs button.on{background:var(--fg);color:#fff;border-color:var(--fg)}
.stats{display:flex;gap:28px;margin-bottom:22px;font-size:14px;color:var(--mute)}
.stats b{color:var(--fg);font-size:20px;display:block;font-weight:600}
h2{font-size:16px;margin:26px 0 10px;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:14px}
th{text-align:left;font-weight:500;color:var(--mute);border-bottom:1px solid var(--line);padding:6px 8px;font-size:13px}
td{padding:8px;border-bottom:1px solid var(--line);vertical-align:top}
tr.row{cursor:pointer}
tr.row:hover td{background:var(--hl)}
tr.row.sel td{background:var(--hl)}
.num{text-align:right;font-variant-numeric:tabular-nums}
.bull{color:var(--bull)}.bear{color:var(--bear)}.neu{color:var(--neu)}
.tag{display:inline-block;font-size:12px;padding:1px 7px;border-radius:4px;border:1px solid currentColor;line-height:1.5;margin-right:6px;white-space:nowrap}
.post{padding:12px 0;border-bottom:1px solid var(--line)}
.post .meta{font-size:12px;color:var(--mute);margin-bottom:4px}
.post .meta a{color:var(--mute)}
.post .lab{margin:2px 0 6px;font-size:13px}
.post .lab span{margin-right:10px}
.post .txt{white-space:pre-wrap;color:#333;font-size:14px}
.post .quoted{margin-top:6px;padding-left:10px;border-left:2px solid var(--line);color:var(--mute);font-size:13px;white-space:pre-wrap}
details summary{cursor:pointer;color:var(--mute);font-size:13px}
#drill{margin-top:8px}
.close{float:right;font-size:13px;color:var(--mute);cursor:pointer;background:none;border:0;font:inherit}
.note{color:var(--mute);font-size:12px;margin-top:6px}
@media(max-width:640px){.stats{gap:16px;flex-wrap:wrap}td,th{padding:6px 4px}.hidem{display:none}}
</style></head><body><main>
<h1>Serenity 觀點追蹤</h1>
<div class="sub">@aleabitoreddit 公開貼文 · 最新貼文 __LATEST__ UTC · 更新 __BUILT__ · 立場由 AI 判讀，可能出錯，不是投資建議</div>
<div class="tabs" id="tabs"><button data-d="1">今天</button><button data-d="7" class="on">7 天</button><button data-d="28">28 天</button><button data-d="0">全部</button></div>
<div class="stats" id="stats"></div>
<h2>提到的股票</h2>
<table id="tk"><thead><tr><th>股票</th><th class="num">提到</th><th class="num bull">看多</th><th class="num bear">看空</th><th class="num neu">中立</th><th>最新立場</th><th class="hidem">主題</th><th class="hidem">最近一次</th></tr></thead><tbody></tbody></table>
<div class="note">點一檔股票看她每一次怎麼講。</div>
<div id="drill"></div>
<h2 id="tl-h">貼文</h2>
<div id="tl"></div>
</main>
<script>
const DATA=__DATA__;
let days=7, sel=null;
const fmt=t=>t.slice(0,10);
const cls={bullish:'bull',bearish:'bear',neutral:'neu'}, zh={bullish:'看多',bearish:'看空',neutral:'中立'};
function inWin(p){ if(!days) return true; const cut=Date.now()-days*864e5; return new Date(p.time).getTime()>=cut; }
function render(){
  const posts=DATA.filter(inWin);
  const agg={};
  for(const p of posts) for(const k of p.tickers){ const a=agg[k.t]??={t:k.t,n:0,bullish:0,bearish:0,neutral:0,last:null,themes:{}}; a.n++; a[k.stance]=(a[k.stance]||0)+1; if(!a.last||p.time>a.last.time) a.last={time:p.time,stance:k.stance,reason:k.reason_zh||k.reason}; const th=p.theme_zh||p.theme; if(th) a.themes[th]=(a.themes[th]||0)+1; }
  const rows=Object.values(agg).sort((a,b)=>b.n-a.n||a.t.localeCompare(b.t));
  const nb=rows.filter(r=>r.bullish>r.bearish).length, ns=rows.filter(r=>r.bearish>r.bullish).length;
  document.getElementById('stats').innerHTML=`<div><b>${posts.length}</b>貼文</div><div><b>${rows.length}</b>股票</div><div><b class="bull">${nb}</b>偏多</div><div><b class="bear">${ns}</b>偏空</div>`;
  document.querySelector('#tk tbody').innerHTML=rows.map(r=>{const th=Object.entries(r.themes).sort((a,b)=>b[1]-a[1]).slice(0,2).map(x=>x[0]).join('、');
    return `<tr class="row${sel===r.t?' sel':''}" data-t="${r.t}"><td><b>${r.t}</b></td><td class="num">${r.n}</td><td class="num bull">${r.bullish||''}</td><td class="num bear">${r.bearish||''}</td><td class="num neu">${r.neutral||''}</td><td><span class="${cls[r.last.stance]}">${zh[r.last.stance]}</span> <span style="color:var(--mute)">${r.last.reason}</span></td><td class="hidem" style="color:var(--mute)">${th}</td><td class="hidem" style="color:var(--mute)">${fmt(r.last.time)}</td></tr>`}).join('')||'<tr><td colspan=8 style="color:var(--mute)">這段時間沒有貼文</td></tr>';
  document.querySelectorAll('#tk tr.row').forEach(tr=>tr.onclick=()=>{sel=sel===tr.dataset.t?null:tr.dataset.t;render();});
  const list=sel?DATA.filter(p=>p.tickers.some(k=>k.t===sel)):posts;
  document.getElementById('drill').innerHTML=sel?`<h2>${sel} 的每一次提及（全部時間）<button class="close" id="cl">收起</button></h2>`+list.map(p=>post(p,sel)).join(''):'';
  if(sel) document.getElementById('cl').onclick=()=>{sel=null;render();};
  document.getElementById('tl-h').textContent=days?`貼文（${days===1?'今天':days+' 天'}）`:'貼文（全部）';
  document.getElementById('tl').innerHTML=posts.map(p=>post(p)).join('');
}
function post(p,focus){
  const labs=p.tickers.map(k=>`<span class="${cls[k.stance]}"><span class="tag">${k.t} ${zh[k.stance]}</span>${focus===k.t||p.tickers.length<=3?(k.reason_zh||k.reason):''}</span>`).join('');
  const txt=p.text.replace(/\n\$([A-Z.]+)\n/g,' $$$1 ').replace(/\n{3,}/g,'\n\n');
  const body=p.zh?`<div class="txt">${esc(p.zh)}</div><details><summary>原文</summary><div class="quoted">${esc(txt)}</div></details>`:`<div class="txt">${esc(txt)}</div>`;
  const q=p.quoted?`<details><summary>她回應或引用的內容</summary><div class="quoted">${esc(p.quoted_zh||p.quoted)}${p.quoted_zh?'\n\n原文：'+esc(p.quoted):''}</div></details>`:'';
  const th=p.theme_zh||p.theme;
  return `<div class="post"><div class="meta">${p.time.slice(0,16).replace('T',' ')} UTC · <a href="${p.link}" target="_blank">原文連結</a>${p.paywalled?' · 付費內容，只看得到開頭':''}${th?' · '+th:''}</div><div class="lab">${labs}</div>${body}${q}</div>`;
}
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
document.querySelectorAll('#tabs button').forEach(b=>b.onclick=()=>{days=+b.dataset.d;document.querySelectorAll('#tabs button').forEach(x=>x.classList.toggle('on',x===b));render();});
render();
</script></body></html>'''
out = HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False)).replace('__LATEST__', latest).replace('__BUILT__', built)
pathlib.Path('index.html').write_text(out)
print('index.html', len(out), 'bytes,', len(data), 'posts')
