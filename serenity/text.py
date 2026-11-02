"""Small text and time helpers."""
import datetime
import sys

from .config import DASHES


def warn(msg):
    print('WARN', msg, file=sys.stderr, flush=True)


def nodash(s):
    """Replace every dash-like character with a plain '-'. Non-strings pass through."""
    if not isinstance(s, str):
        return s
    for d in DASHES:
        s = s.replace(d, '-')
    return s


def parse_time(s):
    """ISO time string to an aware datetime (UTC if no zone given), or None if unreadable."""
    try:
        d = datetime.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)


def utc_minute(d):
    """Format an aware datetime as 'YYYY-MM-DD HH:MM' in UTC."""
    return d.astimezone(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')
