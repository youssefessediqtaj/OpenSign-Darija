import type { HolisticFrame, NormalizedLandmark } from '../domain/landmarks';

const HAND_CONNECTIONS = [[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[0,17],[17,18],[18,19],[19,20]];
const POSE_CONNECTIONS = [[11,12],[11,13],[13,15],[12,14],[14,16]];
const FINGERTIPS = new Set([4, 8, 12, 16, 20]);
const HAND_INDICES = Array.from({ length: 21 }, (_, index) => index);

/** Draw the same normalized frame used by recognition over a centered object-cover video. */
export function drawLandmarkOverlay(canvas: HTMLCanvasElement, frame: HolisticFrame, mirrored: boolean) {
  const context = canvas.getContext('2d');
  if (!context) return null;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const ratio = window.devicePixelRatio || 1;
  const pixelWidth = Math.round(width * ratio);
  const pixelHeight = Math.round(height * ratio);
  if (canvas.width !== pixelWidth) canvas.width = pixelWidth;
  if (canvas.height !== pixelHeight) canvas.height = pixelHeight;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, width, height);
  const videoWidth = frame.metadata.videoWidth;
  const videoHeight = frame.metadata.videoHeight;
  if (!width || !height || !videoWidth || !videoHeight) return null;
  const scale = Math.max(width / videoWidth, height / videoHeight);
  const renderedWidth = videoWidth * scale;
  const renderedHeight = videoHeight * scale;
  const offsetX = (width - renderedWidth) / 2;
  const offsetY = (height - renderedHeight) / 2;
  const point = (landmark: NormalizedLandmark) => ({
    x: mirrored ? width - (offsetX + landmark.x * renderedWidth) : offsetX + landmark.x * renderedWidth,
    y: offsetY + landmark.y * renderedHeight,
  });
  // Holistic hand landmarks can have visibility=0 even when all 21 points are
  // detected. The returned hand array itself is the detection signal; unlike
  // pose, its per-point visibility is not a usable rendering confidence.
  const valid = (p: NormalizedLandmark | undefined, hands: boolean) => p && Number.isFinite(p.x) && Number.isFinite(p.y) && (hands || ((p.visibility === undefined || p.visibility >= 0.5) && (p.presence === undefined || p.presence >= 0.5)));
  const draw = (landmarks: NormalizedLandmark[], connections: number[][], indices: number[], color: string, lineColor: string, hands: boolean) => {
    context.strokeStyle = lineColor;
    context.lineWidth = 2;
    context.lineCap = 'round';
    context.beginPath();
    for (const [a, b] of connections) {
      if (!valid(landmarks[a], hands) || !valid(landmarks[b], hands)) continue;
      const from = point(landmarks[a]);
      const to = point(landmarks[b]);
      context.moveTo(from.x, from.y);
      context.lineTo(to.x, to.y);
    }
    context.stroke();
    context.fillStyle = color;
    let drawn = 0;
    for (const index of indices) {
      if (!valid(landmarks[index], hands)) continue;
      const p = point(landmarks[index]);
      context.beginPath();
      context.arc(p.x, p.y, hands && FINGERTIPS.has(index) ? 4 : 3, 0, Math.PI * 2);
      context.fill();
      drawn += 1;
    }
    return drawn;
  };
  draw(frame.pose, POSE_CONNECTIONS, [11,12,13,14,15,16], '#fb923c', '#fb923c', false);
  const leftDrawn = draw(frame.leftHand, HAND_CONNECTIONS, HAND_INDICES, '#22c55e', '#3b82f6', true);
  const rightDrawn = draw(frame.rightHand, HAND_CONNECTIONS, HAND_INDICES, '#22c55e', '#3b82f6', true);
  return { leftDrawn, rightDrawn, width: canvas.width, height: canvas.height };
}
