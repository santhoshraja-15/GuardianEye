/**
 * GuardianEye Master TypeScript Interfaces & Contracts
 */

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

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
  status: 'QUEUED' | 'PROCESSING' | 'PROCESSED' | 'FAILED';
  created_at: string;
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

export interface HeatmapPoint {
  x_normalized: number;
  y_normalized: number;
  intensity: number;
  zone_code: string;
  incident_count: number;
}

export interface BehaviourDistributionItem {
  behaviour_code: string;
  count: number;
  percentage: number;
  avg_risk_score: number;
}

export interface DashboardSummary {
  total_videos_processed: number;
  total_incidents_detected: number;
  critical_incidents: number;
  open_alerts: number;
  estimated_damage_loss_usd: number;
  mean_time_to_acknowledge_seconds: number;
  behaviour_distribution: BehaviourDistributionItem[];
  risk_heatmaps: HeatmapPoint[];
  operational_health_status: 'OPTIMAL' | 'DEGRADED' | 'CRITICAL';
}

export interface ZoneTopology {
  zone_id: string;
  zone_code: string;
  zone_name: string;
  zone_type: string;
  polygon_points: [number, number][];
  risk_multiplier: number;
}

export interface CameraTopology {
  camera_id: string;
  camera_code: string;
  camera_name: string;
  position_xyz: [number, number, number];
  coverage_zones: string[];
}

export interface DigitalTwinTopology {
  warehouse_id: string;
  warehouse_name: string;
  dimensions_meters: [number, number, number];
  zones: ZoneTopology[];
  cameras: CameraTopology[];
  active_entity_count: number;
}

export interface CitationReference {
  source_type: string;
  source_id: string;
  title: string;
  confidence: number;
  snippet: string;
}

export interface AssistantQueryResponse {
  answer: string;
  grounded_citations: CitationReference[];
  is_grounded: boolean;
  confidence: number;
  suggested_followups: string[];
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
