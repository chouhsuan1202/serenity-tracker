"""Generate data/brief.json: short summary of Serenity's posts for last 7 and 28 days. Uses claude CLI (subscription), no API key."""
import json, subprocess, sys, re, time, datetime, pathlib

MODEL = sys.argv[1] if len(sys.argv) > 1 else 'sonnet'
IN = pathlib.Path('data/classified.json')
OUT = pathlib.Path('data/brief.json')
data = json.load(open(IN))

PROMPT = """下面是 X 帳號 Serenity（半導體供應鏈分析師）最近 %d 天的貼文摘要。
幫我整理成 3 到 5 條重點，給一個閱讀吃力的人快速掃過。
規則：
- 每條 25 字以內，白話，講她在說什麼、對哪些股票看多或看空。
- 不加投資建議。批評管理層不算看空；只有她明講看空或會跌才寫看空，不猜未來，只講她講過的事。
- 不用破折號。
- 只回傳 JSON 物件：{"points":["...", "..."]}
貼文：
"""

def window(days):
    cut = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    posts = [x for x in data if datetime.datetime.fromisoformat(x['time'].replace('Z', '+00:00')) >= cut]
    payload = [{'time': x['time'], 'zh': x.get('zh', ''),
                'tickers': [{'t': k['t'], 'stance': k['stance'], 'reason_zh': k.get('reason_zh', '')} for k in x['tickers']]}
               for x in posts]
    return payload

def ask(days):
    payload = window(days)
    if not payload:
        return []  # no posts in window: an empty summary is correct
    for attempt in range(3):
        r = subprocess.run(['claude', '-p', '--model', MODEL, PROMPT % days + json.dumps(payload, ensure_ascii=False)],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=300)
        m = re.search(r'\{.*\}', r.stdout, re.S)
        try:
            res = json.loads(m.group(0))
            pts = res.get('points', [])
            assert isinstance(pts, list) and len(pts) >= 1
            return pts
        except Exception as e:
            print('retry', days, e, r.stdout[:200], r.stderr[:200], file=sys.stderr, flush=True)
            time.sleep(3)
    print('failed', days, flush=True)
    return None

old = json.load(open(OUT)) if OUT.exists() else {}
brief, failed = {}, []
for d in ('7', '28'):
    pts = ask(int(d))
    if pts is None:  # keep the previous summary instead of silently blanking it
        failed.append(d); pts = old.get(d, [])
    brief[d] = pts
json.dump(brief, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('brief.json', brief)
if failed:
    sys.exit(f'brief: {",".join(failed)}-day summary failed, kept previous version')
