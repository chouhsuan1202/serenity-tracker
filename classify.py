"""Classify Serenity tweets: tickers + stance. Uses claude CLI (subscription), no API key."""
import json, subprocess, sys, re, pathlib, time
RAW = pathlib.Path('data/tweets_raw.json'); OUT = pathlib.Path('data/classified.json')
MODEL = sys.argv[1] if len(sys.argv) > 1 else 'sonnet'
tweets = json.load(open(RAW))
done = {x['id']: x for x in json.load(open(OUT))} if OUT.exists() else {}
todo = [t for t in tweets if t['id'] not in done]
PROMPT = """You label stock opinions in posts by Serenity (@aleabitoreddit), an AI/semiconductor supply-chain analyst on X.
For EACH post return the tickers/companies explicitly discussed and the author's stance on each.
Rules:
- stance: "bullish", "bearish", or "neutral" (mentioned as fact/news with no clear view). Only bullish/bearish when the author's own view is clear.
- Use the ticker if given (e.g. NVDA, SIVE). Taiwan/foreign names without a US ticker: use the name (e.g. "ESMT (3006)", "Samsung", "Soitec").
- Skip index ETFs, and skip companies that are only mentioned in passing as a counterparty, unless the author expresses a view on them.
- Criticism of management, IR, or communication is NOT bearish unless she expects the stock to fall or says she is selling. Sarcasm mocking shorts or bears is bullish.
- reason: at most 15 words, in the author's framing.
- theme: 1 to 3 words (e.g. "CW lasers", "legacy memory", "neoclouds", "macro"). Use "" if none.
- If the post has a "quoted" field, that is someone else's text the author is replying to or quoting. Use it only for context.
- Posts ending with "…" are paywalled teasers: label only what the teaser itself supports.
Return ONLY a JSON array, one object per post, same order: {"id":..., "tickers":[{"t":"NVDA","stance":"bullish","reason":"..."}], "theme":"..."}
Posts:
"""
B = 20
from concurrent.futures import ThreadPoolExecutor
import threading
lock = threading.Lock()
def work(i):
    batch = todo[i:i+B]
    payload = [{'id': t['id'], 'text': t['text'], 'quoted': t['quoted']} for t in batch]
    for attempt in range(3):
        r = subprocess.run(['claude', '-p', '--model', MODEL, PROMPT + json.dumps(payload, ensure_ascii=False)],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=600)
        m = re.search(r'\[.*\]', r.stdout, re.S)
        try:
            res = json.loads(m.group(0)); assert len(res) == len(batch); break
        except Exception as e:
            print('retry', i, e, r.stdout[:200], r.stderr[:200], file=sys.stderr); time.sleep(3)
    else:
        print('failed batch %d' % i, flush=True); return 0
    with lock:
        for t, lab in zip(batch, res):
            done[t['id']] = {**t, 'tickers': lab.get('tickers', []), 'theme': lab.get('theme', ''), 'paywalled': t['text'].endswith('…')}
        json.dump(list(done.values()), open(OUT, 'w'), ensure_ascii=False, indent=1)
        print(f'{len(done)}/{len(tweets)}', flush=True)
    return len(batch)
with ThreadPoolExecutor(4) as ex: list(ex.map(work, range(0, len(todo), B)))
print('done', len(done), 'of', len(tweets))
