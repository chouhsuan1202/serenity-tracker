"""Turn clean posts into the single-file index.html (CSS, scripts and data all inline, no outside requests)."""
import json
import re

from .config import WEB
from .text import nodash, parse_time, utc_minute


def js_json(obj):
    """JSON safe to embed inside <script>: no '</script>' breakout, no HTML comment tricks."""
    s = json.dumps(obj, ensure_ascii=False)
    return (s.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
             .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def fill(template, values):
    """Replace every placeholder in one pass, so text inside the data is never rewritten."""
    return re.sub('|'.join(map(re.escape, values)), lambda m: values[m.group(0)], template)


def clean_brief(brief):
    """Keep only lists of strings, without dashes."""
    return {k: [nodash(s) for s in v if isinstance(s, str)] for k, v in brief.items() if isinstance(v, list)}


def render(data, brief, built):
    """data: output of normalize() (newest first). brief: {'7': [...], '28': [...]}. built: build time label."""
    latest = utc_minute(parse_time(data[0]['time'])) if data else '-'
    shell = fill((WEB / 'template.html').read_text(), {
        '__CSS__': (WEB / 'style.css').read_text(),
        '__CALC_JS__': (WEB / 'calc.js').read_text().rstrip('\n'),
        '__VIEW_JS__': (WEB / 'view.js').read_text().rstrip('\n'),
    })
    return fill(shell, {'__DATA__': js_json(data), '__BRIEF__': js_json(clean_brief(brief)),
                        '__LATEST__': latest, '__BUILT__': built})
