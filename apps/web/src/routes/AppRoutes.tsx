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
import { DataSourcesPage } from '../pages/DataSourcesPage';
import { ExternalDatasetsAdminPage } from '../pages/ExternalDatasetsAdminPage';
import { HomePage } from '../pages/HomePage';
import { LoginPage } from '../pages/LoginPage';
import { LinguisticsAdminPage } from '../pages/LinguisticsAdminPage';
import {
  MessageDetailPage,
  MessageEditPage,
  MessageFavoritesPage,
  MessageHistoryPage,
  MessagesHomePage,
  NewMessagePage,
} from '../pages/MessagesPage';
import { RegisterPage } from '../pages/RegisterPage';
import { RecognitionPage } from '../pages/RecognitionPage';
import { SignsPage } from '../pages/SignsPage';
import { SimplePage } from '../pages/SimplePage';
import { SettingsPage } from '../pages/SettingsPage';
import { SpeechAdminPage } from '../pages/SpeechAdminPage';
import { ProtectedRoute } from './ProtectedRoute';

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<HomePage />} />
        <Route path="demo" element={<DemoPage />} />
        <Route path="signs" element={<SignsPage />} />
        <Route path="about" element={<SimplePage title="A propos">OpenSign Darija prepare une plateforme open source pour l’accessibilite en Darija et Langue des Signes Marocaine.</SimplePage>} />
        <Route path="about/data-sources" element={<DataSourcesPage />} />
        <Route path="privacy" element={<SimplePage title="Confidentialite">Aucune donnee biometrique ni video reelle n’est collectee dans cette phase initiale.</SimplePage>} />
        <Route path="accessibility" element={<SimplePage title="Accessibilite">L’interface privilegie les contrastes, la navigation clavier, les labels explicites et la reduction des animations.</SimplePage>} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route path="app" element={<AppLayout />}>
          <Route index element={<AppDashboardPage />} />
          <Route path="recognition" element={<RecognitionPage />} />
          <Route path="messages" element={<MessagesHomePage />} />
          <Route path="messages/new" element={<NewMessagePage />} />
          <Route path="messages/history" element={<MessageHistoryPage />} />
          <Route path="messages/favorites" element={<MessageFavoritesPage />} />
          <Route path="messages/:messageId" element={<MessageDetailPage />} />
          <Route path="messages/:messageId/edit" element={<MessageEditPage />} />
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
          <Route path="datasets/external" element={<ExternalDatasetsAdminPage />} />
          <Route path="datasets/external/kaggle-alphabet" element={<ExternalDatasetsAdminPage labelMode="alphabet" />} />
          <Route path="datasets/external/mendeley-words" element={<ExternalDatasetsAdminPage labelMode="words" />} />
          <Route path="datasets/external/alphabet-labels" element={<ExternalDatasetsAdminPage labelMode="alphabet" />} />
          <Route path="datasets/external/word-labels" element={<ExternalDatasetsAdminPage labelMode="words" />} />
          <Route path="models" element={<ModelAdminPage />} />
          <Route path="linguistics" element={<LinguisticsAdminPage />} />
          <Route path="speech" element={<SpeechAdminPage />} />
          <Route path="speech/voices" element={<SpeechAdminPage />} />
          <Route path="speech/generations" element={<SpeechAdminPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
