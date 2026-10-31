import { Navigate, Route, Routes } from 'react-router-dom';

import { ContributionPage } from '../features/contributions';
import { RecognitionPage } from '../features/recognition';

export function AppRoutes() {
  return (
    <Routes>
      <Route index element={<RecognitionPage />} />
      <Route path="app/recognition" element={<RecognitionPage />} />
      <Route path="contribute" element={<ContributionPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
