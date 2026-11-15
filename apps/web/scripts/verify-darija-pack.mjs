// Fail the production build if the bundled voice pack differs from its approved manifest.
import { createHash } from 'node:crypto';
import { existsSync, lstatSync, readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';

const labels = new Set(['black', 'blue', 'brown', 'green', 'orange', 'pink', 'red', 'white', 'yellow']);
const pack = JSON.parse(readFileSync(resolve('src/features/recognition/domain/approved-voice-pack.json'), 'utf8'));
const dir = resolve('public/audio/darija/colors');
const assets = pack.assets;
if (pack.version !== '1' || !assets || typeof assets !== 'object' || Array.isArray(assets)) throw new Error('Invalid Darija pack manifest');
const files = existsSync(dir) ? readdirSync(dir) : [];
for (const file of files) {
  const label = file.endsWith('.wav') ? file.slice(0, -4) : '';
  if (!labels.has(label) || !Object.hasOwn(assets, label)) throw new Error(`Unapproved voice asset: ${file}`);
}
for (const [label, entry] of Object.entries(assets)) {
  if (!labels.has(label) || !entry || entry.approved !== true || typeof entry.expression !== 'string' || !entry.expression || typeof entry.version !== 'string' || !entry.version || !/^[a-f0-9]{64}$/.test(entry.sha256)) throw new Error(`Invalid approval: ${label}`);
  const file = resolve(dir, `${label}.wav`);
  if (!existsSync(file) || !lstatSync(file).isFile()) throw new Error(`Missing or unsafe approved voice asset: ${label}`);
  const digest = createHash('sha256').update(readFileSync(file)).digest('hex');
  if (digest !== entry.sha256) throw new Error(`Voice checksum mismatch: ${label}`);
}
console.log(`Darija voice pack verified: ${Object.keys(assets).length} approved assets`);
