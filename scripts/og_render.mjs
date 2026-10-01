// צילום הכרטיסים של scripts/make_og.py ל-static/img/og/<key>.png (1200×630).
// דורש Playwright עם Chromium: npm i playwright (או PLAYWRIGHT / נתיב לדפדפן ב-CHROMIUM_PATH).
import { chromium } from 'playwright';
import { readFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const build = join(root, 'og-build');
const out = join(root, 'static', 'img', 'og');
mkdirSync(out, { recursive: true });
const keys = JSON.parse(readFileSync(join(build, 'keys.json'), 'utf8'));

const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const page = await browser.newPage({ viewport: { width: 1200, height: 800 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(join(build, 'cards.html')).href);
await page.evaluate(() => document.fonts.ready);
for (const key of keys) {
  await page.locator(`[id="${key}"]`).screenshot({ path: join(out, `${key}.png`) });
}

// אייקונים מתוך favicon.svg: ריבוע מלא בצבע הרקע (iOS מעגל פינות בעצמו)
const svg = readFileSync(join(root, 'static', 'img', 'favicon.svg'), 'utf8');
const icons = { 'apple-touch-icon.png': 180, 'favicon-48.png': 48 };
for (const [name, size] of Object.entries(icons)) {
  const p = await browser.newPage({ viewport: { width: size, height: size }, deviceScaleFactor: 1 });
  await p.setContent(`<body style="margin:0;background:#f4f2ec"><div style="width:${size}px;height:${size}px;display:flex;align-items:center;justify-content:center">${svg.replace('<svg ', `<svg width="${Math.round(size * .8)}" height="${Math.round(size * .8)}" `)}</div></body>`);
  await p.screenshot({ path: join(root, 'static', 'img', name) });
  await p.close();
}
await browser.close();
console.log(`${keys.length} images -> ${out}; icons: ${Object.keys(icons).join(', ')}`);
