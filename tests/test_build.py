import json, os, pathlib, shutil, subprocess, sys, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402


def post(**kw):
    p = {'id': '1', 'link': 'https://x.com/aleabitoreddit/status/1', 'author': 'aleabitoreddit',
         'time': '2026-09-09T05:00:00.000Z', 'text': 'hi', 'social': '', 'quoted': '', 'zh': '嗨',
         'quoted_zh': '', 'theme': '', 'theme_zh': '', 'paywalled': False, 'tickers': []}
    p.update(kw)
    return p


class Normalize(unittest.TestCase):
    def test_alias_dedupe_and_dollar(self):
        out = build.normalize([post(tickers=[{'t': '$Micron', 'stance': 'bullish'}, {'t': 'MU', 'stance': 'bearish'}])])
        self.assertEqual([(k['t'], k['stance']) for k in out[0]['tickers']], [('MU', 'bullish')])

    def test_unknown_stance_becomes_neutral(self):
        out = build.normalize([post(tickers=[{'t': 'NVDA', 'stance': 'mixed'}])])
        self.assertEqual(out[0]['tickers'][0]['stance'], 'neutral')

    def test_bad_time_and_bad_ticker_dropped(self):
        out = build.normalize([post(id='a', time=''), post(id='b', tickers=[{'t': None}, 'x', {'t': '$'}])])
        self.assertEqual([p['id'] for p in out], ['b'])
        self.assertEqual(out[0]['tickers'], [])

    def test_non_x_link_removed(self):
        out = build.normalize([post(link='javascript:alert(1)')])
        self.assertEqual(out[0]['link'], '')

    def test_dashes_replaced(self):
        out = build.normalize([post(zh='a\u2014b\u2013c')])
        self.assertEqual(out[0]['zh'], 'a-b-c')

    def test_sorted_newest_first(self):
        out = build.normalize([post(id='old', time='2026-01-01T00:00:00Z'), post(id='new', time='2026-02-01T00:00:00Z')])
        self.assertEqual([p['id'] for p in out], ['new', 'old'])


class Render(unittest.TestCase):
    def test_script_breakout_escaped(self):
        evil = '</script><script>alert(1)</script><!--'
        html = build.render(build.normalize([post(text=evil, zh=evil)]), {'7': [evil]}, 'x')
        script = html.split('<script>', 1)[1].rsplit('</script>', 1)[0]
        self.assertNotIn('</script', script.lower())
        self.assertNotIn('<!--', script)
        data = json.loads(script.split('const DATA=', 1)[1].split(';\nconst BRIEF=', 1)[0])
        self.assertEqual(data[0]['text'], evil)  # content preserved exactly

    def test_no_em_dash_in_output(self):
        html = build.render(build.normalize([post(text='x\u2014y')]), {'7': ['a\u2014b']}, 'x')
        self.assertNotIn('\u2014', html)

    def test_placeholder_text_in_post_left_alone(self):
        html = build.render(build.normalize([post(text='__BRIEF__ __LATEST__')]), {'7': ['b']}, 'x')
        self.assertIn('"text": "__BRIEF__ __LATEST__"', html)

    def test_all_dash_variants_replaced(self):
        out = build.normalize([post(zh=''.join(build.DASHES))])
        self.assertEqual(out[0]['zh'], '-' * len(build.DASHES))

    def test_main_refuses_empty(self):
        with tempfile.TemporaryDirectory() as d:
            src = pathlib.Path(d, 'c.json'); src.write_text('[]')
            with self.assertRaises(SystemExit):
                build.main(str(src), str(pathlib.Path(d, 'b.json')), str(pathlib.Path(d, 'i.html')))
            self.assertFalse(pathlib.Path(d, 'i.html').exists())


class Pipeline(unittest.TestCase):
    """Run the scripts in a temp dir with a fake `claude` CLI, check failures are loud."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(self.dir, 'data'))
        self.bin = os.path.join(self.dir, 'bin'); os.mkdir(self.bin)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def fake_claude(self, stdout):
        f = pathlib.Path(self.bin, 'claude')
        f.write_text('#!/bin/sh\ncat <<\'EOF\'\n' + stdout + '\nEOF\n'); f.chmod(0o755)

    def run_script(self, name):
        env = {**os.environ, 'PATH': self.bin + os.pathsep + os.environ['PATH']}
        return subprocess.run([sys.executable, str(ROOT / name), 'x'], cwd=self.dir, env=env,
                              capture_output=True, text=True, timeout=60)

    def write(self, rel, obj):
        pathlib.Path(self.dir, rel).write_text(json.dumps(obj))

    def read(self, rel):
        return json.loads(pathlib.Path(self.dir, rel).read_text())

    def test_merge_skips_malformed(self):
        self.write('data/tweets_raw.json', [post(id='1')])
        good = {k: post(id='2')[k] for k in ('id', 'link', 'author', 'time', 'text', 'social', 'quoted')}
        self.write('data/incoming.json', [good, {'id': '3'}])
        r = self.run_script('merge.py')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(x['id'] for x in self.read('data/tweets_raw.json')), ['1', '2'])
        self.assertIn('skipped 1', r.stderr)

    def test_classify_wrong_ids_fails_loudly(self):
        self.write('data/tweets_raw.json', [post(id='1')])
        self.fake_claude('[{"id":"999","tickers":[],"theme":""}]')
        r = self.run_script('classify.py')
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(pathlib.Path(self.dir, 'data/classified.json').exists())

    def test_classify_reordered_answer_matched_by_id(self):
        self.write('data/tweets_raw.json', [post(id='1', text='a'), post(id='2', text='b')])
        self.fake_claude('[{"id":"2","tickers":[{"t":"MU","stance":"bullish","reason":"r"}],"theme":""},'
                         '{"id":"1","tickers":[],"theme":""}]')
        r = self.run_script('classify.py')
        self.assertEqual(r.returncode, 0, r.stderr)
        got = {x['id']: x['tickers'] for x in self.read('data/classified.json')}
        self.assertEqual(got['1'], []); self.assertEqual(got['2'][0]['t'], 'MU')

    def test_translate_failure_exits_nonzero(self):
        p = post(); del p['zh']
        self.write('data/classified.json', [p])
        self.fake_claude('not json')
        r = self.run_script('translate.py')
        self.assertNotEqual(r.returncode, 0)

    def test_brief_failure_keeps_old_summary(self):
        recent = post(time=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat())
        self.write('data/classified.json', [recent])
        self.write('data/brief.json', {'7': ['舊的'], '28': ['舊的28']})
        self.fake_claude('garbage')
        r = self.run_script('brief.py')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.read('data/brief.json'), {'7': ['舊的'], '28': ['舊的28']})


if __name__ == '__main__':
    unittest.main()
