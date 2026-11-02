"""Unit tests for the shared Python code in serenity/ and the pure parts of merge.py and brief.py."""
import datetime
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from serenity import claude_cli, page, text  # noqa: E402
from serenity.config import DASHES  # noqa: E402
from serenity.normalize import ticker_name  # noqa: E402
import brief  # noqa: E402
import merge  # noqa: E402

UTC = datetime.timezone.utc


class Text(unittest.TestCase):
    def test_parse_time(self):
        self.assertEqual(text.parse_time('2026-09-09T05:00:00.000Z'), datetime.datetime(2026, 9, 9, 5, tzinfo=UTC))
        self.assertEqual(text.parse_time('2026-09-09T05:00:00'), datetime.datetime(2026, 9, 9, 5, tzinfo=UTC), 'no zone means UTC')
        self.assertIsNone(text.parse_time('yesterday'))

    def test_utc_minute(self):
        tpe = datetime.timezone(datetime.timedelta(hours=8))
        self.assertEqual(text.utc_minute(datetime.datetime(2026, 9, 9, 13, 5, 59, tzinfo=tpe)), '2026-09-09 05:05')

    def test_nodash(self):
        self.assertEqual(text.nodash('a' + ''.join(DASHES) + 'b'), 'a' + '-' * len(DASHES) + 'b')
        self.assertIsNone(text.nodash(None))

    def test_ticker_name(self):
        self.assertEqual(ticker_name(' $Micron '), 'MU')
        self.assertEqual(ticker_name('$SIVE'), 'SIVE')


class Page(unittest.TestCase):
    def test_fill_is_single_pass(self):
        self.assertEqual(page.fill('A B', {'A': 'B', 'B': 'A'}), 'B A')

    def test_clean_brief(self):
        self.assertEqual(page.clean_brief({'7': ['a—b', 3], '28': 'not a list'}), {'7': ['a-b']})

    def test_js_json_escapes(self):
        s = page.js_json({'x': '</script>& '})
        self.assertNotIn('<', s); self.assertNotIn('&', s); self.assertNotIn(' ', s)


class Merge(unittest.TestCase):
    def p(self, i, time='2026-09-09T00:00:00Z'):
        return {'id': i, 'link': '', 'author': 'a', 'time': time, 'text': '', 'social': '', 'quoted': ''}

    def test_merge_keeps_old_adds_new_sorts(self):
        old = [dict(self.p('1'), text='old')]
        merged, added, bad = merge.merge(old, [dict(self.p('1'), text='new'), self.p('2', '2026-09-10T00:00:00Z'), {'id': '3'}])
        self.assertEqual([x['id'] for x in merged], ['2', '1'])
        self.assertEqual(merged[1]['text'], 'old', 'known posts are not overwritten')
        self.assertEqual((added, len(bad)), (1, 1))

    def test_valid(self):
        self.assertTrue(merge.valid(self.p('1')))
        self.assertFalse(merge.valid(self.p('')))
        self.assertFalse(merge.valid(dict(self.p('1'), time='')))
        self.assertFalse(merge.valid('x'))


class Brief(unittest.TestCase):
    def test_window_cut(self):
        now = datetime.datetime(2026, 9, 9, 12, tzinfo=UTC)
        data = [{'time': '2026-09-02T12:00:00Z', 'zh': 'edge', 'tickers': [{'t': 'MU', 'stance': 'bullish'}]},
                {'time': '2026-09-02T11:59:59Z', 'zh': 'old', 'tickers': []}]
        got = brief.window(data, 7, now)
        self.assertEqual([x['zh'] for x in got], ['edge'])
        self.assertEqual(got[0]['tickers'], [{'t': 'MU', 'stance': 'bullish', 'reason_zh': ''}])

    def test_check_points(self):
        self.assertEqual(brief.check_points({'points': ['a']}), ['a'])
        with self.assertRaises(AssertionError):
            brief.check_points({'points': []})


class ClaudeCli(unittest.TestCase):
    def test_matched_by_id_reorders(self):
        batch = [{'id': '1'}, {'id': '2'}]
        self.assertEqual(claude_cli.matched_by_id(batch)([{'id': 2, 'v': 'b'}, {'id': '1', 'v': 'a'}]),
                         [{'id': '1', 'v': 'a'}, {'id': 2, 'v': 'b'}])
        with self.assertRaises(AssertionError):
            claude_cli.matched_by_id(batch)([{'id': '1'}, {'id': '9'}])

    def test_run_batches_reports_failed_starts(self):
        seen = []
        failed = claude_cli.run_batches(list(range(5)), 2, lambda i, b, lock: seen.append(b) or i != 2)
        self.assertEqual(failed, [2])
        self.assertEqual(sorted(seen), [[0, 1], [2, 3], [4]])


if __name__ == '__main__':
    unittest.main()
