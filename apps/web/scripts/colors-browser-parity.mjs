// Compare browser MediaPipe on the exact PNG frames prepared by the local Python harness.
import { chromium } from '@playwright/test';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const project = resolve('../..');
const directory = resolve(project, process.argv[2] ?? 'ml/data/colors_v1/parity_phase3');
const packageDir = resolve('node_modules/@mediapipe/tasks-vision');
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.route('**/__parity/**', async (route) => {
    const path = new URL(route.request().url()).pathname.replace('/__parity/', '');
    let file;
    if (/^frame-\d\d\.png$/.test(path)) file = resolve(directory, path);
    else if (path === 'model.task') file = resolve(project, 'ml/assets/mediapipe/holistic_landmarker.task');
    else if (/^wasm\/[a-zA-Z0-9_.-]+$/.test(path)) file = resolve(packageDir, path);
    else return route.abort();
    return route.fulfill({ path: file });
  });
  await page.goto('http://127.0.0.1:5173/');
  const frames = await page.evaluate(async () => {
    const vision = await import('/node_modules/@mediapipe/tasks-vision/vision_bundle.mjs');
    const files = await vision.FilesetResolver.forVisionTasks('/__parity/wasm');
    const detector = await vision.HolisticLandmarker.createFromOptions(files, {
      baseOptions: { modelAssetPath: '/__parity/model.task', delegate: 'CPU' },
      runningMode: 'VIDEO', minFaceDetectionConfidence: .5,
      minPoseDetectionConfidence: .5, minHandLandmarksConfidence: .5,
    });
    const results = [];
    for (let i = 0; i < 12; i += 1) {
      const image = new globalThis.Image();
      image.src = `/__parity/frame-${String(i).padStart(2, '0')}.png`;
      await image.decode();
      const result = detector.detectForVideo(image, i * 50);
      const group = (points) => (points?.[0] ?? []).map((p) => [p.x, p.y, p.z]);
      results.push({ pose: group(result.poseLandmarks), leftHand: group(result.leftHandLandmarks),
        rightHand: group(result.rightHandLandmarks), timestampMs: i * 50 });
    }
    detector.close();
    return results;
  });
  await writeFile(resolve(directory, 'browser.json'), JSON.stringify(frames), { mode: 0o600, flag: 'wx' });
  const python = JSON.parse(await readFile(resolve(directory, 'python.json'), 'utf8'));
  const errors = [], counts = {};
  for (let i = 0; i < frames.length; i += 1) {
    for (const group of ['pose', 'leftHand', 'rightHand']) {
      const a = python[i][group], b = frames[i][group];
      counts[group] ??= { both: 0, python_only: 0, browser_only: 0 };
      if (a.length && b.length) {
        counts[group].both += 1;
        if (a.length !== b.length) throw new Error(`landmark count mismatch: ${group}`);
        for (let j = 0; j < a.length; j += 1) for (let k = 0; k < 3; k += 1) errors.push(Math.abs(a[j][k] - b[j][k]));
      } else if (a.length) counts[group].python_only += 1;
      else if (b.length) counts[group].browser_only += 1;
    }
  }
  errors.sort((a, b) => a - b);
  const summary = { scope: 'same 12 PNG frames from one video, fixed timestamps; raw detector coordinates',
    counts, coordinate_count: errors.length, mean_abs_difference: errors.reduce((a, b) => a + b, 0) / errors.length,
    p95_abs_difference: errors[Math.floor(errors.length * .95)], max_abs_difference: errors.at(-1) };
  await writeFile(resolve(directory, 'summary.json'), JSON.stringify(summary, null, 2), { mode: 0o600, flag: 'wx' });
  process.stdout.write(`${JSON.stringify(summary)}\n`);
} finally { await browser.close(); }
