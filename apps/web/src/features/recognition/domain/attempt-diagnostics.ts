/** Ephemeral local debugging only: never include landmarks, images, or identifiers of a person. */
export type AttemptDiagnostic = {
  attempt_id: string;
  segment_start_ms: number;
  segment_end_ms: number;
  captured_frames: number;
  processed_frames: number;
  sequence_length: number | null;
  hand_coverage: number | null;
  pose_coverage: number | null;
  completion_reason: string;
  input_feature_schema: string | null;
  model_feature_schema: string | null;
  model_version: string | null;
  model_id?: string | null;
  experiment_id?: string | null;
  request_status: string;
  reason: string | null;
  output_shape: number[] | null;
  top_three_raw_scores: Array<{ label: string; raw_score: number }> | null;
};
