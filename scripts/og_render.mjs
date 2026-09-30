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
await browser.close();
console.log(`${keys.length} images -> ${out}`);
