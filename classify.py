"""Classify Serenity tweets: tickers + stance. Uses claude CLI (subscription), no API key.
Incremental: posts already in data/classified.json are not sent again. Usage: python3 classify.py [model]"""
import json
import sys

from serenity.claude_cli import ARRAY, ask_json, matched_by_id, model_from_argv, run_batches
from serenity.config import CLASSIFIED, RAW

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
BATCH = 20


def main():
    model = model_from_argv()
    tweets = json.load(open(RAW))
    done = {x['id']: x for x in json.load(open(CLASSIFIED))} if CLASSIFIED.exists() else {}
    todo = [t for t in tweets if t['id'] not in done]

    def work(start, batch, lock):
        payload = [{'id': t['id'], 'text': t['text'], 'quoted': t['quoted']} for t in batch]
        res = ask_json(PROMPT + json.dumps(payload, ensure_ascii=False), model, ARRAY, matched_by_id(batch), 600, start)
        if res is None:
            print('failed batch %d' % start, flush=True)
            return False
        with lock:
            for t, lab in zip(batch, res):
                done[t['id']] = {**t, 'tickers': lab.get('tickers', []), 'theme': lab.get('theme', ''), 'paywalled': t['text'].endswith('…')}
            json.dump(list(done.values()), open(CLASSIFIED, 'w'), ensure_ascii=False, indent=1)
            print(f'{len(done)}/{len(tweets)}', flush=True)
        return True

    failed = run_batches(todo, BATCH, work)
    print('done', len(done), 'of', len(tweets))
    if failed:
        sys.exit(f'classify: {len(failed)} batch(es) failed, {len(tweets) - len(done)} posts unlabeled')


if __name__ == '__main__':
    main()
