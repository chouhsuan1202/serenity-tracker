"""Add Traditional Chinese fields to data/classified.json: zh (post), quoted_zh, reason_zh, theme_zh.
Incremental (posts that already have zh are skipped), 4 batches in parallel. Usage: python3 translate.py [model]"""
import json
import sys

from serenity.claude_cli import ARRAY, ask_json, matched_by_id, model_from_argv, run_batches
from serenity.config import CLASSIFIED

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
BATCH = 20


def main():
    model = model_from_argv()
    data = json.load(open(CLASSIFIED))
    todo = [x for x in data if 'zh' not in x]

    def work(start, batch, lock):
        payload = [{'id': x['id'], 'text': x['text'], 'quoted': x['quoted'], 'tickers': [k['reason'] for k in x['tickers']], 'theme': x['theme']} for x in batch]
        res = ask_json(PROMPT + json.dumps(payload, ensure_ascii=False), model, ARRAY, matched_by_id(batch), 900, start)
        if res is None:
            print('failed', start, flush=True)
            return False
        with lock:
            for x, t in zip(batch, res):
                x['zh'] = t.get('zh', ''); x['quoted_zh'] = t.get('quoted_zh', ''); x['theme_zh'] = t.get('theme_zh', '')
                for k, z in zip(x['tickers'], t.get('reasons_zh', [])):
                    k['reason_zh'] = z
            json.dump(data, open(CLASSIFIED, 'w'), ensure_ascii=False, indent=1)
            print(f"{sum(1 for x in data if 'zh' in x)}/{len(data)}", flush=True)
        return True

    failed = run_batches(todo, BATCH, work)
    bad = sum(1 for x in data for k in x['tickers'] if 'reason_zh' not in k)
    print('done', sum(1 for x in data if 'zh' in x), 'of', len(data), 'missing reason_zh', bad)
    if failed or bad:
        sys.exit(f'translate: {len(failed)} batch(es) failed, {bad} reasons untranslated')


if __name__ == '__main__':
    main()
