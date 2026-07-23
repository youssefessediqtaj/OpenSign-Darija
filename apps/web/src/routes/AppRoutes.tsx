import { Navigate, Route, Routes } from 'react-router-dom';

import { RecognitionPage } from '../pages/RecognitionPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route index element={<RecognitionPage />} />
      <Route path="app/recognition" element={<RecognitionPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
