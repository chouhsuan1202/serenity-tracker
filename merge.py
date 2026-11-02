import json, pathlib, sys
raw = pathlib.Path('data/tweets_raw.json'); inc = pathlib.Path('data/incoming.json')
old = {x['id']: x for x in json.load(open(raw))} if raw.exists() else {}
new = json.load(open(inc)); n0 = len(old)
if not isinstance(new, list):
    sys.exit(f'{inc}: expected a JSON list of posts')
KEYS = ('id', 'link', 'author', 'time', 'text', 'social', 'quoted')
bad = [x for x in new if not isinstance(x, dict) or any(not isinstance(x.get(k), str) for k in KEYS) or not x['id'] or not x['time']]
for x in new:
    if x not in bad:
        old.setdefault(x['id'], x)
json.dump(sorted(old.values(), key=lambda x: x['time'], reverse=True), open(raw, 'w'), ensure_ascii=False, indent=1)
print('added', len(old) - n0, 'total', len(old))
if bad:
    print(f'skipped {len(bad)} malformed post(s), e.g. {str(bad[0])[:200]}', file=sys.stderr)
