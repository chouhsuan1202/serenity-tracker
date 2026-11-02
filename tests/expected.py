"""Independent re-count of what the page should show, straight from data/classified.json.
Usage: python3 tests/expected.py <now ISO> <IANA tz>"""
import json, sys, pathlib, datetime, zoneinfo
from collections import Counter, defaultdict
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from build import ALIAS  # shared config only, counting logic is separate

now = datetime.datetime.fromisoformat(sys.argv[1].replace('Z', '+00:00'))
tz = zoneinfo.ZoneInfo(sys.argv[2])
posts = json.load(open(ROOT / 'data/classified.json'))
local_midnight = now.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
starts = {'1': local_midnight, '7': now - datetime.timedelta(days=7), '28': now - datetime.timedelta(days=28), '0': None}
out = {}
for key, start in starts.items():
    win = [p for p in posts if start is None or datetime.datetime.fromisoformat(p['time'].replace('Z', '+00:00')) >= start]
    agg = defaultdict(Counter)
    for p in win:
        first = {}
        for k in p['tickers']:
            t = k['t'].strip().lstrip('$'); t = ALIAS.get(t, t)
            first.setdefault(t, k['stance'] if k['stance'] in ('bullish', 'bearish', 'neutral') else 'neutral')
        for t, st in first.items():
            agg[t]['n'] += 1; agg[t][st] += 1
    out[key] = {'posts': len(win), 'with_tickers': sum(1 for p in win if p['tickers']),
                'tickers': {t: dict(c) for t, c in agg.items()}}
print(json.dumps(out, ensure_ascii=False))
