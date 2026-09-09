import json, pathlib
raw = pathlib.Path('data/tweets_raw.json'); inc = pathlib.Path('data/incoming.json')
old = {x['id']: x for x in json.load(open(raw))} if raw.exists() else {}
new = json.load(open(inc)); n0 = len(old)
for x in new: old.setdefault(x['id'], x)
json.dump(sorted(old.values(), key=lambda x: x['time'], reverse=True), open(raw, 'w'), ensure_ascii=False, indent=1)
print('added', len(old) - n0, 'total', len(old))
