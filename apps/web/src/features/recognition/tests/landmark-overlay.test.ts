import { describe, expect, it, vi } from 'vitest';
import { createSyntheticFrame } from '../services/holistic';
import { drawLandmarkOverlay } from '../services/landmark-overlay';

function setup(width = 400, height = 400) {
  const context = { setTransform: vi.fn(), clearRect: vi.fn(), beginPath: vi.fn(), moveTo: vi.fn<(...args: number[]) => void>(), lineTo: vi.fn<(...args: number[]) => void>(), stroke: vi.fn(), arc: vi.fn<(...args: number[]) => void>(), fill: vi.fn() };
  const canvas = { clientWidth: width, clientHeight: height, width: 0, height: 0, getContext: vi.fn(() => context) } as unknown as HTMLCanvasElement;
  return { canvas, context };
}

describe('landmark overlay', () => {
  it('draws both hands, fingertips and upper body using centered cover crop and mirroring', () => {
    const { canvas, context } = setup();
    const frame = createSyntheticFrame(0, 0, 'rest', false);
    const drawn = drawLandmarkOverlay(canvas, frame, true);
    expect(drawn).toMatchObject({ leftDrawn: 21, rightDrawn: 21 });
    expect(context.arc).toHaveBeenCalledTimes(48);
    expect(context.arc.mock.calls.filter((call) => call[2] === 4)).toHaveLength(10);
    const wrist = frame.leftHand[0];
    const renderedWidth = 400 * 1280 / 720;
    expect(context.arc.mock.calls[6][0]).toBeCloseTo(400 - ((400 - renderedWidth) / 2 + wrist.x * renderedWidth));
    expect(context.arc.mock.calls[6][1]).toBeCloseTo(wrist.y * 400);
    expect(context.lineTo).toHaveBeenCalledTimes(47);
  });

  it('renders all detected hand points and connections with zero MediaPipe visibility', () => {
    const { canvas, context } = setup(400, 225);
    const frame = createSyntheticFrame(0, 0, 'rest', false);
    frame.pose = [];
    frame.rightHand = [];
    frame.leftHand = Array.from({ length: 21 }, (_, i) => ({ x: 0.1 + i * 0.02, y: 0.2 + i * 0.01, z: 0, visibility: 0, presence: 0 }));
    drawLandmarkOverlay(canvas, frame, false);
    expect(context.arc).toHaveBeenCalledTimes(21);
    const edges = [[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[0,17],[17,18],[18,19],[19,20]];
    expect(context.lineTo).toHaveBeenCalledTimes(21);
    edges.forEach(([a, b], i) => {
      expect(context.moveTo.mock.calls[i][0]).toBeCloseTo(frame.leftHand[a].x * 400);
      expect(context.lineTo.mock.calls[i][0]).toBeCloseTo(frame.leftHand[b].x * 400);
      expect(context.lineTo.mock.calls[i][1]).toBeCloseTo(frame.leftHand[b].y * 225);
    });
    frame.leftHand[4].x = 0.9;
    frame.leftHand[8].y = 0.8;
    context.arc.mockClear();
    drawLandmarkOverlay(canvas, frame, false);
    expect(context.arc.mock.calls[4][0]).toBeCloseTo(360);
    expect(context.arc.mock.calls[8][1]).toBeCloseTo(180);
    context.arc.mockClear();
    frame.leftHand = [];
    drawLandmarkOverlay(canvas, frame, false);
    expect(context.arc).not.toHaveBeenCalled();
    expect(context.clearRect).toHaveBeenCalledTimes(3);
  });

  it('handles unmirrored coordinates, high DPI, resizing and missing hands', () => {
    const { canvas, context } = setup();
    const frame = createSyntheticFrame(0, 0, 'rest', false);
    const originalDpr = window.devicePixelRatio;
    Object.defineProperty(window, 'devicePixelRatio', { configurable: true, value: 2 });
    try {
      drawLandmarkOverlay(canvas, frame, false);
      expect(canvas.width).toBe(800);
      expect(context.arc.mock.calls[6][0]).toBeCloseTo((400 - 400 * 1280 / 720) / 2 + frame.leftHand[0].x * 400 * 1280 / 720);
      Object.defineProperty(canvas, 'clientWidth', { value: 300, configurable: true });
      context.arc.mockClear();
      drawLandmarkOverlay(canvas, createSyntheticFrame(1, 1, 'no-hands'), false);
      expect(canvas.width).toBe(600);
      expect(context.clearRect).toHaveBeenCalledTimes(2);
      expect(context.arc).toHaveBeenCalledTimes(6);
    } finally {
      Object.defineProperty(window, 'devicePixelRatio', { configurable: true, value: originalDpr });
    }
  });
});
