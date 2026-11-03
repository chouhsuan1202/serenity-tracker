"""Merge data/incoming.json (from receiver.py) into data/tweets_raw.json. Posts already known are kept as they are."""
import json
import sys

from serenity.config import INCOMING, POST_KEYS, RAW


def valid(x):
    return isinstance(x, dict) and all(isinstance(x.get(k), str) for k in POST_KEYS) and bool(x['id']) and bool(x['time'])


def merge(old, new):
    """Returns (merged list newest first, number added, malformed posts)."""
    byid = {x['id']: x for x in old}
    n0 = len(byid)
    bad = [x for x in new if not valid(x)]
    for x in new:
        if valid(x):
            byid.setdefault(x['id'], x)
    return sorted(byid.values(), key=lambda x: x['time'], reverse=True), len(byid) - n0, bad


def main():
    old = json.load(open(RAW)) if RAW.exists() else []
    new = json.load(open(INCOMING))
    if not isinstance(new, list):
        sys.exit(f'{INCOMING}: expected a JSON list of posts')
    merged, added, bad = merge(old, new)
    json.dump(merged, open(RAW, 'w'), ensure_ascii=False, indent=1)
    print('added', added, 'total', len(merged))
    if bad:
        print(f'skipped {len(bad)} malformed post(s), e.g. {str(bad[0])[:200]}', file=sys.stderr)


if __name__ == '__main__':
    main()
