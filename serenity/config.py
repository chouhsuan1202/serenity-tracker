"""Settings shared by every step of the pipeline."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEB = ROOT / 'web'

# Data files, relative to the working directory (the scripts are run from the repo root).
RAW = pathlib.Path('data/tweets_raw.json')
INCOMING = pathlib.Path('data/incoming.json')
CLASSIFIED = pathlib.Path('data/classified.json')
BRIEF = pathlib.Path('data/brief.json')
INDEX = pathlib.Path('index.html')

DEFAULT_MODEL = 'sonnet'

# Different spellings of the same company, mapped to the name shown on the page.
ALIAS = {'SK Hynix': 'SKHY', 'Mediatek': 'MediaTek', 'ESMT': 'ESMT (3006)', 'Sandisk': 'SNDK', 'SanDisk': 'SNDK', 'Micron': 'MU', 'Nvidia': 'NVDA'}
STANCES = ('bullish', 'bearish', 'neutral')
# Every dash-like character the page must not show: figure, en, em, horizontal bar,
# two-em, three-em, small em, and the vertical presentation forms.
DASHES = ('\u2012', '\u2013', '\u2014', '\u2015', '\u2e3a', '\u2e3b', '\ufe58', '\ufe31', '\ufe32')
# Fields every scraped post must have (as strings) before it is merged.
POST_KEYS = ('id', 'link', 'author', 'time', 'text', 'social', 'quoted')
