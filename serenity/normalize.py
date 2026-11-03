"""Clean data/classified.json for the page. Bad records are dropped or fixed loudly, never silently."""
from .config import ALIAS, STANCES
from .text import nodash, parse_time, warn

TEXT_FIELDS = ('text', 'quoted', 'zh', 'quoted_zh', 'theme', 'theme_zh')


def ticker_name(raw):
    """'$Micron ' -> 'MU': strip spaces and $, then apply ALIAS."""
    t = raw.strip().lstrip('$')
    return ALIAS.get(t, t)


def _clean_tickers(pid, tickers):
    seen = {}
    for k in tickers or []:
        if not isinstance(k, dict) or not isinstance(k.get('t'), str) or not k['t'].strip('$ '):
            warn(f'post {pid}: bad ticker {k!r}, skipped')
            continue
        k['t'] = ticker_name(k['t'])
        if k.get('stance') not in STANCES:
            warn(f'post {pid}: {k["t"]} unknown stance {k.get("stance")!r}, shown as neutral')
            k['stance'] = 'neutral'
        seen.setdefault(k['t'], k)  # same company twice in one post: keep the first
    out = list(seen.values())
    for k in out:
        k['reason'] = nodash(k.get('reason', ''))
        k['reason_zh'] = nodash(k.get('reason_zh', ''))
    return out


def normalize(data):
    out = []
    for p in data:
        pid = p.get('id', '?')
        if not isinstance(p.get('time'), str) or parse_time(p['time']) is None:
            warn(f'post {pid}: bad time {p.get("time")!r}, skipped')
            continue
        link = p.get('link', '')
        if not (isinstance(link, str) and link.startswith('https://x.com/')):
            warn(f'post {pid}: unexpected link {link!r}, removed')
            p['link'] = ''
        if not isinstance(p.get('text'), str):
            p['text'] = ''
        if 'zh' not in p:
            warn(f'post {pid}: no zh translation (run translate.py)')
        p['tickers'] = _clean_tickers(pid, p.get('tickers'))
        for field in TEXT_FIELDS:
            if field in p:
                p[field] = nodash(p[field])
        p['paywalled'] = bool(p.get('paywalled'))
        out.append(p)
    out.sort(key=lambda x: parse_time(x['time']), reverse=True)
    return out
