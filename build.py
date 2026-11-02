"""Build index.html from data/classified.json and data/brief.json (single file, data embedded).
Usage: python3 build.py"""
import datetime
import json
import pathlib
import sys

from serenity.config import ALIAS, BRIEF, CLASSIFIED, DASHES, INDEX  # noqa: F401  (re-exported for tests)
from serenity.normalize import normalize
from serenity.page import js_json, render  # noqa: F401
from serenity.text import nodash, parse_time, utc_minute, warn  # noqa: F401


def main(src=str(CLASSIFIED), brief_src=str(BRIEF), dst=str(INDEX)):
    data = normalize(json.load(open(src)))
    if not data:
        sys.exit(f'{src}: no usable posts, index.html not written')
    bp = pathlib.Path(brief_src)
    brief = json.load(open(bp)) if bp.exists() else {}
    if not bp.exists():
        warn(f'{brief_src} missing, page has no summary')
    out = render(data, brief, utc_minute(datetime.datetime.now(datetime.timezone.utc)))
    pathlib.Path(dst).write_text(out)
    print(dst, len(out), 'bytes,', len(data), 'posts')


if __name__ == '__main__':
    main()
