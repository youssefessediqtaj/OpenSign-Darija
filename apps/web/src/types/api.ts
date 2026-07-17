export type ApiErrorPayload = {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
};

export type User = {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  is_verified: boolean;
  roles: string[];
};

export type Tokens = {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
};

export type Category = {
  id: string;
  slug: string;
  name_fr: string;
  name_ar: string;
  name_en: string;
  description: string;
};

export type Sign = {
  id: string;
  code: string;
  slug: string;
  canonical_meaning: string;
  darija_arabic: string;
  darija_latin: string;
  french_translation: string;
  english_translation: string;
  category: Category;
  status: 'DRAFT' | 'EXPERIMENTAL' | 'ACTIVE' | 'DEPRECATED';
  risk_level: 'NORMAL' | 'SENSITIVE' | 'MEDICAL' | 'LEGAL' | 'FINANCIAL' | 'EMERGENCY';
  is_active: boolean;
};

export type PaginatedSigns = {
  items: Sign[];
  total: number;
  page: number;
  page_size: number;
};

export type RecognitionPrediction = {
  prediction_id?: string;
  label: string;
  confidence: number;
  rank: number;
  sign?: Sign;
  is_unknown?: boolean;
};

export type RecognitionResponse = {
  recognition_id?: string;
  request_id: string;
  sequence_id?: string;
  status: string;
  model_name: string;
  model_version: string;
  feature_schema_version?: string;
  inference_mode?: 'mock' | 'real';
  decision?: 'known' | 'uncertain' | 'unknown';
  confidence_level?: 'high' | 'medium' | 'low';
  predictions: RecognitionPrediction[];
  unknown_probability: number;
  processing_time_ms: number;
};

export type ActiveModel = {
  id?: string | null;
  name: string;
  semantic_version: string;
  status: string;
  architecture: string;
  vocabulary_size: number;
  feature_schema_version: string;
  metrics_json: Record<string, unknown>;
  thresholds_json: Record<string, unknown>;
  is_active: boolean;
};

export type SemanticConcept = {
  id: string;
  code: string;
  name_fr: string;
  name_en: string;
  concept_type: string;
  is_active: boolean;
};

export type LinguisticTemplate = {
  id: string;
  code: string;
  name_fr: string;
  name_ar: string;
  name_en: string;
  category: string;
  risk_level: string;
  version: string;
  is_active: boolean;
};

export type MessageItem = {
  id: string;
  position: number;
  item_type: string;
  sign_id?: string | null;
  semantic_concept_id?: string | null;
  semantic_concept_code?: string | null;
  recognition_session_id?: string | null;
  source: string;
  display_label: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type Message = {
  id: string;
  user_id?: string | null;
  anonymous_session_id?: string | null;
  status: 'DRAFT' | 'GENERATING' | 'READY' | 'COMPLETED' | 'ARCHIVED' | 'DELETED';
  title?: string | null;
  raw_semantic_sequence: unknown[];
  generated_darija_arabic?: string | null;
  generated_darija_latin?: string | null;
  generated_french?: string | null;
  generated_english?: string | null;
  final_darija_arabic?: string | null;
  final_darija_latin?: string | null;
  final_french?: string | null;
  final_english?: string | null;
  generation_strategy: string;
  generation_version: string;
  generation_metadata: Record<string, unknown>;
  is_favorite: boolean;
  item_count: number;
  risk_level: 'NORMAL' | 'SENSITIVE' | 'MEDICAL' | 'LEGAL' | 'FINANCIAL' | 'EMERGENCY';
  items: MessageItem[];
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
};

export type MessageList = {
  items: Message[];
  total: number;
  limit: number;
  offset: number;
};

export type GenerationResponse = {
  message_id: string;
  generation_version: string;
  strategy: string;
  semantic_sequence: string[];
  result: Record<string, string>;
  template?: string | null;
  linguistic_status: 'HIGH' | 'MEDIUM' | 'LOW' | 'INCOMPLETE' | 'AMBIGUOUS';
  system_insertions: string[];
  warnings: string[];
  alternatives: Array<Record<string, string>>;
};

export type MessageRevision = {
  id: string;
  revision_number: number;
  change_type: string;
  before_snapshot: Record<string, unknown>;
  after_snapshot: Record<string, unknown>;
  created_at: string;
};

export type VersionResponse = {
  service: string;
  version: string;
};

export type ConsentType =
  | 'LANDMARK_PROCESSING'
  | 'LANDMARK_STORAGE'
  | 'VIDEO_RECORDING'
  | 'VIDEO_STORAGE'
  | 'RESEARCH_USE'
  | 'MODEL_TRAINING'
  | 'PUBLIC_DATASET_RELEASE'
  | 'COMMERCIAL_USE'
  | 'CONTACT_FOR_FUTURE_STUDIES';

export type ConsentTemplate = {
  id: string;
  code: string;
  version: string;
  title: string;
  summary: string;
  full_text: string;
  language: string;
  is_active: boolean;
  published_at?: string;
};

export type ConsentRecord = {
  id: string;
  consent_template_id: string;
  consent_type: ConsentType;
  granted: boolean;
  granted_at?: string;
  revoked_at?: string;
  evidence: Record<string, unknown>;
  template?: ConsentTemplate;
};

export type ContributorProfile = {
  id: string;
  user_id: string;
  public_id: string;
  preferred_interface_language: string;
  region?: string;
  dominant_hand?: 'LEFT' | 'RIGHT' | 'AMBIDEXTROUS' | 'UNDISCLOSED';
  experience_level?: 'NATIVE_SIGNER' | 'FLUENT_SIGNER' | 'LEARNER' | 'INTERPRETER' | 'UNDISCLOSED';
};

export type ContributionCampaign = {
  id: string;
  name: string;
  slug: string;
  description: string;
  status: 'DRAFT' | 'SCHEDULED' | 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'ARCHIVED';
  target_language: string;
  target_sign_count: number;
  target_repetitions_per_sign: number;
  minimum_repetitions_per_submission: number;
  maximum_repetitions_per_submission: number;
};

export type CampaignSign = {
  id: string;
  campaign_id: string;
  sign_id: string;
  target_repetitions: number;
  minimum_duration_ms: number;
  maximum_duration_ms: number;
  instruction_text: string;
  is_active: boolean;
  sign: Sign;
};

export type RecordingQualityStatus = 'PASSED' | 'WARNING' | 'FAILED';

export type ContributionRecording = {
  id: string;
  contribution_id: string;
  repetition_index: number;
  video_object_key?: string;
  landmark_object_key: string;
  feature_schema_version: string;
  duration_ms: number;
  source_fps: number;
  target_frame_count: number;
  file_size_bytes: number;
  landmark_size_bytes: number;
  checksum_video?: string;
  checksum_landmarks: string;
  quality_score: number;
  automatic_quality_status: RecordingQualityStatus;
  upload_confirmed_at?: string;
};

export type DatasetContribution = {
  id: string;
  contributor_id: string;
  campaign_id: string;
  campaign_sign_id: string;
  status:
    | 'DRAFT'
    | 'CAPTURING'
    | 'READY_TO_SUBMIT'
    | 'UPLOADING'
    | 'SUBMITTED'
    | 'AUTOMATIC_CHECK_FAILED'
    | 'PENDING_LINGUIST_REVIEW'
    | 'LINGUIST_REJECTED'
    | 'PENDING_ML_REVIEW'
    | 'ML_REJECTED'
    | 'APPROVED'
    | 'REVISION_REQUESTED'
    | 'REVOKED'
    | 'ARCHIVED';
  consent_snapshot: Record<string, unknown>;
  campaign?: ContributionCampaign;
  campaign_sign?: CampaignSign;
  recordings: ContributionRecording[];
};

export type UploadSession = {
  recording_id: string;
  landmark: { object_key: string; upload_url: string; expires_in_seconds: number; content_type: string };
  video?: { object_key: string; upload_url: string; expires_in_seconds: number; content_type: string };
};

export type DatasetVersion = {
  id: string;
  name: string;
  semantic_version: string;
  status: 'DRAFT' | 'BUILDING' | 'VALIDATING' | 'READY' | 'PUBLISHED' | 'FAILED' | 'ARCHIVED';
  description: string;
  feature_schema_version: string;
  sign_count: number;
  recording_count: number;
  contributor_count: number;
  manifest_object_key?: string;
  statistics_object_key?: string;
};
