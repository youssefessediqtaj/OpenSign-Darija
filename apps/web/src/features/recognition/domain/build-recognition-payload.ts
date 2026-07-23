import type { HolisticFrame } from './landmarks';
import type {
  LandmarkSequence,
  WordRecognitionPayloadValidationError,
  WordRecognitionPayloadValidationResult,
  WordLandmarkSequencePayload,
} from './recognition-contract';
import type { SegmentationKind } from '../state/recognition-flow';
import {
  normalizeSchemaV1Frame,
  OPEN_SIGNE_COORDINATE_COUNT,
  OPEN_SIGNE_COORDINATE_FORMAT,
  OPEN_SIGNE_LANDMARK_COUNT,
  OPEN_SIGNE_LANDMARK_SCHEMA_VERSION,
} from './normalize-landmarks';
import { uniformSample } from './resample-landmark-sequence';
import { calculateSequenceQuality } from './sequence-quality';

const WORD_TARGET_FRAME_COUNT = 60;
const MIN_VALID_WORD_FRAMES = 8;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function hasFinitePoint(point: { x?: number; y?: number; z?: number } | undefined): boolean {
  return Boolean(
    point &&
      Number.isFinite(point.x) &&
      Number.isFinite(point.y) &&
      Number.isFinite(point.z),
  );
}

function isValidWordSourceFrame(frame: HolisticFrame): boolean {
  return (
    frame.metadata.poseDetected &&
    (frame.metadata.leftHandDetected || frame.metadata.rightHandDetected) &&
    hasFinitePoint(frame.pose[11]) &&
    hasFinitePoint(frame.pose[12])
  );
}

export function wordValidationErrorMessage(error: WordRecognitionPayloadValidationError): string {
  switch (error.code) {
    case 'detector_not_ready':
      return 'Attendez que le moteur de detection soit pret.';
    case 'insufficient_valid_frames':
      return `Capture insuffisante : seulement ${error.received} images valides sur le minimum requis.`;
    case 'invalid_frame_count':
      return 'La sequence doit contenir exactement 60 images.';
    case 'invalid_landmark_count':
      return 'Chaque image doit contenir exactement 75 landmarks.';
    case 'invalid_coordinate_count':
      return 'Chaque landmark doit contenir exactement trois coordonnees.';
    case 'invalid_segmentation_kind':
      return 'Le type de segmentation automatique est invalide.';
    case 'unreliable_segmentation':
      return 'Les limites du signe ne sont pas assez fiables.';
    case 'invalid_usable_frame_count':
      return 'La sequence ne contient pas assez d’images utilisables.';
    case 'non_finite_coordinate':
      return 'Les coordonnees invalides ont ete rejetees avant envoi.';
    case 'invalid_presence_mask':
      return 'Le masque de presence doit contenir 75 valeurs 0 ou 1.';
    case 'invalid_timestamp':
    case 'non_monotonic_timestamp':
      return 'Les horodatages de capture sont invalides.';
    case 'invalid_source_fps':
      return 'La cadence de capture est invalide.';
    case 'invalid_duration':
      return 'La sequence est trop courte ou trop longue.';
    default:
      return 'La sequence capturee ne respecte pas le format attendu.';
  }
}

function pushError(
  errors: WordRecognitionPayloadValidationError[],
  error: WordRecognitionPayloadValidationError,
): void {
  errors.push(error);
}

export function createLandmarkSequence(frames: HolisticFrame[], startedAt: string): LandmarkSequence {
  const first = frames[0];
  const last = frames[frames.length - 1];
  const durationMs = first && last ? Math.max(last.timestampMs - first.timestampMs, 0) : 0;
  const sourceFps = durationMs > 0 ? Number(((frames.length / durationMs) * 1000).toFixed(1)) : 0;
  const quality = calculateSequenceQuality(frames, durationMs);
  return {
    id: crypto.randomUUID(),
    startedAt,
    durationMs,
    sourceFps,
    frames,
    rawFrameCount: frames.length,
    validFrameCount: frames.filter(isValidWordSourceFrame).length,
    quality,
  };
}

export function toWordLandmarkPayload(
  sequence: LandmarkSequence,
  segmentation: {
    kind: SegmentationKind;
    reliable: boolean;
    usableFrameCount: number;
  },
): WordLandmarkSequencePayload {
  return finalizeWordRecognitionPayloadV1(sequence, segmentation);
}

export function finalizeWordRecognitionPayloadV1(
  sequence: LandmarkSequence,
  segmentation: {
    kind: SegmentationKind;
    reliable: boolean;
    usableFrameCount: number;
  },
): WordLandmarkSequencePayload {
  const validFrames = sequence.frames.filter(isValidWordSourceFrame);
  const sampled = uniformSample(validFrames, WORD_TARGET_FRAME_COUNT);
  const outputDurationMs = Math.max(
    WORD_TARGET_FRAME_COUNT - 1,
    Math.min(10_000, Math.round(sequence.durationMs)),
  );
  return {
    sequence_id: sequence.id,
    captured_at: sequence.startedAt,
    recognition_mode: 'WORD_ISOLATED',
    duration_ms: Math.round(sequence.durationMs),
    source_fps: sequence.sourceFps,
    target_frame_count: WORD_TARGET_FRAME_COUNT,
    landmark_count: OPEN_SIGNE_LANDMARK_COUNT,
    coordinate_count: OPEN_SIGNE_COORDINATE_COUNT,
    coordinate_format: OPEN_SIGNE_COORDINATE_FORMAT,
    feature_schema_version: OPEN_SIGNE_LANDMARK_SCHEMA_VERSION,
    segmentation_kind: segmentation.kind,
    segmentation_reliable: segmentation.reliable,
    usable_frame_count: segmentation.usableFrameCount,
    frames: sampled.map((frame, index) =>
      normalizeSchemaV1Frame(
        frame,
        index,
        Math.round((index * outputDurationMs) / (WORD_TARGET_FRAME_COUNT - 1)),
      ),
    ),
    quality: {
      detected_hand_ratio: sequence.quality.detectedHandRatio,
      detected_face_ratio: sequence.quality.detectedFaceRatio,
      detected_pose_ratio: sequence.quality.detectedPoseRatio,
      missing_frame_ratio: sequence.quality.missingFrameRatio,
      movement_score: sequence.quality.movementScore,
    },
  };
}

export function validateWordLandmarkPayload(payload: WordLandmarkSequencePayload): string[] {
  return validateWordRecognitionPayloadV1(payload).errors.map(wordValidationErrorMessage);
}

export function validateWordRecognitionPayloadV1(
  payload: WordLandmarkSequencePayload,
  diagnostics: { rawFrameCount?: number; validFrameCount?: number } = {},
): WordRecognitionPayloadValidationResult {
  const errors: WordRecognitionPayloadValidationError[] = [];
  if (!UUID_PATTERN.test(payload.sequence_id)) {
    pushError(errors, {
      code: 'invalid_sequence_id',
      field: 'sequence_id',
      message: 'sequence_id must be a UUID',
      expected: 'uuid',
      received: payload.sequence_id,
    });
  }
  if (!Number.isFinite(Date.parse(payload.captured_at))) {
    pushError(errors, {
      code: 'invalid_captured_at',
      field: 'captured_at',
      message: 'captured_at must be an ISO-8601 timestamp',
      expected: 'ISO-8601 timestamp',
      received: payload.captured_at,
    });
  }
  if (payload.recognition_mode !== 'WORD_ISOLATED') {
    pushError(errors, {
      code: 'invalid_recognition_mode',
      field: 'recognition_mode',
      message: 'recognition_mode must be WORD_ISOLATED',
      expected: 'WORD_ISOLATED',
      received: payload.recognition_mode,
    });
  }
  if (payload.feature_schema_version !== OPEN_SIGNE_LANDMARK_SCHEMA_VERSION) {
    pushError(errors, {
      code: 'invalid_schema',
      field: 'feature_schema_version',
      message: 'feature_schema_version must be OPEN_SIGNE_LANDMARK_SCHEMA_V1',
      expected: OPEN_SIGNE_LANDMARK_SCHEMA_VERSION,
      received: payload.feature_schema_version,
    });
  }
  if (payload.target_frame_count !== WORD_TARGET_FRAME_COUNT) {
    pushError(errors, {
      code: 'invalid_target_frame_count',
      field: 'target_frame_count',
      message: 'target_frame_count must be 60',
      expected: WORD_TARGET_FRAME_COUNT,
      received: payload.target_frame_count,
    });
  }
  if (payload.landmark_count !== OPEN_SIGNE_LANDMARK_COUNT) {
    pushError(errors, {
      code: 'invalid_landmark_count',
      field: 'landmark_count',
      message: 'landmark_count must be 75',
      expected: OPEN_SIGNE_LANDMARK_COUNT,
      received: payload.landmark_count,
    });
  }
  if (payload.coordinate_count !== OPEN_SIGNE_COORDINATE_COUNT) {
    pushError(errors, {
      code: 'invalid_coordinate_count',
      field: 'coordinate_count',
      message: 'coordinate_count must be 3',
      expected: OPEN_SIGNE_COORDINATE_COUNT,
      received: payload.coordinate_count,
    });
  }
  if (payload.coordinate_format !== OPEN_SIGNE_COORDINATE_FORMAT) {
    pushError(errors, {
      code: 'invalid_coordinate_format',
      field: 'coordinate_format',
      message: 'coordinate_format must be shoulder_centered_v1',
      expected: OPEN_SIGNE_COORDINATE_FORMAT,
      received: payload.coordinate_format,
    });
  }
  if (payload.segmentation_kind !== 'dynamic' && payload.segmentation_kind !== 'static') {
    pushError(errors, {
      code: 'invalid_segmentation_kind',
      field: 'segmentation_kind',
      message: 'segmentation_kind must be dynamic or static',
      expected: 'dynamic|static',
      received: String(payload.segmentation_kind),
    });
  }
  if (payload.segmentation_reliable !== true) {
    pushError(errors, {
      code: 'unreliable_segmentation',
      field: 'segmentation_reliable',
      message: 'automatic segmentation must be reliable',
      expected: 'true',
      received: String(payload.segmentation_reliable),
    });
  }
  if (
    !Number.isInteger(payload.usable_frame_count) ||
    payload.usable_frame_count < MIN_VALID_WORD_FRAMES ||
    payload.usable_frame_count > WORD_TARGET_FRAME_COUNT
  ) {
    pushError(errors, {
      code: 'invalid_usable_frame_count',
      field: 'usable_frame_count',
      message: 'usable_frame_count must be an integer between 8 and 60',
      expected: '8..60',
      received: payload.usable_frame_count,
    });
  }
  if (!Number.isInteger(payload.duration_ms) || payload.duration_ms < 500 || payload.duration_ms > 8000) {
    pushError(errors, {
      code: 'invalid_duration',
      field: 'duration_ms',
      message: 'duration_ms must be an integer between 500 and 8000',
      expected: '500..8000',
      received: payload.duration_ms,
    });
  }
  if (!Number.isFinite(payload.source_fps) || payload.source_fps <= 0 || payload.source_fps > 60) {
    pushError(errors, {
      code: 'invalid_source_fps',
      field: 'source_fps',
      message: 'source_fps must be greater than zero and at most 60',
      expected: '0..60',
      received: payload.source_fps,
    });
  }
  Object.entries(payload.quality).forEach(([key, value]) => {
    if (!Number.isFinite(value) || value < 0 || value > 1) {
      pushError(errors, {
        code: 'invalid_quality',
        field: `quality.${key}`,
        message: 'quality ratios must be finite values between 0 and 1',
        expected: '0..1',
        received: String(value),
      });
    }
  });
  if (payload.quality.detected_hand_ratio < 0.35) {
    pushError(errors, {
      code: 'insufficient_valid_frames',
      field: 'quality.detected_hand_ratio',
      message: 'at least one hand must be visible in enough frames',
      expected: '>=0.35',
      received: payload.quality.detected_hand_ratio,
    });
  }
  if (payload.quality.detected_pose_ratio < 0.45) {
    pushError(errors, {
      code: 'insufficient_valid_frames',
      field: 'quality.detected_pose_ratio',
      message: 'body pose must be visible in enough frames',
      expected: '>=0.45',
      received: payload.quality.detected_pose_ratio,
    });
  }
  if (payload.segmentation_kind !== 'static' && payload.quality.movement_score < 0.03) {
    pushError(errors, {
      code: 'insufficient_valid_frames',
      field: 'quality.movement_score',
      message: 'movement score is too low',
      expected: '>=0.03',
      received: payload.quality.movement_score,
    });
  }
  if (diagnostics.validFrameCount !== undefined && diagnostics.validFrameCount < MIN_VALID_WORD_FRAMES) {
    pushError(errors, {
      code: 'insufficient_valid_frames',
      field: 'frames',
      message: 'not enough valid source frames to build a word sequence',
      expected: MIN_VALID_WORD_FRAMES,
      received: diagnostics.validFrameCount,
    });
  }
  if (payload.frames.length !== WORD_TARGET_FRAME_COUNT) {
    pushError(errors, {
      code: 'invalid_frame_count',
      field: 'frames',
      message: 'frames must contain exactly 60 frames',
      expected: WORD_TARGET_FRAME_COUNT,
      received: payload.frames.length,
    });
  }
  let previousTimestamp = -1;
  payload.frames.forEach((frame, frameIndex) => {
    if (frame.index !== frameIndex) {
      pushError(errors, {
        code: 'invalid_frame_index',
        field: `frames.${frameIndex}.index`,
        message: 'frame index must match chronological output order',
        expected: frameIndex,
        received: frame.index,
      });
    }
    if (!Number.isFinite(frame.timestamp_ms) || frame.timestamp_ms < 0 || frame.timestamp_ms > 10000) {
      pushError(errors, {
        code: 'invalid_timestamp',
        field: `frames.${frameIndex}.timestamp_ms`,
        message: 'timestamp_ms must be finite and relative to capture start',
        expected: '0..10000',
        received: frame.timestamp_ms,
      });
    }
    if (frameIndex > 0 && frame.timestamp_ms <= previousTimestamp) {
      pushError(errors, {
        code: 'non_monotonic_timestamp',
        field: `frames.${frameIndex}.timestamp_ms`,
        message: 'timestamps must be strictly increasing',
        expected: `>${previousTimestamp}`,
        received: frame.timestamp_ms,
      });
    }
    previousTimestamp = frame.timestamp_ms;
    if (frame.landmarks.length !== OPEN_SIGNE_LANDMARK_COUNT) {
      pushError(errors, {
        code: 'invalid_landmark_count',
        field: `frames.${frameIndex}.landmarks`,
        message: 'each frame must contain 75 landmarks',
        expected: OPEN_SIGNE_LANDMARK_COUNT,
        received: frame.landmarks.length,
      });
    }
    if (
      frame.presence_mask.length !== OPEN_SIGNE_LANDMARK_COUNT ||
      frame.presence_mask.some((value) => value !== 0 && value !== 1)
    ) {
      pushError(errors, {
        code: 'invalid_presence_mask',
        field: `frames.${frameIndex}.presence_mask`,
        message: 'presence_mask must contain 75 entries of 0 or 1',
        expected: OPEN_SIGNE_LANDMARK_COUNT,
        received: frame.presence_mask.length,
      });
    }
    frame.landmarks.forEach((landmark, landmarkIndex) => {
      if (landmark.length !== OPEN_SIGNE_COORDINATE_COUNT) {
        pushError(errors, {
          code: 'invalid_coordinate_count',
          field: `frames.${frameIndex}.landmarks.${landmarkIndex}`,
          message: 'each landmark must contain three coordinates',
          expected: OPEN_SIGNE_COORDINATE_COUNT,
          received: landmark.length,
        });
      }
      landmark.forEach((coordinate, coordinateIndex) => {
        if (!Number.isFinite(coordinate)) {
          pushError(errors, {
            code: 'non_finite_coordinate',
            field: `frames.${frameIndex}.landmarks.${landmarkIndex}.${coordinateIndex}`,
            message: 'coordinates must be finite numbers',
            expected: 'finite number',
            received: String(coordinate),
          });
        }
      });
    });
  });
  return {
    valid: errors.length === 0,
    errors,
    diagnostics: {
      rawFrameCount: diagnostics.rawFrameCount,
      validFrameCount: diagnostics.validFrameCount,
      outputFrameCount: payload.frames.length,
      payloadByteSize: JSON.stringify(payload).length,
    },
  };
}
