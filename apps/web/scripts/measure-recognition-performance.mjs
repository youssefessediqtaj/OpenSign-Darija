import { webcrypto } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';

import { createServer } from 'vite';

globalThis.crypto ??= webcrypto;

const webRoot = fileURLToPath(new URL('..', import.meta.url));
const reportPath = fileURLToPath(
  new URL('../../../artifacts/reports/frontend-automatic-segmentation-benchmark.json', import.meta.url),
);
const vite = await createServer({
  root: webRoot,
  logLevel: 'error',
  appType: 'custom',
  server: { middlewareMode: true },
});

function syntheticFrame(frameIndex, timestampMs, kind = 'gesture-a', moving = true) {
  const shoulderLeft = { x: 0.4, y: 0.48, z: 0, visibility: 0.98 };
  const shoulderRight = { x: 0.6, y: 0.48, z: 0, visibility: 0.98 };
  const phase = moving ? Math.sin(frameIndex * 1.3) : 0;
  const gestureOffset = kind === 'gesture-a' ? -0.2 : kind === 'gesture-b' ? 0.16 : 0;
  const handY = kind === 'rest' ? 0.78 : kind === 'gesture-a' ? 0.36 : 0.5;
  const wristLeft = {
    x: 0.38 + gestureOffset + phase * (moving ? 0.09 : 0),
    y: handY,
    z: -0.02,
    visibility: 0.9,
  };
  const wristRight = {
    x: 0.62 - gestureOffset - phase * (moving ? 0.09 : 0),
    y: handY + (kind === 'gesture-b' ? -0.16 : 0),
    z: -0.02,
    visibility: 0.9,
  };
  const pose = Array.from({ length: 33 }, () => ({ x: 0, y: 0, z: 0, visibility: 0 }));
  pose[0] = { x: 0.5, y: 0.22, z: 0, visibility: 0.95 };
  pose[11] = shoulderLeft;
  pose[12] = shoulderRight;
  pose[13] = {
    x: (shoulderLeft.x + wristLeft.x) / 2,
    y: (shoulderLeft.y + wristLeft.y) / 2,
    z: 0,
    visibility: 0.9,
  };
  pose[14] = {
    x: (shoulderRight.x + wristRight.x) / 2,
    y: (shoulderRight.y + wristRight.y) / 2,
    z: 0,
    visibility: 0.9,
  };
  pose[15] = wristLeft;
  pose[16] = wristRight;
  const leftHand = Array.from({ length: 21 }, (_, index) => ({
    x: wristLeft.x + (index % 5) * 0.012,
    y: wristLeft.y + Math.floor(index / 5) * 0.014,
    z: 0,
    visibility: 0.92,
  }));
  const rightHand = Array.from({ length: 21 }, (_, index) => ({
    x: wristRight.x - (index % 5) * 0.012,
    y: wristRight.y + Math.floor(index / 5) * 0.014,
    z: 0,
    visibility: 0.92,
  }));
  const noHands = kind === 'no-hands';
  return {
    timestampMs,
    frameIndex,
    pose,
    face: [{ x: 0.5, y: 0.24, z: 0, visibility: 0.95 }],
    leftHand: noHands ? [] : leftHand,
    rightHand: noHands ? [] : rightHand,
    metadata: {
      videoWidth: 1280,
      videoHeight: 720,
      processingTimeMs: 18,
      faceDetected: true,
      leftHandDetected: !noHands,
      rightHandDetected: !noHands,
      poseDetected: true,
      averageLuminance: 140,
    },
  };
}

function automaticScenarioFrame(index, timestamp, detectorFps) {
  const elapsedSeconds = index / detectorFps;
  if (elapsedSeconds < 1.2) return syntheticFrame(index, timestamp, 'rest', false);
  if (elapsedSeconds < 2.2) return syntheticFrame(index, timestamp, 'gesture-a', true);
  if (elapsedSeconds < 3.1) return syntheticFrame(index, timestamp, 'gesture-a', false);
  if (elapsedSeconds < 4.6) return syntheticFrame(index, timestamp, 'rest', false);
  if (elapsedSeconds < 5.6) return syntheticFrame(index, timestamp, 'gesture-b', true);
  if (elapsedSeconds < 6.5) return syntheticFrame(index, timestamp, 'gesture-b', false);
  return syntheticFrame(index, timestamp, 'rest', false);
}

function percentile(values, percentileValue) {
  const sorted = [...values].sort((left, right) => left - right);
  const index = Math.min(sorted.length - 1, Math.ceil(sorted.length * percentileValue) - 1);
  return sorted[index] ?? 0;
}

try {
  const segmentationModule = await vite.ssrLoadModule(
    '/src/features/recognition/services/automatic-segmentation.service.ts',
  );
  const sequenceModule = await vite.ssrLoadModule(
    '/src/features/recognition/services/sequence-validator.service.ts',
  );
  const { AutomaticSignSegmenter, DEFAULT_SEGMENTATION_CONFIG } = segmentationModule;
  const {
    createLandmarkSequence,
    toWordLandmarkPayload,
    validateWordRecognitionPayloadV1,
  } = sequenceModule;
  const detectorFps = 20;
  const intervalMs = 1000 / detectorFps;

  const restSegmenter = new AutomaticSignSegmenter();
  const restEventCounts = { started: 0, completed: 0, rejected: 0, reset: 0 };
  const restStarted = performance.now();
  const restFrameCount = detectorFps * 60;
  for (let index = 0; index < restFrameCount; index += 1) {
    const event = restSegmenter.ingest(
      syntheticFrame(index, index * intervalMs, 'rest', false),
      'WAITING_FOR_SIGN',
    );
    if (event.type in restEventCounts) restEventCounts[event.type] += 1;
  }
  const restProcessingMs = performance.now() - restStarted;

  const loopSegmenter = new AutomaticSignSegmenter();
  let loopState = 'WAITING_FOR_SIGN';
  const segments = [];
  const startEvents = [];
  for (let index = 0; index < detectorFps * 8; index += 1) {
    const timestamp = index * intervalMs;
    const event = loopSegmenter.ingest(
      automaticScenarioFrame(index, timestamp, detectorFps),
      loopState,
    );
    if (event.type === 'started') {
      startEvents.push({ kind: event.kind, timestamp_ms: timestamp });
      loopState = 'CAPTURING';
    } else if (event.type === 'completed') {
      segments.push(event.segment);
      loopSegmenter.beginCooldown(timestamp);
      loopState = 'COOLDOWN';
    } else if (event.type === 'reset') {
      loopState = 'WAITING_FOR_SIGN';
    }
  }

  const heldSegmenter = new AutomaticSignSegmenter();
  let heldState = 'WAITING_FOR_SIGN';
  let initialHeldCompletions = 0;
  let duplicateHeldCompletions = 0;
  let heldIndex = 0;
  const feedHeld = (kind, moving, duplicatePhase = false) => {
    const timestamp = heldIndex * intervalMs;
    const event = heldSegmenter.ingest(
      syntheticFrame(heldIndex, timestamp, kind, moving),
      heldState,
    );
    heldIndex += 1;
    if (event.type === 'started') heldState = 'CAPTURING';
    if (event.type === 'completed') {
      if (duplicatePhase) duplicateHeldCompletions += 1;
      else initialHeldCompletions += 1;
      heldSegmenter.beginCooldown(timestamp);
      heldState = 'COOLDOWN';
    }
  };
  for (let count = 0; count < 12; count += 1) feedHeld('rest', false);
  for (let count = 0; count < 18; count += 1) feedHeld('gesture-a', true);
  for (let count = 0; count < 15; count += 1) feedHeld('gesture-a', false);
  for (let count = 0; count < detectorFps * 15; count += 1) {
    feedHeld('gesture-a', false, true);
  }

  if (segments.length !== 2) {
    throw new Error(`Expected two deterministic segments, received ${segments.length}`);
  }
  const payloadBuildTimes = [];
  let payload;
  let validation;
  for (let iteration = 0; iteration < 100; iteration += 1) {
    const buildStarted = performance.now();
    const segment = segments[0];
    const sequence = createLandmarkSequence(
      segment.sourceFrames,
      '2026-07-19T00:00:00.000Z',
    );
    payload = toWordLandmarkPayload(sequence, undefined, {
      kind: segment.kind,
      reliable: segment.reliable,
      usableFrameCount: segment.usableFrameCount,
    });
    validation = validateWordRecognitionPayloadV1(payload, {
      rawFrameCount: sequence.rawFrameCount,
      validFrameCount: sequence.validFrameCount,
    });
    payloadBuildTimes.push(performance.now() - buildStarted);
  }
  if (!validation?.valid) {
    throw new Error(`Generated payload failed validation: ${JSON.stringify(validation?.errors)}`);
  }

  const finiteCoordinates = payload.frames.every((frame) =>
    frame.landmarks.every(
      (landmark) => landmark.length === 3 && landmark.every(Number.isFinite),
    ),
  );
  const report = {
    generated_at: new Date().toISOString(),
    environment: {
      kind: 'deterministic_synthetic_landmarks',
      detector_cadence_fps: detectorFps,
      frame_interval_ms: Number(intervalMs.toFixed(3)),
      physical_camera: false,
    },
    configured_timing: {
      pre_roll_frames: DEFAULT_SEGMENTATION_CONFIG.preRollFrames,
      pre_roll_ms_at_configured_fps: Number(
        (DEFAULT_SEGMENTATION_CONFIG.preRollFrames * intervalMs).toFixed(3),
      ),
      dynamic_start_consecutive_frames: DEFAULT_SEGMENTATION_CONFIG.dynamicStartFrames,
      dynamic_start_observation_window_ms: Number(
        (DEFAULT_SEGMENTATION_CONFIG.dynamicStartFrames * intervalMs).toFixed(3),
      ),
      static_dwell_ms: DEFAULT_SEGMENTATION_CONFIG.staticDwellMs,
      end_stability_ms: DEFAULT_SEGMENTATION_CONFIG.endStableMs,
      post_roll_frames: DEFAULT_SEGMENTATION_CONFIG.postRollFrames,
      post_roll_ms_at_configured_fps: Number(
        (DEFAULT_SEGMENTATION_CONFIG.postRollFrames * intervalMs).toFixed(3),
      ),
      nominal_stable_end_to_finalize_ms: Number(
        (
          DEFAULT_SEGMENTATION_CONFIG.endStableMs +
          DEFAULT_SEGMENTATION_CONFIG.postRollFrames * intervalMs
        ).toFixed(3),
      ),
      minimum_duration_ms: DEFAULT_SEGMENTATION_CONFIG.minimumDurationMs,
      maximum_duration_ms: DEFAULT_SEGMENTATION_CONFIG.maximumDurationMs,
      cooldown_ms: DEFAULT_SEGMENTATION_CONFIG.cooldownMs,
      rest_reset_stability_ms: DEFAULT_SEGMENTATION_CONFIG.resetStableMs,
    },
    sixty_second_rest_simulation: {
      duration_ms: 60_000,
      input_frames: restFrameCount,
      event_counts: restEventCounts,
      api_submission_candidates: restEventCounts.completed,
      false_capture_count: restEventCounts.started,
      processing_ms: Number(restProcessingMs.toFixed(3)),
      processing_throughput_frames_per_second: Number(
        ((restFrameCount / restProcessingMs) * 1000).toFixed(1),
      ),
      passed: restEventCounts.started === 0 && restEventCounts.completed === 0,
    },
    two_sign_loop_simulation: {
      detected_start_events: startEvents,
      completed_segments: segments.length,
      kinds: segments.map((segment) => segment.kind),
      output_frame_counts: segments.map((segment) => segment.frames.length),
      final_state: loopState,
    },
    held_pose_duplicate_simulation: {
      held_after_first_result_ms: 15_000,
      initial_completion_count: initialHeldCompletions,
      duplicate_completion_count: duplicateHeldCompletions,
      final_state: heldState,
      passed: initialHeldCompletions === 1 && duplicateHeldCompletions === 0,
    },
    payload_build: {
      iterations: payloadBuildTimes.length,
      mean_ms: Number(
        (payloadBuildTimes.reduce((sum, value) => sum + value, 0) / payloadBuildTimes.length).toFixed(
          3,
        ),
      ),
      p95_ms: Number(percentile(payloadBuildTimes, 0.95).toFixed(3)),
      payload_bytes: Buffer.byteLength(JSON.stringify(payload)),
      frame_count: payload.frames.length,
      landmark_count: payload.frames[0]?.landmarks.length ?? 0,
      coordinate_count: payload.frames[0]?.landmarks[0]?.length ?? 0,
      finite_coordinates: finiteCoordinates,
      schema_valid: validation.valid,
    },
    physical_camera_only_metrics_remaining: [
      'Real MediaPipe detector FPS and dropped-frame rate on each target device.',
      'GPU/CPU landmark extraction latency and thermal throttling.',
      'False-start and missed-boundary rates across real users, clothing, lighting, distance, and backgrounds.',
      'Threshold precision/recall tuning on representative physical-camera sign/rest recordings.',
      'Camera permission-to-ready latency.',
      'Physical camera-to-Arabic end-to-end latency.',
      'Text-display-to-audible-playback latency and browser autoplay behavior.',
      'Long-session memory, battery, and device temperature behavior.',
    ],
    limitation:
      'Synthetic landmarks verify deterministic control flow and computational overhead; they do not establish physical-camera accuracy or production sign-recognition quality.',
  };

  await mkdir(dirname(reportPath), { recursive: true });
  await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify({ report: reportPath, summary: report }, null, 2));
} finally {
  await vite.close();
}
