// Renders docs/icons/favicon.svg into 1024x1024 sources for @capacitor/assets.
// Replace assets/*.png with a designer-made 1024px icon later if you like.
import sharp from "sharp";
import { mkdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const svg = readFileSync(join(here, "..", "..", "docs", "icons", "favicon.svg"));
const dir = join(here, "..", "assets");
mkdirSync(dir, { recursive: true });
const BG = "#15192a";
// Full-bleed icon: square, no rounded corners (stores apply their own mask).
const flat = Buffer.from(svg.toString().replace(/rx="14"/, 'rx="0"'));
await sharp(flat, { density: 1200 }).resize(1024, 1024).png().toFile(join(dir, "icon-only.png"));
// Adaptive-icon foreground: logo at ~62% in the Android safe zone, transparent around.
const fg = await sharp(svg, { density: 1200 }).resize(640, 640).png().toBuffer();
await sharp({ create: { width: 1024, height: 1024, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } })
  .composite([{ input: fg, gravity: "center" }]).png().toFile(join(dir, "icon-foreground.png"));
await sharp({ create: { width: 1024, height: 1024, channels: 4, background: BG } }).png().toFile(join(dir, "icon-background.png"));
// Splash: logo centered on the app background colour.
const sp = await sharp(svg, { density: 1200 }).resize(700, 700).png().toBuffer();
for (const name of ["splash.png", "splash-dark.png"])
  await sharp({ create: { width: 2732, height: 2732, channels: 4, background: BG } })
    .composite([{ input: sp, gravity: "center" }]).png().toFile(join(dir, name));
console.log("assets/ icon + splash sources written");
