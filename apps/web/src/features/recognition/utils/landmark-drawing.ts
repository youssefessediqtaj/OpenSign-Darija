import type { HolisticFrame, NormalizedLandmark } from '../types/landmark.types';

function drawPoint(context: CanvasRenderingContext2D, point: NormalizedLandmark, width: number, height: number) {
  context.beginPath();
  context.arc(point.x * width, point.y * height, 3, 0, Math.PI * 2);
  context.fill();
}

function drawLine(
  context: CanvasRenderingContext2D,
  a: NormalizedLandmark | undefined,
  b: NormalizedLandmark | undefined,
  width: number,
  height: number,
) {
  if (!a || !b) return;
  context.beginPath();
  context.moveTo(a.x * width, a.y * height);
  context.lineTo(b.x * width, b.y * height);
  context.stroke();
}

export function drawLandmarks(canvas: HTMLCanvasElement, frame: HolisticFrame): void {
  const context = canvas.getContext('2d');
  if (!context) return;
  const width = canvas.width;
  const height = canvas.height;
  context.clearRect(0, 0, width, height);
  context.lineWidth = 3;
  context.strokeStyle = 'rgba(20, 184, 166, 0.9)';
  context.fillStyle = 'rgba(255, 255, 255, 0.95)';

  drawLine(context, frame.pose[11], frame.pose[12], width, height);
  drawLine(context, frame.pose[11], frame.pose[13], width, height);
  drawLine(context, frame.pose[13], frame.pose[15], width, height);
  drawLine(context, frame.pose[12], frame.pose[14], width, height);
  drawLine(context, frame.pose[14], frame.pose[16], width, height);

  [...frame.leftHand, ...frame.rightHand, frame.pose[0], frame.pose[11], frame.pose[12], frame.pose[15], frame.pose[16]]
    .filter(Boolean)
    .forEach((point) => drawPoint(context, point, width, height));

  context.strokeStyle = 'rgba(255, 255, 255, 0.65)';
  context.strokeRect(width * 0.18, height * 0.08, width * 0.64, height * 0.82);
}
