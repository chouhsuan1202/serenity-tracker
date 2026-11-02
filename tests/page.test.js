// Browser tests for index.html: counts vs independent Python, XSS, layout at 375px / 1280px, console errors.
// Run: python3 build.py && node tests/page.test.js
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), os = require('os'), assert = require('assert');
const ROOT = path.resolve(__dirname, '..');
const NOW = '2026-09-09T12:00:00Z', TZ = 'Asia/Taipei';
let failures = 0;
async function test(name, fn) {
  try { await fn(); console.log('ok  ', name); } catch (e) { failures++; console.log('FAIL', name, '\n  ', e.message); }
}
async function open(browser, file, width, errors) {
  const page = await browser.newPage({ viewport: { width, height: 800 }, timezoneId: TZ });
  page.on('console', m => m.type() === 'error' && errors.push(m.text()));
  page.on('pageerror', e => errors.push(String(e)));
  page.on('dialog', d => { errors.push('dialog: ' + d.message()); d.dismiss(); });
  await page.addInitScript(t => { Date.now = () => t; }, new Date(NOW).getTime());
  await page.goto('file://' + file);
  return page;
}
const noHScroll = page => page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth);

(async () => {
  const browser = await chromium.launch();
  const expected = JSON.parse(execFileSync('python3', [path.join(__dirname, 'expected.py'), NOW, TZ], { encoding: 'utf8' }));
  const real = path.join(ROOT, 'index.html');

  await test('tab counts and per-stock counts match independent calculation', async () => {
    const errors = [], page = await open(browser, real, 1280, errors);
    for (const d of ['1', '7', '28', '0']) {
      const btn = page.locator(`#tabs button[data-d="${d}"]`);
      assert.match(await btn.textContent(), new RegExp(` · ${expected[d].posts}$`), `tab ${d}`);
      await btn.click();
      if (await page.locator('#moreBtn').isVisible()) await page.click('#moreBtn');
      const rows = await page.$$eval('.tkrow', els => els.map(e => ({ t: e.dataset.t, n: +e.querySelector('.l1 .mute').textContent.match(/\d+/)[0] })));
      const exp = expected[d].tickers;
      assert.strictEqual(rows.length, Object.keys(exp).length, `ticker count, tab ${d}`);
      for (const r of rows) assert.strictEqual(r.n, exp[r.t].n, `${r.t} mentions, tab ${d}`);
      assert.strictEqual(await page.locator('#tl .post').count(), expected[d].with_tickers, `posts with tickers, tab ${d}`);
    }
    // stock page uses all-time counts
    const all = expected['0'].tickers;
    const top = Object.entries(all).sort((a, b) => b[1].n - a[1].n)[0];
    await page.click(`.tkrow[data-t="${top[0]}"]`);
    const c = top[1];
    assert.strictEqual(await page.textContent('#ssub'), `提到 ${c.n} 次，看多 ${c.bullish || 0}、看空 ${c.bearish || 0}、中立 ${c.neutral || 0}（全部時間）`);
    assert.deepStrictEqual(errors, []);
  });

  for (const width of [375, 1280]) {
    await test(`no horizontal scroll at ${width}px, all views, posts expanded`, async () => {
      const errors = [], page = await open(browser, real, width, errors);
      for (const d of ['1', '7', '28', '0']) {
        await page.click(`#tabs button[data-d="${d}"]`);
        await page.evaluate(() => { document.querySelectorAll('details').forEach(x => x.open = true); document.querySelectorAll('.clamp').forEach(x => x.classList.remove('clamp')); });
        assert.ok(await noHScroll(page), `tab ${d}`);
      }
      await page.click('#tabs button[data-d="0"]');
      await page.click('.tkrow');
      assert.ok(await noHScroll(page), 'stock page');
      assert.deepStrictEqual(errors, []);
    });
  }

  await test('hostile data is shown as text, not executed', async () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ser-'));
    const evil = '</script><img src=x onerror=alert(1)><script>alert(2)</script>';
    const longword = 'https://example.com/' + 'a'.repeat(400);
    const posts = [{ id: '1', link: 'javascript:alert(3)', author: 'a', time: '2026-09-09T05:00:00Z', text: evil + ' ' + longword,
      social: '', quoted: evil, zh: evil + longword, quoted_zh: evil, theme: '', theme_zh: '', paywalled: false,
      tickers: [{ t: '"><img src=x onerror=alert(4)>', stance: 'weird', reason: evil, reason_zh: evil }] }];
    fs.writeFileSync(path.join(tmp, 'c.json'), JSON.stringify(posts));
    fs.writeFileSync(path.join(tmp, 'b.json'), JSON.stringify({ 7: [evil] }));
    execFileSync('python3', ['-c', `import sys; sys.path.insert(0, ${JSON.stringify(ROOT)}); import build; build.main(*sys.argv[1:])`,
      path.join(tmp, 'c.json'), path.join(tmp, 'b.json'), path.join(tmp, 'i.html')], { stdio: 'pipe' });
    const errors = [], page = await open(browser, path.join(tmp, 'i.html'), 375, errors);
    assert.strictEqual(await page.locator('img').count(), 0, 'no injected <img>');
    assert.strictEqual(await page.locator('a[href^="javascript"]').count(), 0, 'no javascript: link');
    assert.ok((await page.textContent('#brief')).includes('<img src=x'), 'brief shown as text');
    assert.match(await page.textContent('.tkrow .l2 .tag'), /中立/, 'unknown stance shown as neutral');
    await page.click('.tkrow');
    assert.ok(await noHScroll(page), 'long unbroken text wraps');
    assert.deepStrictEqual(errors, []);
  });

  await test('"expand" works for long posts inside collapsed 其他貼文 section', async () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ser-'));
    const long = Array.from({ length: 20 }, (_, i) => '第 ' + i + ' 行').join('\n');
    const posts = [{ id: '1', link: 'https://x.com/a/status/1', author: 'a', time: '2026-09-09T05:00:00Z', text: long, social: '', quoted: '',
      zh: long, quoted_zh: '', theme: '', theme_zh: '', paywalled: false, tickers: [] }];
    fs.writeFileSync(path.join(tmp, 'c.json'), JSON.stringify(posts));
    execFileSync('python3', ['-c', `import sys; sys.path.insert(0, ${JSON.stringify(ROOT)}); import build; build.main(*sys.argv[1:])`,
      path.join(tmp, 'c.json'), path.join(tmp, 'none.json'), path.join(tmp, 'i.html')], { stdio: 'pipe' });
    const errors = [], page = await open(browser, path.join(tmp, 'i.html'), 375, errors);
    await page.click('#otherSec summary');
    const btn = page.locator('#otherSec .expand');
    assert.ok(await btn.isVisible(), 'expand button visible');
    await btn.click();
    assert.strictEqual(await page.locator('#otherSec .txt.clamp').count(), 0);
    assert.deepStrictEqual(errors, []);
  });

  await browser.close();
  if (failures) { console.log(failures + ' failed'); process.exit(1); }
  console.log('all passed');
})();
