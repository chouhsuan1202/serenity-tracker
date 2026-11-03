"""Call the `claude` CLI (uses the Claude subscription, no API key) and parse a JSON answer."""
import json
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from .config import DEFAULT_MODEL

ARRAY = r'\[.*\]'
OBJECT = r'\{.*\}'
TRIES = 3


def model_from_argv():
    return sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL


def ask_json(prompt, model, pattern, check, timeout, tag):
    """Ask up to TRIES times. `check(parsed)` returns the result or raises to retry. None if all tries fail."""
    for _ in range(TRIES):
        r = subprocess.run(['claude', '-p', '--model', model, prompt],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=timeout)
        m = re.search(pattern, r.stdout, re.S)
        try:
            return check(json.loads(m.group(0)))
        except Exception as e:
            print('retry', tag, e, r.stdout[:200], r.stderr[:200], file=sys.stderr, flush=True)
            time.sleep(3)
    return None


def matched_by_id(batch):
    """A `check` for batch answers: one item per post, matched by id (not position), in batch order."""
    def check(res):
        assert len(res) == len(batch)
        byid = {str(x.get('id')): x for x in res}
        assert set(byid) == {str(x['id']) for x in batch}, 'ids do not match batch'
        return [byid[str(x['id'])] for x in batch]
    return check


def run_batches(todo, size, work, workers=4):
    """Call work(start, batch, lock) for each slice of `todo`, 4 at a time. Returns the start index of failed batches."""
    lock, failed = threading.Lock(), []

    def one(i):
        if not work(i, todo[i:i + size], lock):
            failed.append(i)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(one, range(0, len(todo), size)))
    return failed
