import { apiRequest } from '../lib/api';
import type {
  CampaignSign,
  ConsentRecord,
  ConsentTemplate,
  ConsentType,
  ContributionCampaign,
  ContributionRecording,
  ContributorProfile,
  DatasetContribution,
  DatasetVersion,
  ActiveModel,
  UploadSession,
} from '../types/api';

export const REQUIRED_LANDMARK_CONSENTS: ConsentType[] = [
  'LANDMARK_PROCESSING',
  'LANDMARK_STORAGE',
  'RESEARCH_USE',
  'MODEL_TRAINING',
];

export const VIDEO_CONSENTS: ConsentType[] = ['VIDEO_RECORDING', 'VIDEO_STORAGE'];

export const datasetApi = {
  templates: () => apiRequest<ConsentTemplate[]>('/api/v1/consents/templates'),
  myConsents: () => apiRequest<ConsentRecord[]>('/api/v1/consents/me'),
  createConsents: (consent_template_id: string, choices: { consent_type: ConsentType; granted: boolean }[]) =>
    apiRequest<ConsentRecord[]>('/api/v1/consents', {
      method: 'POST',
      body: JSON.stringify({ consent_template_id, choices, language: 'fr', evidence: { ui_action: 'checkbox_submit' } }),
    }),
  revokeConsent: (id: string) => apiRequest<ConsentRecord>(`/api/v1/consents/${id}/revoke`, { method: 'POST' }),
  profile: () => apiRequest<ContributorProfile>('/api/v1/contributors/me'),
  createProfile: () =>
    apiRequest<ContributorProfile>('/api/v1/contributors/me', {
      method: 'POST',
      body: JSON.stringify({ preferred_interface_language: 'fr', accessibility_preferences: {} }),
    }),
  campaigns: () => apiRequest<ContributionCampaign[]>('/api/v1/contribution-campaigns'),
  campaign: (id: string) => apiRequest<ContributionCampaign>(`/api/v1/contribution-campaigns/${id}`),
  campaignSigns: (id: string) => apiRequest<CampaignSign[]>(`/api/v1/contribution-campaigns/${id}/signs`),
  createContribution: (campaign_id: string, campaign_sign_id: string, wants_video: boolean) =>
    apiRequest<DatasetContribution>('/api/v1/contributions', {
      method: 'POST',
      body: JSON.stringify({ campaign_id, campaign_sign_id, wants_video }),
    }),
  contribution: (id: string) => apiRequest<DatasetContribution>(`/api/v1/contributions/${id}`),
  myContributions: () => apiRequest<DatasetContribution[]>('/api/v1/contributions/me'),
  addRecording: (contributionId: string, body: Record<string, unknown>) =>
    apiRequest<ContributionRecording>(`/api/v1/contributions/${contributionId}/recordings`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  uploadSession: (contributionId: string, recordingId: string, include_video: boolean) =>
    apiRequest<UploadSession>(`/api/v1/contributions/${contributionId}/recordings/${recordingId}/upload-session`, {
      method: 'POST',
      body: JSON.stringify({
        include_video,
        landmark_content_type: 'application/json',
        video_content_type: include_video ? 'video/webm' : undefined,
      }),
    }),
  confirmUpload: (contributionId: string, recordingId: string, body: Record<string, unknown>) =>
    apiRequest<ContributionRecording>(`/api/v1/contributions/${contributionId}/recordings/${recordingId}/confirm-upload`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  submitContribution: (id: string) => apiRequest<DatasetContribution>(`/api/v1/contributions/${id}/submit`, { method: 'POST' }),
  revokeContribution: (id: string) => apiRequest<DatasetContribution>(`/api/v1/contributions/${id}/revoke`, { method: 'POST' }),
  linguisticQueue: () => apiRequest<DatasetContribution[]>('/api/v1/reviews/linguistic/queue'),
  mlQueue: () => apiRequest<DatasetContribution[]>('/api/v1/reviews/ml/queue'),
  linguisticDecision: (id: string, decision: 'APPROVED' | 'REJECTED' | 'REVISION_REQUESTED') =>
    apiRequest(`/api/v1/reviews/linguistic/${id}/decision`, { method: 'POST', body: JSON.stringify({ decision }) }),
  mlDecision: (id: string, decision: 'APPROVED' | 'REJECTED' | 'REVISION_REQUESTED') =>
    apiRequest(`/api/v1/reviews/ml/${id}/decision`, { method: 'POST', body: JSON.stringify({ decision }) }),
  datasets: () => apiRequest<DatasetVersion[]>('/api/v1/admin/datasets'),
  createDataset: () =>
    apiRequest<DatasetVersion>('/api/v1/admin/datasets', {
      method: 'POST',
      body: JSON.stringify({
        name: 'opensign-darija-pilot',
        semantic_version: '0.1.0',
        description: 'Version brouillon construite depuis les contributions approuvees.',
        feature_schema_version: '1.0.0',
      }),
    }),
  buildDataset: (id: string) => apiRequest<DatasetVersion>(`/api/v1/admin/datasets/${id}/build`, { method: 'POST' }),
  activeModel: () => apiRequest<ActiveModel>('/api/v1/models/active'),
  models: () => apiRequest<ActiveModel[]>('/api/v1/admin/models'),
  activateModel: (id: string) => apiRequest<ActiveModel>(`/api/v1/admin/models/${id}/activate`, { method: 'POST' }),
  rollbackModel: (id: string) => apiRequest<ActiveModel>(`/api/v1/admin/models/${id}/rollback`, { method: 'POST' }),
};
