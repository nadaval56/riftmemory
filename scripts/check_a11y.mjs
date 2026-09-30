// בדיקת נגישות ופרטיות בדפדפן אמיתי (Playwright + axe-core).
//
// הרצה (אחרי build_site.py, עם שרת מקומי שמגיש את site/ תחת /riftmemory/):
//   npm i --no-save axe-core playwright
//   BASE=http://localhost:8765/riftmemory node scripts/check_a11y.mjs
//
// מה נבדק, בכל דף:
//   1. axe-core, כללי WCAG 2.0/2.1 ברמות A ו-AA, בארבעה מצבי תצוגה:
//      בהיר, כהה, ניגודיות גבוהה, ניגודיות הפוכה.
//   2. גלישה אופקית ברוחב 320px, בגודל הטקסט הגדול ועם ריווח מוגדל (1.4.10, 1.4.12).
//   3. שגודל הטקסט "גדול" באמת מגדיל את גוף הטקסט (מידות ב-rem ולא ב-px).
//   4. תפריט הנגישות: נפתח ב-Alt+Shift+A, המיקוד בתוכו, Esc סוגר.
//   5. פרטיות: שום בקשה לא יוצאת לדומיין אחר מדומיין האתר.
// יציאה בקוד 1 אם נמצאה בעיה.

import { chromium } from 'playwright';
import { createRequire } from 'module';
import fs from 'fs';

const require = createRequire(import.meta.url);
const BASE = (process.env.BASE || 'http://localhost:8765/riftmemory').replace(/\/$/, '');
const AXE = fs.readFileSync(process.env.AXE || require.resolve('axe-core/axe.min.js'), 'utf8');
const PAGES = ['/', '/events/1927-dead-sea/', '/events/1837-safed/', '/events/0749-shviit/', '/recent/',
               '/instruments/', '/timeline/', '/about/', '/people/', '/what-is-an-earthquake/', '/privacy/', '/accessibility/', '/404.html'];
const MODES = [
  { name: 'בהיר', theme: 'light' },
  { name: 'כהה', theme: 'dark' },
  { name: 'ניגודיות גבוהה', a11y: { mode: 'contrast' } },
  { name: 'ניגודיות הפוכה', a11y: { mode: 'invert' } },
];

const host = new URL(BASE).host;
let problems = 0;
const fail = (msg) => { problems++; console.log('כשל: ' + msg); };

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined });

async function openPage(path, { width = 1280, theme, a11y, ack = true } = {}) {
  const ctx = await browser.newContext({ viewport: { width, height: 900 }, locale: 'he-IL' });
  await ctx.addInitScript(({ theme, a11y, ack }) => {
    if (ack) localStorage.setItem('privacy:v1', JSON.stringify({ ack: true, local: true }));
    if (theme) localStorage.setItem('riftmemory.theme', theme);
    if (a11y) localStorage.setItem('a11y:v1', JSON.stringify(Object.assign({ fs: 's', mode: '' }, a11y)));
  }, { theme, a11y, ack });
  const page = await ctx.newPage();
  const foreign = new Set();
  page.on('request', (r) => { const h = new URL(r.url()).host; if (h && h !== host) foreign.add(h); });
  await page.goto(BASE + path, { waitUntil: 'networkidle' });
  await page.waitForTimeout(300);
  return { ctx, page, foreign };
}

for (const path of PAGES) {
  // 1. axe בכל מצב
  for (const m of MODES) {
    const { ctx, page, foreign } = await openPage(path, m);
    await page.addScriptTag({ content: AXE });
    const res = await page.evaluate(async () => {
      // eslint-disable-next-line no-undef
      const r = await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } });
      return r.violations.map((v) => ({ id: v.id, impact: v.impact, n: v.nodes.length,
        sample: v.nodes.slice(0, 3).map((x) => x.target.join(' ') + (x.any[0] ? ' — ' + x.any[0].message : '')) }));
    });
    for (const v of res) fail(`${path} [${m.name}] ${v.id} (${v.impact}, ${v.n}): ${v.sample.join(' | ')}`);
    if (foreign.size) fail(`${path} [${m.name}] בקשות לדומיינים אחרים: ${[...foreign].join(', ')}`);
    await ctx.close();
  }

  // 2. גלישה אופקית ב-320px, טקסט גדול + ריווח
  {
    const { ctx, page } = await openPage(path, { width: 320, a11y: { fs: 'l', spacing: 1 } });
    const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    if (over > 1) fail(`${path} גלישה אופקית של ${over}px ברוחב 320 עם טקסט גדול וריווח`);
    await ctx.close();
  }

  // 3. הגדלת טקסט אמיתית
  {
    const sizes = [];
    for (const fs_ of ['s', 'l']) {
      const { ctx, page } = await openPage(path, { a11y: { fs: fs_ } });
      sizes.push(await page.evaluate(() => parseFloat(getComputedStyle(document.body).fontSize)));
      await ctx.close();
    }
    if (!(sizes[1] >= sizes[0] * 1.2)) fail(`${path} גודל טקסט "גדול" לא מגדיל את גוף הטקסט (${sizes.join(' → ')})`);
  }
}

// 4. תפריט הנגישות והודעת הפרטיות (בדף הבית)
{
  const { ctx, page } = await openPage('/', { ack: false });
  if (!(await page.locator('.consent').isVisible())) fail('הודעת הפרטיות לא מוצגת בכניסה ראשונה');
  await page.locator('.consent-ok').click();
  if (await page.locator('.consent').count()) fail('הודעת הפרטיות לא נסגרה');
  await page.keyboard.press('Alt+Shift+KeyA');
  const open = await page.locator('#a11y-panel').isVisible();
  const inside = await page.evaluate(() => document.getElementById('a11y-panel').contains(document.activeElement));
  if (!open || !inside) fail('תפריט הנגישות לא נפתח במקלדת, או שהמיקוד לא עבר אליו');
  await page.keyboard.press('Escape');
  if (await page.locator('#a11y-panel').isVisible()) fail('Esc לא סוגר את תפריט הנגישות');
  // קישור דילוג: התחנה הראשונה ב-Tab
  await page.goto(BASE + '/', { waitUntil: 'networkidle' });
  await page.keyboard.press('Tab');
  const first = await page.evaluate(() => document.activeElement && document.activeElement.className);
  if (first !== 'skip-link') fail(`התחנה הראשונה ב-Tab היא "${first}" ולא קישור הדילוג`);
  await ctx.close();
}

await browser.close();
console.log(`${problems} בעיות`);
process.exit(problems ? 1 : 0);
