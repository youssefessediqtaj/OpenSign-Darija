import { defineConfig, devices } from '@playwright/test';

const runtimeProcess = (globalThis as {
  process?: { env?: Record<string, string | undefined> };
}).process;
const fakeCameraVideo = runtimeProcess?.env?.PLAYWRIGHT_FAKE_CAMERA_VIDEO;
const fakeCameraArguments = fakeCameraVideo
  ? [
      '--use-fake-device-for-media-stream',
      '--use-fake-ui-for-media-stream',
      `--use-file-for-fake-video-capture=${fakeCameraVideo}`,
    ]
  : [];

export default defineConfig({
  testDir: './tests/e2e',
  webServer: {
    command: 'npm run dev',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: true,
  },
  use: {
    baseURL: 'http://127.0.0.1:5173',
    ...devices['Desktop Chrome'],
    launchOptions: {
      args: fakeCameraArguments,
    },
  },
});
