import { create } from 'zustand';

import type { CameraPreferences } from '../types/camera.types';

const PREFERENCES_KEY = 'opensign.recognitionPreferences';

const defaultPreferences: CameraPreferences = {
  preferredDeviceId: null,
  showLandmarks: true,
  cameraQuality: 'STANDARD',
  performanceMode: 'AUTO',
  batterySaver: false,
  reduceMotion: false,
  theme: 'system',
  language: 'fr',
};

function loadPreferences(): CameraPreferences {
  try {
    const raw = window.localStorage.getItem(PREFERENCES_KEY);
    return raw ? { ...defaultPreferences, ...JSON.parse(raw) } : defaultPreferences;
  } catch {
    return defaultPreferences;
  }
}

type RecognitionStore = {
  preferences: CameraPreferences;
  anonymousSessionId: string;
  updatePreferences: (preferences: Partial<CameraPreferences>) => void;
  resetPreferences: () => void;
};

export const useRecognitionStore = create<RecognitionStore>((set) => ({
  preferences: loadPreferences(),
  anonymousSessionId: crypto.randomUUID(),
  updatePreferences: (nextPreferences) =>
    set((state) => {
      const preferences = { ...state.preferences, ...nextPreferences };
      window.localStorage.setItem(PREFERENCES_KEY, JSON.stringify(preferences));
      return { preferences };
    }),
  resetPreferences: () => {
    window.localStorage.removeItem(PREFERENCES_KEY);
    set({ preferences: defaultPreferences });
  },
}));
