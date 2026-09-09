#!/bin/zsh
cd "$(dirname "$0")"
[ -f data/incoming.json ] && python3 merge.py
python3 classify.py sonnet && python3 build.py
