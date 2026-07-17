import { Navigate, Route, Routes } from 'react-router-dom';

import { AppLayout } from '../layouts/AppLayout';
import { PublicLayout } from '../layouts/PublicLayout';
import { AppDashboardPage } from '../pages/AppDashboardPage';
import {
  CampaignDetailPage,
  CampaignsPage,
  ContributePage,
  ContributionDetailPage,
  ContributionHistoryPage,
  ContributionSessionPage,
  ConsentPage,
  DatasetAdminPage,
  LinguisticReviewPage,
  MlReviewPage,
  ModelAdminPage,
  PrivacySettingsPage,
} from '../pages/ContributionPages';
import { DemoPage } from '../pages/DemoPage';
import { HomePage } from '../pages/HomePage';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { RecognitionPage } from '../pages/RecognitionPage';
import { SignsPage } from '../pages/SignsPage';
import { SimplePage } from '../pages/SimplePage';
import { SettingsPage } from '../pages/SettingsPage';
import { ProtectedRoute } from './ProtectedRoute';

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<HomePage />} />
        <Route path="demo" element={<DemoPage />} />
        <Route path="signs" element={<SignsPage />} />
        <Route path="about" element={<SimplePage title="A propos">OpenSign Darija prepare une plateforme open source pour l’accessibilite en Darija et Langue des Signes Marocaine.</SimplePage>} />
        <Route path="privacy" element={<SimplePage title="Confidentialite">Aucune donnee biometrique ni video reelle n’est collectee dans cette phase initiale.</SimplePage>} />
        <Route path="accessibility" element={<SimplePage title="Accessibilite">L’interface privilegie les contrastes, la navigation clavier, les labels explicites et la reduction des animations.</SimplePage>} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route path="app" element={<AppLayout />}>
          <Route index element={<AppDashboardPage />} />
          <Route path="recognition" element={<RecognitionPage />} />
          <Route path="messages" element={<SimplePage title="Messages">Construction de messages Darija prevue pour une prochaine phase.</SimplePage>} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="settings/privacy" element={<PrivacySettingsPage />} />
          <Route path="contribute" element={<ContributePage />} />
          <Route path="contribute/consent" element={<ConsentPage />} />
          <Route path="contribute/campaigns" element={<CampaignsPage />} />
          <Route path="contribute/campaigns/:campaignId" element={<CampaignDetailPage />} />
          <Route path="contribute/session/:contributionId" element={<ContributionSessionPage />} />
          <Route path="contribute/history" element={<ContributionHistoryPage />} />
          <Route path="contribute/history/:contributionId" element={<ContributionDetailPage />} />
        </Route>
        <Route path="admin" element={<AppLayout />}>
          <Route path="reviews/linguistic" element={<LinguisticReviewPage />} />
          <Route path="reviews/ml" element={<MlReviewPage />} />
          <Route path="datasets" element={<DatasetAdminPage />} />
          <Route path="models" element={<ModelAdminPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
