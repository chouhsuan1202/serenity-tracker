#!/bin/sh
set -e
cd "$(dirname "$0")"
[ -f data/incoming.json ] && python3 merge.py
python3 classify.py sonnet
python3 translate.py sonnet
python3 brief.py sonnet || echo "brief.py 失敗，沿用舊的重點摘要" >&2
python3 build.py
