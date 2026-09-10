/**
 * GuardianEye Master TypeScript Interfaces & Contracts
 */

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface ProcessingJobRecord {
  id: string;
  video_id: string;
  job_status: string;
  progress_percentage: number;
  frames_processed: number;
  total_frames: number;
  inference_fps_achieved: number;
  processing_time_seconds: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface VideoItem {
  id: string;
  filename: string;
  storage_path: string;
  file_size_bytes: number;
  duration_seconds: number;
  fps: number;
  width: number;
  height: number;
  codec: string;
  checksum_sha256: string;
  status: 'UPLOADED' | 'QUEUED' | 'PROCESSING' | 'PROCESSED' | 'COMPLETED' | 'FAILED' | string;
  created_at: string;
}

export interface VideoResponse extends VideoItem {
  camera_id?: string;
  updated_at: string;
  processing_jobs: ProcessingJobRecord[];
}

export interface TrackPointResponse {
  frame_number: number;
  timestamp_seconds: number;
  bbox_xyxy: [number, number, number, number];
  centroid_xy: [number, number];
  velocity_xy: [number, number];
  confidence: number;
  zone_id?: string;
  // Ground-contact anchor point (see backend TrackPointResponse) — use
  // this for overlay placement, not a bbox-center derived locally.
  anchor_xy?: [number, number];
  normalized_xy?: [number, number];
}

export interface TrackResponse {
  id: string;
  video_id: string;
  track_id: number;
  class_name: string;
  confidence: number;
  first_frame: number;
  last_frame: number;
  duration_seconds: number;
  max_velocity: number;
  trajectory_points: TrackPointResponse[];
}

export interface TrajectorySummaryResponse {
  video_id: string;
  total_tracks: number;
  tracks: TrackResponse[];
}

export interface BehaviourEvidenceResponse {
  trigger_rule: string;
  primary_entity_id: number;
  primary_class: string;
  secondary_entity_id?: number;
  secondary_class?: string;
  peak_velocity_px_s?: number;
  impact_deceleration?: number;
  fall_height_px?: number;
  duration_seconds?: number;
  zone_code?: string;
  spatial_overlap_iou?: number;
  metrics?: Record<string, unknown>;
}

export interface BehaviourEventResponse {
  id?: string;
  video_id?: string;
  behaviour_type: string;
  severity: string;
  start_frame: number;
  end_frame: number;
  start_time_seconds: number;
  end_time_seconds: number;
  duration_seconds: number;
  confidence: number;
  description: string;
  evidence?: BehaviourEvidenceResponse;
  keyframe_indices: number[];
}

export interface DetectedBox {
  track_id: number;
  class_name: string;
  bbox_xyxy: [number, number, number, number];
  confidence: number;
  velocity_xy?: [number, number];
  state_label?: string;
  is_primary?: boolean;
}

export interface ReplayKeyframe {
  frame_index: number;
  timestamp_seconds: number;
  image_url: string;
  sha256_hash: string;
  boxes: DetectedBox[];
}

export interface IncidentItem {
  id: string;
  incident_code: string;
  behaviour_event_id: string;
  warehouse_id: string;
  zone_id?: string;
  camera_id?: string;
  title: string;
  summary: string;
  severity: SeverityLevel;
  status: 'DETECTED' | 'ALERTED' | 'ACKNOWLEDGED' | 'UNDER_REVIEW' | 'CONFIRMED' | 'REJECTED' | 'ACTION_TAKEN' | 'RESOLVED';
  assigned_to?: string;
  resolved_at?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface AlertItem {
  id: string;
  behaviour_event_id: string;
  zone_id?: string;
  alert_level: SeverityLevel;
  message: string;
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';
  deduplication_key: string;
  acknowledged_by?: string;
  acknowledged_at?: string;
  created_at: string;
}

export interface EvidencePackageItem {
  id: string;
  incident_id: string;
  snapshot_path: string;
  clip_path: string;
  pre_event_seconds: number;
  post_event_seconds: number;
  sha256_checksum: string;
  overlay_data: string;
}

export interface IncidentReplayItem {
  incident_id: string;
  video_id: string;
  behaviour_code: string;
  clip_url: string;
  snapshot_url: string;
  sha256_checksum: string;
  duration_seconds: number;
  keyframes: ReplayKeyframe[];
}

export interface HeatmapPoint {
  x_normalized: number;
  y_normalized: number;
  intensity: number;
  zone_code: string;
  zone_name: string;
  incident_count: number;
}

export interface BehaviourDistributionItem {
  behaviour_code: string;
  count: number;
  percentage: number;
  // null when no risk assessment exists yet for this behaviour code —
  // render as "N/A", never as 0 (0 would imply verified zero risk).
  avg_risk_score: number | null;
}

export interface RiskTrendPoint {
  label: string;
  period_start: string;
  period_end: string;
  total_incidents: number;
  avg_risk_score: number | null;
}

export interface RiskTrendComparison {
  period_a_label: string;
  period_b_label: string;
  period_a_avg_risk: number | null;
  period_b_avg_risk: number | null;
  direction: 'INCREASED' | 'DECREASED' | 'STABLE' | null;
  percent_change: number | null;
  data_available: boolean;
}

export interface AnalyticsProvenance {
  avg_risk_score_method: string;
  damage_exposure_method: string;
  heatmap_method: string;
  response_time_method: string;
  generated_at: string;
}

export interface DashboardSummary {
  total_videos_processed: number;
  total_incidents_detected: number;
  critical_incidents: number;
  open_alerts: number;
  // Kept for backward compatibility — mirrors potential_damage_exposure_usd.
  estimated_damage_loss_usd: number;
  potential_damage_exposure_usd: number;
  confirmed_damage_cost_usd: number;
  // null when there are zero acknowledged alerts to average.
  mean_time_to_acknowledge_seconds: number | null;
  behaviour_distribution: BehaviourDistributionItem[];
  risk_heatmaps: HeatmapPoint[];
  operational_health_status: 'OPTIMAL' | 'DEGRADED' | 'CRITICAL';
  risk_trend_daily: RiskTrendPoint[];
  risk_trend_shift: RiskTrendComparison | null;
  provenance: AnalyticsProvenance | null;
}

export interface ZoneTopology {
  zone_id: string;
  zone_code: string;
  zone_name: string;
  zone_type: string;
  polygon_points: [number, number][];
  // Same polygon, normalized to a shared 0-1 plane — render from this,
  // not polygon_points (which is in an arbitrary zone-authoring plane
  // with no declared physical scale). See ai/spatial/coordinate_transform.py.
  normalized_polygon_points: [number, number][];
  risk_multiplier: number;
  is_restricted: boolean;
}

export interface CameraTopology {
  camera_id: string;
  camera_code: string;
  camera_name: string;
  position_xyz: [number, number, number];
  // Normalized against the warehouse's own declared width/length —
  // render from this, not position_xyz directly against dimensions_meters.
  normalized_position: [number, number];
  is_positioned: boolean;
  orientation_degrees: number | null;
  fov_degrees: number;
  coverage_range_m: number;
  coverage_zones: string[];
  is_calibrated: boolean;
  status: string;
}

export interface EntityTopology {
  track_id: number;
  video_id: string;
  camera_id: string | null;
  class_name: string;
  normalized_position: [number, number];
  zone_id: string | null;
  world_position: [number, number] | null;
  world_position_quality: string | null;
  confidence: number;
  last_seen_frame: number;
  last_seen_timestamp_seconds: number;
}

export interface DigitalTwinTopology {
  warehouse_id: string;
  warehouse_name: string;
  dimensions_meters: [number, number, number];
  zones: ZoneTopology[];
  cameras: CameraTopology[];
  entities: EntityTopology[];
  active_entity_count: number;
  is_live_entity_count: boolean;
}

export interface CameraRecord {
  id: string;
  warehouse_id: string;
  zone_id: string | null;
  name: string;
  camera_code: string;
  rtsp_url: string | null;
  fps: number;
  resolution: string;
  status: string;
  location_x: number;
  location_y: number;
  location_z: number;
  is_positioned: boolean;
  orientation_degrees: number | null;
  fov_degrees: number;
  coverage_range_m: number;
  is_calibrated: boolean;
  created_at: string;
  updated_at: string;
}

export interface CameraCreatePayload {
  warehouse_id: string;
  name: string;
  camera_code: string;
  zone_id?: string | null;
  rtsp_url?: string | null;
  fps?: number;
  resolution?: string;
  status?: string;
}

export interface CameraUpdatePayload {
  name?: string;
  zone_id?: string | null;
  rtsp_url?: string | null;
  fps?: number;
  resolution?: string;
  status?: string;
  location_x?: number;
  location_y?: number;
  location_z?: number;
  orientation_degrees?: number;
  fov_degrees?: number;
  coverage_range_m?: number;
}

export interface CalibrationPointPair {
  video_point: [number, number];
  world_point: [number, number];
}

export interface CalibrationRecord {
  camera_id: string;
  source_points: [number, number][];
  world_points: [number, number][];
  homography_matrix: number[][] | null;
  reprojection_error: number | null;
  is_active: boolean;
  calibrated_at: string;
}

export interface CitationReference {
  source_type: string;
  source_id: string;
  title: string;
  confidence: number;
  snippet: string;
}

export interface ComparisonMetric {
  label: string;
  period_a_label: string;
  period_b_label: string;
  period_a_value: number;
  period_b_value: number;
  absolute_change: number;
  percent_change: number | null;
  direction: 'INCREASED' | 'DECREASED' | 'STABLE';
}

export interface WhatChangedSummary {
  improved: string[];
  worsened: string[];
  new_items: string[];
  persistent: string[];
  most_significant_change: string | null;
}

export interface AssistantQueryResponse {
  answer: string;
  grounded_citations: CitationReference[];
  is_grounded: boolean;
  confidence: number;
  suggested_followups: string[];
  // Present only for comparative/temporal questions ("compare today vs
  // yesterday", "what changed this shift?") — absent for every other query.
  period_a_label?: string | null;
  period_b_label?: string | null;
  comparison?: ComparisonMetric[] | null;
  what_changed?: WhatChangedSummary | null;
  why_it_matters?: string | null;
  recommended_action?: string | null;
  data_available?: boolean;
  llm_provider_used?: string | null;
}

export interface BehaviourDNAItem {
  track_id: number;
  class_name: string;
  vector_32d: number[];
  state_signature: string;
  similarity_drop: number;
  similarity_drag: number;
  similarity_throw: number;
  similarity_step: number;
}

export interface CounterfactualSim {
  observed_action: string;
  observed_risk_score: number;
  counterfactual_action: string;
  simulated_risk_score: number;
  risk_delta: number;
  simulation_method: string;
}

export interface HumanReviewPayload {
  incident_id: string;
  review_outcome: 'CORRECT' | 'INCORRECT' | 'CHANGE_BEHAVIOUR' | 'UNCERTAIN';
  corrected_behaviour_code?: string;
  reviewer_notes?: string;
  is_curated_for_training?: boolean;
}

export interface HumanReviewItem {
  id: string;
  incident_id: string;
  reviewed_by: string;
  review_outcome: string;
  corrected_behaviour_code?: string;
  reviewer_notes?: string;
  is_curated_for_training: boolean;
  created_at: string;
}

export interface PreventionRuleItem {
  behaviour_code: string;
  rule_name: string;
  description: string;
  risk_category: string;
  severity_default: string;
  sop_citation: string;
  detection_threshold_description: string;
}

export interface RecommendationItem {
  id: string;
  incident_id: string;
  action_title: string;
  description: string;
  prevention_type: string;
  estimated_risk_reduction_pct: number;
  status: string;
  created_at: string;
}

export interface RootCauseItem {
  id: string;
  incident_id: string;
  cause_category: string;
  observed_factors: string;
  inferred_factors: string;
  confidence: number;
  created_at: string;
}

export interface ModelArtifactItem {
  id: string;
  name: string;
  model_type: string;
  version: string;
  framework: string;
  artifact_path: string;
  status: string;
  approved_by?: string;
  approved_at?: string;
  created_at: string;
}

export interface DatasetItem {
  id: string;
  name: string;
  description?: string;
  dataset_type: string;
  created_at: string;
}

