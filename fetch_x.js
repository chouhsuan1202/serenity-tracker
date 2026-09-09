// 在 x.com/aleabitoreddit 頁面執行（Chrome 已登入 X）。捲動收集貼文，存到 window.__ser。
// 之後用 location.href='http://127.0.0.1:8765/receive#'+encodeURIComponent(JSON.stringify(Object.values(window.__ser))) 送回本機 receiver.py
window.__ser = window.__ser || {};
const grab=()=>{ for(const a of document.querySelectorAll('article')){
  const link=[...a.querySelectorAll('a[href*="/status/"]')].map(x=>x.getAttribute('href')).find(h=>/^\/[^/]+\/status\/\d+$/.test(h));
  if(!link) continue; const id=link.split('/status/')[1]; if(window.__ser[id]) continue;
  const t=a.querySelector('[data-testid="tweetText"]')?.innerText||'';
  const time=a.querySelector('time')?.getAttribute('datetime')||'';
  const social=a.querySelector('[data-testid="socialContext"]')?.innerText||'';
  const author=link.split('/')[1];
  const quoted=[...a.querySelectorAll('[data-testid="tweetText"]')].slice(1).map(q=>q.innerText).join(' | ');
  window.__ser[id]={id,link:'https://x.com'+link,author,time,text:t,social,quoted:quoted.slice(0,300)};
}};
for(let i=0;i<25;i++){ grab(); window.scrollBy(0,2500); await new Promise(r=>setTimeout(r,700)); }
grab();
