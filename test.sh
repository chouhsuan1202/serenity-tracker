#!/bin/sh
# Run every test, same as GitHub Actions. Needs python3, node, and playwright (npm install --no-save playwright).
set -e
cd "$(dirname "$0")"
python3 -m unittest discover tests
node --test tests/calc.test.js
python3 build.py
node tests/page.test.js
