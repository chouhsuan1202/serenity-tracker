// Compare two builds of the page view by view: visible text and full-page screenshots.
// Usage: node tests/compare_pages.js old.html new.html [--text-only]
// Prints one line per view and exits 1 if anything differs. Used to show a refactor changed nothing on screen.
const { chromium } = require('playwright');
const path = require('path');

const [a, b] = process.argv.slice(2).filter(x => !x.startsWith('--'));
const textOnly = process.argv.includes('--text-only');
const CLOCKS = ['2026-09-09T12:00:00Z', '2026-11-02T12:00:00Z']; // a day with data, and a later day when the data is old
const TZ = 'Asia/Taipei';

async function views(browser, file, now, width) {
  const page = await browser.newPage({ viewport: { width, height: 900 }, timezoneId: TZ });
  await page.addInitScript(t => { Date.now = () => t; }, new Date(now).getTime());
  await page.goto('file://' + path.resolve(file));
  // the build time differs between any two builds; blank it so only real differences show
  await page.evaluate(() => { const f = document.querySelector('.footer'); f.textContent = f.textContent.replace(/更新 .+? UTC/, '更新 (build time) UTC'); });
  const out = [];
  const snap = async name => out.push({
    name,
    text: await page.evaluate(() => document.body.innerText),
    png: textOnly ? null : await page.screenshot({ fullPage: true }),
  });
  for (const d of ['1', '7', '28', '0']) {
    await page.click(`#tabs button[data-d="${d}"]`);
    await snap(`tab ${d}`);
    if (await page.locator('#moreBtn').isVisible()) { await page.click('#moreBtn'); await snap(`tab ${d} all tickers`); }
    if (await page.locator('#otherSec > summary').isVisible()) { await page.click('#otherSec > summary'); await page.waitForTimeout(200); await snap(`tab ${d} other posts open`); await page.click('#otherSec > summary'); }
  }
  const syms = await page.$$eval('.tkrow', els => els.slice(0, 5).map(e => e.dataset.t));
  for (const s of syms) {
    await page.click(`.tkrow[data-t="${s}"]`);
    await snap(`stock ${s}`);
    await page.click('#backBtn');
  }
  await page.close();
  return out;
}

(async () => {
  const browser = await chromium.launch();
  let diffs = 0, total = 0;
  for (const now of CLOCKS) for (const width of [375, 1280]) {
    const [va, vb] = [await views(browser, a, now, width), await views(browser, b, now, width)];
    if (va.length !== vb.length) { console.log('DIFF', now, width, 'number of views', va.length, vb.length); diffs++; continue; }
    va.forEach((x, i) => {
      total++;
      const y = vb[i];
      const sameText = x.name === y.name && x.text === y.text;
      const samePng = textOnly || x.png.equals(y.png);
      if (!sameText || !samePng) diffs++;
      console.log(sameText && samePng ? 'same' : 'DIFF', now.slice(0, 10), width + 'px', x.name,
        sameText ? '' : '(text differs)', samePng ? '' : '(pixels differ)');
    });
  }
  await browser.close();
  console.log(`${total - diffs}/${total} views identical`);
  process.exit(diffs ? 1 : 0);
})();
