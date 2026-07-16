import { toCompactPayload, validateCompactPayload } from '../services/sequence-validator.service';
import type { LandmarkSequence } from '../types/sequence.types';

type WorkerRequest = {
  type: 'compact';
  sequence: LandmarkSequence;
  anonymousSessionId: string;
};

self.onmessage = (event: MessageEvent<WorkerRequest>) => {
  if (event.data.type !== 'compact') return;
  const payload = toCompactPayload(event.data.sequence, event.data.anonymousSessionId);
  const warnings = validateCompactPayload(payload);
  self.postMessage({ type: 'compact-result', payload, warnings });
};
