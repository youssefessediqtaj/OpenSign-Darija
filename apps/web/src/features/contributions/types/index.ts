export type ContributionSignKey = 'salam' | 'chokran' | 'tabib' | 'mosaada' | 'maa';

export type ContributionSign = {
  key: ContributionSignKey;
  label_ar: string;
  darija_transliteration: string | null;
  reference_video_identifier: string;
  reference_video_url: string | null;
  poster_url: string;
  reference_video_approved: boolean;
  recording_instructions: string;
  active: boolean;
  expected_min_duration_seconds: number;
  expected_max_duration_seconds: number;
};

export type ContributionStatus = {
  collection_enabled: boolean;
  compliance_configured: boolean;
  public_submission_allowed: boolean;
  collection_available: boolean;
  storage_status: 'not_checked' | 'available' | 'unavailable';
  message: string;
  missing_configuration: string[];
  invalid_configuration: string[];
  readiness_dwell_ms: number;
};

export type NoticeField = {
  name: string;
  required: boolean;
};

export type ContributionNotice = {
  language: 'fr';
  arabic_translation_status: 'structure_ready_translation_pending';
  title: string;
  summary: string;
  controller_name: string;
  controller_address: string;
  controller_contact: string;
  purpose: string;
  collected_data: NoticeField[];
  refusal_consequence: string;
  recipient_categories: string[];
  model_collaborator_sharing: string;
  storage_location_category: string;
  retention_days: number | null;
  rights: string[];
  rights_request_method: string;
  cndp_procedure_type: string;
  cndp_reference: string;
  notice_version: string;
  consent_timestamp_source: string;
  consent_checkbox_text: string;
  complete_notice: string[];
};

export type ContributionReceipt = {
  status: 'received';
  contribution_id: string;
  sign_key: ContributionSignKey;
  created_at: string;
  consent_notice_version: string;
  review_status: 'pending';
  deletion_request_instructions: string;
};

export type ContributionFormValues = {
  fullName: string;
  age: string;
  city: string;
  signKey: ContributionSignKey;
  consentAccepted: boolean;
};
