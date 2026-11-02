"""Add Traditional Chinese fields to data/classified.json: zh (post), reason_zh, theme_zh. Incremental, parallel."""
import json, subprocess, sys, re, time, threading
from concurrent.futures import ThreadPoolExecutor
MODEL = sys.argv[1] if len(sys.argv) > 1 else 'sonnet'
P = 'data/classified.json'
data = json.load(open(P)); byid = {x['id']: x for x in data}
todo = [x for x in data if 'zh' not in x]
PROMPT = """把下面每則 X 貼文翻成繁體中文（台灣用語），給一個閱讀吃力的人看。
規則：
- zh：整則貼文的白話翻譯。短句，一句一個意思，砍掉贅字與語氣詞，數字、公司名、股票代號原樣保留。不要加自己的解讀。若原文結尾是「…」表示被截斷，翻到那裡就停，結尾也加「…」。
- quoted_zh：quoted 欄位（她回應或引用的別人的話）的白話翻譯，沒有就空字串。
- reasons_zh：對應 tickers 陣列裡每個 reason 的中文，順序一樣，每個 15 字內。
- theme_zh：theme 的中文，5 字內，沒有就空字串。
- 絕對不用破折號。
只回傳 JSON 陣列，順序同輸入：{"id":..., "zh":"...", "quoted_zh":"...", "reasons_zh":[...], "theme_zh":"..."}
貼文：
"""
lock = threading.Lock(); B = 20; failed = []
def work(i):
    batch = todo[i:i+B]
    payload = [{'id': x['id'], 'text': x['text'], 'quoted': x['quoted'], 'tickers': [k['reason'] for k in x['tickers']], 'theme': x['theme']} for x in batch]
    for attempt in range(3):
        r = subprocess.run(['claude', '-p', '--model', MODEL, PROMPT + json.dumps(payload, ensure_ascii=False)], capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=900)
        m = re.search(r'\[.*\]', r.stdout, re.S)
        try:
            res = json.loads(m.group(0)); assert len(res) == len(batch)
            got = {str(x.get('id')): x for x in res}
            assert set(got) == {str(x['id']) for x in batch}, 'ids do not match batch'
            res = [got[str(x['id'])] for x in batch]; break
        except Exception as e:
            print('retry', i, e, r.stdout[:200], r.stderr[:200], file=sys.stderr, flush=True); time.sleep(3)
    else:
        print('failed', i, flush=True); failed.append(i); return
    with lock:
        for x, t in zip(batch, res):
            x['zh'] = t.get('zh', ''); x['quoted_zh'] = t.get('quoted_zh', ''); x['theme_zh'] = t.get('theme_zh', '')
            rz = t.get('reasons_zh', [])
            for k, z in zip(x['tickers'], rz): k['reason_zh'] = z
        json.dump(data, open(P, 'w'), ensure_ascii=False, indent=1)
        print(f"{sum(1 for x in data if 'zh' in x)}/{len(data)}", flush=True)
with ThreadPoolExecutor(4) as ex: list(ex.map(work, range(0, len(todo), B)))
bad = sum(1 for x in data for k in x['tickers'] if 'reason_zh' not in k)
print('done', sum(1 for x in data if 'zh' in x), 'of', len(data), 'missing reason_zh', bad)
if failed or bad:
    sys.exit(f'translate: {len(failed)} batch(es) failed, {bad} reasons untranslated')
