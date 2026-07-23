import { normalizeSchemaV1Frame } from './normalize-landmarks';
import type { HolisticFrame, NormalizedLandmark } from './landmarks';
import type {
  RecognitionFlowState,
  SegmentationEvent,
  SegmentationKind,
  SegmentedSign,
} from '../state/recognition-flow';
import { uniformSample } from './resample-landmark-sequence';

type AutomaticSegmentationConfig = {
  targetFrames: number;
  preRollFrames: number;
  postRollFrames: number;
  minimumDurationMs: number;
  maximumDurationMs: number;
  minimumUsableFrames: number;
  dynamicStartEnergy: number;
  dynamicStartFrames: number;
  endEnergy: number;
  endStableMs: number;
  staticDwellMs: number;
  staticPoseDistance: number;
  restBaselineFrames: number;
  restEnergy: number;
  resetPoseDistance: number;
  resetStableMs: number;
  cooldownMs: number;
  duplicateWindowMs: number;
  duplicateSimilarity: number;
};

export const DEFAULT_SEGMENTATION_CONFIG: AutomaticSegmentationConfig = {
  targetFrames: 60,
  preRollFrames: 8,
  postRollFrames: 3,
  minimumDurationMs: 500,
  maximumDurationMs: 6000,
  minimumUsableFrames: 8,
  dynamicStartEnergy: 0.12,
  dynamicStartFrames: 2,
  endEnergy: 0.045,
  endStableMs: 420,
  staticDwellMs: 750,
  staticPoseDistance: 0.32,
  restBaselineFrames: 8,
  restEnergy: 0.035,
  resetPoseDistance: 0.2,
  resetStableMs: 350,
  cooldownMs: 800,
  duplicateWindowMs: 3000,
  duplicateSimilarity: 0.985,
};

const POSE_MOTION_INDICES = [11, 12, 13, 14, 15, 16];

function finitePoint(point: NormalizedLandmark | undefined): point is NormalizedLandmark {
  return Boolean(
    point && Number.isFinite(point.x) && Number.isFinite(point.y) && Number.isFinite(point.z),
  );
}

function handsPresent(frame: HolisticFrame): boolean {
  return (
    frame.metadata.leftHandDetected ||
    frame.metadata.rightHandDetected ||
    frame.leftHand.some(finitePoint) ||
    frame.rightHand.some(finitePoint)
  );
}

function usableFrame(frame: HolisticFrame): boolean {
  return (
    handsPresent(frame) &&
    frame.metadata.poseDetected &&
    finitePoint(frame.pose[11]) &&
    finitePoint(frame.pose[12])
  );
}

function handIsPresent(metadataDetected: boolean, landmarks: NormalizedLandmark[]): boolean {
  return metadataDetected || landmarks.some(finitePoint);
}

type HandZone = 'absent' | 'signing' | 'neutral' | 'rest';

function classifyHandZone(frame: HolisticFrame): HandZone {
  const leftShoulder = frame.pose[11];
  const rightShoulder = frame.pose[12];
  if (!finitePoint(leftShoulder) || !finitePoint(rightShoulder)) return 'absent';

  const anchors: NormalizedLandmark[] = [];
  if (handIsPresent(frame.metadata.leftHandDetected, frame.leftHand)) {
    const leftAnchor = finitePoint(frame.leftHand[0]) ? frame.leftHand[0] : frame.pose[15];
    if (finitePoint(leftAnchor)) anchors.push(leftAnchor);
  }
  if (handIsPresent(frame.metadata.rightHandDetected, frame.rightHand)) {
    const rightAnchor = finitePoint(frame.rightHand[0]) ? frame.rightHand[0] : frame.pose[16];
    if (finitePoint(rightAnchor)) anchors.push(rightAnchor);
  }
  if (anchors.length === 0) return 'absent';

  const shoulderY = (leftShoulder.y + rightShoulder.y) / 2;
  const shoulderWidth = Math.hypot(
    leftShoulder.x - rightShoulder.x,
    leftShoulder.y - rightShoulder.y,
    leftShoulder.z - rightShoulder.z,
  );
  const lowerSigningBoundary = shoulderY + Math.max(0.12, shoulderWidth * 0.9);
  const upperRestBoundary = shoulderY + Math.max(0.2, shoulderWidth * 1.15);
  if (anchors.some((anchor) => anchor.y <= lowerSigningBoundary)) return 'signing';
  if (anchors.every((anchor) => anchor.y >= upperRestBoundary)) return 'rest';
  return 'neutral';
}

function pairedDistances(
  previous: NormalizedLandmark[],
  current: NormalizedLandmark[],
  indices?: number[],
): number[] {
  const selected = indices ?? Array.from({ length: Math.min(previous.length, current.length) }, (_, index) => index);
  return selected.flatMap((index) => {
    const before = previous[index];
    const after = current[index];
    if (!finitePoint(before) || !finitePoint(after)) return [];
    return [Math.hypot(after.x - before.x, after.y - before.y, after.z - before.z)];
  });
}

function frameMotionEnergy(previous: HolisticFrame | null, current: HolisticFrame): number {
  if (!previous) return 0;
  const distances = [
    ...pairedDistances(previous.pose, current.pose, POSE_MOTION_INDICES),
    ...pairedDistances(previous.leftHand, current.leftHand),
    ...pairedDistances(previous.rightHand, current.rightHand),
  ];
  if (distances.length === 0) return 0;
  const mean = distances.reduce((total, value) => total + value, 0) / distances.length;
  return Number(Math.min(mean / 0.05, 1).toFixed(4));
}

function poseVector(frame: HolisticFrame): number[] {
  const normalized = normalizeSchemaV1Frame(frame, 0, 0);
  return normalized.landmarks.slice(13, 75).flatMap((point, index) =>
    normalized.presence_mask[index + 13] === 1 ? point : [0, 0, 0],
  );
}

function meanDistance(left: number[], right: number[]): number {
  const length = Math.min(left.length, right.length);
  if (length === 0) return 1;
  let total = 0;
  for (let index = 0; index < length; index += 1) {
    total += Math.abs(left[index] - right[index]);
  }
  return total / length;
}

function mergeBaseline(current: number[] | null, next: number[], count: number): number[] {
  if (!current || count === 0) return [...next];
  const weight = Math.min(count, 20);
  return current.map((value, index) => (value * weight + (next[index] ?? value)) / (weight + 1));
}

function sequenceDescriptor(frames: HolisticFrame[]): number[] {
  const sampled = uniformSample(frames, 12);
  if (sampled.length === 0) return [];
  const vectors = sampled.map(poseVector);
  const length = vectors[0]?.length ?? 0;
  return Array.from({ length }, (_, index) =>
    Number((vectors.reduce((sum, vector) => sum + (vector[index] ?? 0), 0) / vectors.length).toFixed(5)),
  );
}

function sequenceSimilarity(left: number[], right: number[]): number {
  if (left.length === 0 || right.length === 0) return 0;
  return Number(Math.max(0, 1 - Math.min(meanDistance(left, right) / 0.5, 1)).toFixed(4));
}

export class AutomaticSignSegmenter {
  private readonly config: AutomaticSegmentationConfig;
  private preRoll: HolisticFrame[] = [];
  private captureFrames: HolisticFrame[] = [];
  private captureKind: SegmentationKind = 'dynamic';
  private captureStartedAt = 0;
  private previousFrame: HolisticFrame | null = null;
  private dynamicFrames = 0;
  private staticSince: number | null = null;
  private stableSince: number | null = null;
  private postRollRemaining = 0;
  private restBaseline: number[] | null = null;
  private restBaselineCount = 0;
  private cooldownStartedAt = 0;
  private resetSince: number | null = null;
  private resetObserved = true;
  private lastRecognizedDescriptor: number[] | null = null;
  private lastRecognizedAt = Number.NEGATIVE_INFINITY;

  constructor(config: Partial<AutomaticSegmentationConfig> = {}) {
    this.config = { ...DEFAULT_SEGMENTATION_CONFIG, ...config };
  }

  reset(): void {
    this.preRoll = [];
    this.captureFrames = [];
    this.previousFrame = null;
    this.dynamicFrames = 0;
    this.staticSince = null;
    this.stableSince = null;
    this.postRollRemaining = 0;
    this.cooldownStartedAt = 0;
    this.resetSince = null;
    this.resetObserved = true;
    this.restBaseline = null;
    this.restBaselineCount = 0;
    this.lastRecognizedDescriptor = null;
    this.lastRecognizedAt = Number.NEGATIVE_INFINITY;
  }

  beginCooldown(timestampMs: number): void {
    this.cooldownStartedAt = timestampMs;
    this.resetSince = null;
    this.resetObserved = false;
    this.preRoll = [];
    this.captureFrames = [];
    this.dynamicFrames = 0;
    this.staticSince = null;
    this.stableSince = null;
    this.postRollRemaining = 0;
  }

  rememberRecognized(segment: SegmentedSign, timestampMs: number): void {
    this.lastRecognizedDescriptor = segment.descriptor;
    this.lastRecognizedAt = timestampMs;
  }

  shouldSuppressDuplicate(segment: SegmentedSign, timestampMs: number): boolean {
    if (this.resetObserved || !this.lastRecognizedDescriptor) return false;
    if (timestampMs - this.lastRecognizedAt > this.config.duplicateWindowMs) return false;
    return (
      sequenceSimilarity(segment.descriptor, this.lastRecognizedDescriptor) >=
      this.config.duplicateSimilarity
    );
  }

  ingest(frame: HolisticFrame, state: RecognitionFlowState): SegmentationEvent {
    const energy = frameMotionEnergy(this.previousFrame, frame);
    this.previousFrame = frame;

    if (state === 'COOLDOWN') return this.observeCooldown(frame, energy);
    if (state === 'CAPTURING') return this.capture(frame, energy);
    if (state !== 'WAITING_FOR_SIGN') return { type: 'none' };
    return this.waitForSign(frame, energy);
  }

  private waitForSign(frame: HolisticFrame, energy: number): SegmentationEvent {
    this.preRoll.push(frame);
    if (this.preRoll.length > this.config.preRollFrames) this.preRoll.shift();

    if (!handsPresent(frame)) {
      this.dynamicFrames = 0;
      this.staticSince = null;
      if (
        energy <= this.config.restEnergy &&
        frame.metadata.poseDetected &&
        finitePoint(frame.pose[11]) &&
        finitePoint(frame.pose[12])
      ) {
        const vector = poseVector(frame);
        this.restBaseline = mergeBaseline(this.restBaseline, vector, this.restBaselineCount);
        this.restBaselineCount += 1;
      }
      return { type: 'none' };
    }

    if (energy >= this.config.dynamicStartEnergy) this.dynamicFrames += 1;
    else this.dynamicFrames = Math.max(0, this.dynamicFrames - 1);

    if (this.dynamicFrames >= this.config.dynamicStartFrames) {
      this.startCapture('dynamic', frame.timestampMs);
      return { type: 'started', kind: 'dynamic' };
    }

    const vector = poseVector(frame);
    const baselineReady = this.restBaselineCount >= this.config.restBaselineFrames;
    const distanceFromRest = this.restBaseline ? meanDistance(vector, this.restBaseline) : 0;
    const stable = energy <= this.config.restEnergy;
    const handZone = classifyHandZone(frame);
    const inSigningZone = handZone === 'signing';
    const clearlyAtRest = handZone === 'rest';

    if (!baselineReady && stable) {
      if (clearlyAtRest) {
        this.restBaseline = mergeBaseline(this.restBaseline, vector, this.restBaselineCount);
        this.restBaselineCount += 1;
      }
    }

    const displacedFromRest =
      baselineReady && distanceFromRest >= this.config.staticPoseDistance;
    if (
      stable &&
      handZone !== 'absent' &&
      !clearlyAtRest &&
      (displacedFromRest || inSigningZone)
    ) {
      this.staticSince ??= frame.timestampMs;
      if (frame.timestampMs - this.staticSince >= this.config.staticDwellMs) {
        this.startCapture('static', frame.timestampMs);
        return { type: 'started', kind: 'static' };
      }
      return { type: 'none' };
    }

    this.staticSince = null;
    if (
      baselineReady &&
      stable &&
      clearlyAtRest &&
      distanceFromRest < this.config.resetPoseDistance
    ) {
      this.restBaseline = mergeBaseline(this.restBaseline, vector, this.restBaselineCount);
      this.restBaselineCount += 1;
    }
    return { type: 'none' };
  }

  private startCapture(kind: SegmentationKind, timestampMs: number): void {
    this.captureKind = kind;
    this.captureFrames = [...this.preRoll];
    this.captureStartedAt = this.captureFrames[0]?.timestampMs ?? timestampMs;
    this.stableSince = null;
    this.postRollRemaining = 0;
    this.dynamicFrames = 0;
    this.staticSince = null;
  }

  private capture(frame: HolisticFrame, energy: number): SegmentationEvent {
    this.captureFrames.push(frame);
    const durationMs = frame.timestampMs - this.captureStartedAt;
    if (durationMs >= this.config.maximumDurationMs) return this.complete(frame.timestampMs, true);

    if (energy <= this.config.endEnergy) this.stableSince ??= frame.timestampMs;
    else {
      this.stableSince = null;
      this.postRollRemaining = 0;
    }

    if (
      this.stableSince !== null &&
      frame.timestampMs - this.stableSince >= this.config.endStableMs &&
      this.postRollRemaining === 0
    ) {
      this.postRollRemaining = this.config.postRollFrames;
    }

    if (this.postRollRemaining > 0) {
      this.postRollRemaining -= 1;
      if (this.postRollRemaining === 0) return this.complete(frame.timestampMs, false);
    }
    return { type: 'none' };
  }

  private complete(endedAtMs: number, maximumReached: boolean): SegmentationEvent {
    const sourceFrames = [...this.captureFrames];
    const durationMs = endedAtMs - this.captureStartedAt;
    const usableSourceFrames = sourceFrames.filter(usableFrame);
    this.captureFrames = [];
    this.preRoll = sourceFrames.slice(-this.config.preRollFrames);
    this.stableSince = null;
    this.postRollRemaining = 0;

    if (durationMs < this.config.minimumDurationMs) {
      return { type: 'rejected', reason: 'too_short' };
    }
    if (usableSourceFrames.length < this.config.minimumUsableFrames) {
      return { type: 'rejected', reason: 'insufficient_usable_frames' };
    }
    if (!maximumReached && this.captureKind === 'dynamic' && sourceFrames.length < this.config.minimumUsableFrames) {
      return { type: 'rejected', reason: 'unreliable_boundary' };
    }

    const frames = uniformSample(usableSourceFrames, this.config.targetFrames);
    const usableFrameCount = Math.min(usableSourceFrames.length, this.config.targetFrames);
    const segment: SegmentedSign = {
      id: crypto.randomUUID(),
      kind: this.captureKind,
      reliable: true,
      startedAtMs: this.captureStartedAt,
      endedAtMs,
      sourceFrames,
      frames,
      usableFrameCount,
      descriptor: sequenceDescriptor(frames),
    };
    return { type: 'completed', segment };
  }

  private observeCooldown(frame: HolisticFrame, energy: number): SegmentationEvent {
    const vector = handsPresent(frame) ? poseVector(frame) : null;
    const distanceFromRest = vector && this.restBaseline ? meanDistance(vector, this.restBaseline) : 0;
    const atRest = !handsPresent(frame) || (Boolean(this.restBaseline) && distanceFromRest < this.config.resetPoseDistance);
    if (atRest && energy <= this.config.restEnergy) this.resetSince ??= frame.timestampMs;
    else this.resetSince = null;

    const cooldownComplete = frame.timestampMs - this.cooldownStartedAt >= this.config.cooldownMs;
    const resetComplete =
      this.resetSince !== null && frame.timestampMs - this.resetSince >= this.config.resetStableMs;
    if (!cooldownComplete || !resetComplete) return { type: 'none' };

    this.resetObserved = true;
    this.preRoll = [frame];
    this.dynamicFrames = 0;
    this.staticSince = null;
    this.resetSince = null;
    return { type: 'reset' };
  }
}
