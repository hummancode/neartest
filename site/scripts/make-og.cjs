// Renders scripts/og.html to public/og.png (1200x630). Optional helper, not run in CI.
// Usage (from site/): node scripts/make-og.cjs   — requires Playwright with Chromium.
const { chromium } = require("playwright");
const path = require("path");
(async () => {
  const brand = require("fs").readFileSync(path.join(__dirname, "../src/config.ts"), "utf8").match(/SITE_NAME = "([^"]*)"/)[1];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  await p.goto("file://" + path.join(__dirname, "og.html"));
  await p.evaluate((name) => (document.getElementById("brand").textContent = name), brand);
  await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: path.join(__dirname, "../public/og.png") });
  await b.close();
  console.log("public/og.png yazıldı");
})();
