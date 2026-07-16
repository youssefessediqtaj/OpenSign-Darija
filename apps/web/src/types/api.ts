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
};

export type RecognitionResponse = {
  recognition_id?: string;
  request_id: string;
  sequence_id?: string;
  status: string;
  model_name: string;
  model_version: string;
  feature_schema_version?: string;
  predictions: RecognitionPrediction[];
  unknown_probability: number;
  processing_time_ms: number;
};

export type VersionResponse = {
  service: string;
  version: string;
};
