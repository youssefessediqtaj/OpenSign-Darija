// Run the app's pure TypeScript sampling and normalization on captured browser detections.
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import ts from 'typescript';

const directory = resolve('../..', process.argv[2] ?? 'ml/data/colors_v1/parity_phase3');
async function loadTs(path) {
  const source = await readFile(path, 'utf8');
  const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText;
  return import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
}
const { normalizeSchemaV1Frame } = await loadTs('src/features/recognition/domain/normalize-landmarks.ts');
const { uniformSample } = await loadTs('src/features/recognition/domain/resample-landmark-sequence.ts');
const frames = JSON.parse(await readFile(resolve(directory, 'browser.json'), 'utf8'));
const toPoints = (group) => group.map(([x, y, z]) => ({ x, y, z }));
const valid = frames.filter((f) => f.pose.length > 12 && (f.leftHand.length || f.rightHand.length)).map((f) => ({
  pose: toPoints(f.pose), leftHand: toPoints(f.leftHand), rightHand: toPoints(f.rightHand),
  timestampMs: f.timestampMs,
}));
const tensor = uniformSample(valid, 60).map((f, i) => normalizeSchemaV1Frame(f, i));
await writeFile(resolve(directory, 'browser-tensor.json'), JSON.stringify({ valid_count: valid.length, tensor }), { mode: 0o600, flag: 'wx' });
process.stdout.write(`Browser transform: ${valid.length} valid frames -> ${tensor.length} frames\n`);
