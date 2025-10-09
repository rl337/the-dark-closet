'use strict';

const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

function ensureDirSync(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

function loadJson(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  return JSON.parse(content);
}

function resolveAsset(assetRoot, rel) {
  return path.isAbsolute(rel) ? rel : path.join(assetRoot, rel);
}

async function createPlaceholderPng(targetPath, width, height, label) {
  const bg = { r: 0, g: 0, b: 0, alpha: 0 };
  const svg = `<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"><rect width="100%" height="100%" fill="rgba(0,0,0,0)"/><rect x="2" y="2" width="${width-4}" height="${height-4}" fill="#444" fill-opacity="0.25" stroke="#999" stroke-width="2"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="monospace" font-size="14" fill="#ffffff" fill-opacity="0.85">${label}</text></svg>`;
  const png = await sharp({ create: { width, height, channels: 4, background: bg } })
    .composite([{ input: Buffer.from(svg) }])
    .png()
    .toBuffer();
  await fs.promises.writeFile(targetPath, png);
}

async function ensureAssets(config) {
  const { assetsRoot, canvas, parts } = config;
  const promises = Object.entries(parts).map(async ([key, relPath]) => {
    const abs = resolveAsset(assetsRoot, relPath);
    ensureDirSync(path.dirname(abs));
    if (!fs.existsSync(abs)) {
      await createPlaceholderPng(abs, canvas.width, canvas.height, key);
    }
  });
  await Promise.all(promises);
}

function applyTransform(image, transform) {
  if (!transform) return image;
  const { dx = 0, dy = 0 } = transform;
  return { input: image, left: dx, top: dy }; // sharp composite option
}

async function composeFrame(config, frameIndex, frameDef) {
  const { canvas, assetsRoot, outputRoot, parts, layerOrder } = config;
  ensureDirSync(outputRoot);
  const base = sharp({ create: { width: canvas.width, height: canvas.height, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } });

  const faceEyesKey = frameDef.face && frameDef.face.eyes ? frameDef.face.eyes : 'eyes_open';
  const faceMouthKey = frameDef.face && frameDef.face.mouth ? frameDef.face.mouth : 'mouth_neutral';

  const composites = [];
  for (const layer of layerOrder) {
    let partKey = layer;
    if (layer === 'eyes') partKey = faceEyesKey;
    if (layer === 'mouth') partKey = faceMouthKey;
    const rel = parts[partKey];
    if (!rel) continue;
    const abs = resolveAsset(assetsRoot, rel);
    const buff = await fs.promises.readFile(abs);
    const transform = frameDef.transforms && frameDef.transforms[layer] ? frameDef.transforms[layer] : frameDef.transforms && frameDef.transforms[partKey];
    composites.push({ input: buff, left: (transform && transform.dx) || 0, top: (transform && transform.dy) || 0 });
  }

  const outFile = path.join(outputRoot, `frame_${String(frameIndex).padStart(3, '0')}.png`);
  await base.composite(composites).png().toFile(outFile);
  return outFile;
}

async function generateForAnimation(config, animationName) {
  const anim = config.animations[animationName];
  if (!anim) throw new Error(`Animation not found: ${animationName}`);
  const frames = anim.frames || [];
  const outputs = [];
  for (let i = 0; i < frames.length; i++) {
    const frameOut = await composeFrame(config, i, frames[i]);
    outputs.push(frameOut);
  }
  return outputs;
}

async function main() {
  const configPath = process.argv[2] || path.join(__dirname, '..', 'config', 'dark_weirdo.json');
  const config = loadJson(configPath);

  ensureDirSync(config.assetsRoot);
  ensureDirSync(config.outputRoot);

  await ensureAssets(config);

  const anim = process.argv[3] || 'idle';
  const outputs = await generateForAnimation(config, anim);
  console.log(`Generated ${outputs.length} frames for animation "${anim}" at ${config.outputRoot}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

