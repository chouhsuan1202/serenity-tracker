"""Generate data/brief.json: short summary of Serenity's posts for last 7 and 28 days.
Uses claude CLI (subscription), no API key. If a summary fails, the previous one is kept. Usage: python3 brief.py [model]"""
import datetime
import json
import sys

from serenity.claude_cli import OBJECT, ask_json, model_from_argv
from serenity.config import BRIEF, CLASSIFIED
from serenity.text import parse_time

PROMPT = """下面是 X 帳號 Serenity（半導體供應鏈分析師）最近 %d 天的貼文摘要。
幫我整理成 3 到 5 條重點，給一個閱讀吃力的人快速掃過。
規則：
- 每條 25 字以內，白話，講她在說什麼、對哪些股票看多或看空。
- 不加投資建議。批評管理層不算看空；只有她明講看空或會跌才寫看空，不猜未來，只講她講過的事。
- 不用破折號。
- 只回傳 JSON 物件：{"points":["...", "..."]}
貼文：
"""
WINDOWS = ('7', '28')


def window(data, days, now=None):
    """Posts from the last `days` days, reduced to what the summary needs."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    cut = now - datetime.timedelta(days=days)
    return [{'time': x['time'], 'zh': x.get('zh', ''),
             'tickers': [{'t': k['t'], 'stance': k['stance'], 'reason_zh': k.get('reason_zh', '')} for k in x['tickers']]}
            for x in data if parse_time(x['time']) >= cut]


def check_points(res):
    pts = res.get('points', [])
    assert isinstance(pts, list) and len(pts) >= 1
    return pts


def ask(data, days, model):
    payload = window(data, days)
    if not payload:
        return []  # no posts in window: an empty summary is correct
    pts = ask_json(PROMPT % days + json.dumps(payload, ensure_ascii=False), model, OBJECT, check_points, 300, days)
    if pts is None:
        print('failed', days, flush=True)
    return pts


def main():
    model = model_from_argv()
    data = json.load(open(CLASSIFIED))
    old = json.load(open(BRIEF)) if BRIEF.exists() else {}
    brief, failed = {}, []
    for d in WINDOWS:
        pts = ask(data, int(d), model)
        if pts is None:  # keep the previous summary instead of silently blanking it
            failed.append(d); pts = old.get(d, [])
        brief[d] = pts
    json.dump(brief, open(BRIEF, 'w'), ensure_ascii=False, indent=1)
    print('brief.json', brief)
    if failed:
        sys.exit(f'brief: {",".join(failed)}-day summary failed, kept previous version')


if __name__ == '__main__':
    main()
