/**
 * GuardianEye API Client
 *
 * The frontend must use real backend data only. If the backend is unavailable or
 * the contract is not present, the request should fail loudly so the UI can show
 * a proper error state rather than fabricating production data.
 */
import { apiClient } from '../api/client';
import {
  AlertItem,
  AssistantQueryResponse,
  BehaviourEventResponse,
  DashboardSummary,
  DigitalTwinTopology,
  EvidencePackageItem,
  IncidentItem,
  IncidentReplayItem,
  TrajectorySummaryResponse,
  VideoResponse,
} from '../types';

// This module previously created its own bare axios instance with no
// Authorization header injection and no 401/refresh handling — every page
// using GuardianAPI.* was sending unauthenticated requests to a real
// backend. It now reuses the shared, correctly-configured apiClient from
// api/client.ts (same auth interceptor the api/*.ts modules and hooks use).
export const GuardianAPI = {
  async getDashboardSummary(): Promise<DashboardSummary> {
    const res = await apiClient.get<DashboardSummary>('/analytics/dashboard');
    return res.data;
  },

  async getVideos(): Promise<VideoResponse[]> {
    const res = await apiClient.get<VideoResponse[]>('/videos');
    return res.data;
  },

  async getVideoTracks(videoId: string): Promise<TrajectorySummaryResponse> {
    const res = await apiClient.get<TrajectorySummaryResponse>(`/tracks/${videoId}`);
    return res.data;
  },

  async getBehavioursForVideo(videoId: string): Promise<BehaviourEventResponse[]> {
    const res = await apiClient.get<BehaviourEventResponse[]>(`/behaviours/video/${videoId}`);
    return res.data;
  },

  async getIncidents(): Promise<IncidentItem[]> {
    const res = await apiClient.get<IncidentItem[]>('/incidents');
    return res.data;
  },

  async getEvidenceForIncident(incidentId: string): Promise<EvidencePackageItem> {
    const res = await apiClient.get<EvidencePackageItem>(`/evidence/incident/${incidentId}`);
    return res.data;
  },

  async getIncidentReplay(incidentId: string): Promise<IncidentReplayItem> {
    const res = await apiClient.get<IncidentReplayItem>(`/replay/${incidentId}`);
    return res.data;
  },

  async updateIncidentStatus(payload: {
    incident_id: string;
    new_status: string;
    change_reason: string;
    assigned_to?: string;
    resolution_notes?: string;
  }): Promise<IncidentItem> {
    const res = await apiClient.post<IncidentItem>('/incidents/status', payload);
    return res.data;
  },

  async getAlerts(): Promise<AlertItem[]> {
    const res = await apiClient.get<AlertItem[]>('/alerts');
    return res.data;
  },

  async acknowledgeAlert(alertId: string): Promise<AlertItem> {
    const res = await apiClient.post<AlertItem>('/alerts/acknowledge', { alert_id: alertId });
    return res.data;
  },

  async getDigitalTwinTopology(): Promise<DigitalTwinTopology> {
    const res = await apiClient.get<DigitalTwinTopology>('/digital-twin/topology');
    return res.data;
  },

  async queryAssistant(query: string): Promise<AssistantQueryResponse> {
    const res = await apiClient.post<AssistantQueryResponse>('/assistant/chat', { query });
    return res.data;
  },

  async submitHumanReview(payload: {
    incident_id: string;
    review_outcome: string;
    corrected_behaviour_code?: string;
    reviewer_notes?: string;
    is_curated_for_training?: boolean;
  }) {
    const res = await apiClient.post('/reviews/', payload);
    return res.data;
  },

  async getIncidentReviews(incidentId: string) {
    const res = await apiClient.get(`/reviews/incident/${incidentId}`);
    return res.data;
  },

  async getPreventionRules() {
    const res = await apiClient.get('/prevention/rules');
    return res.data;
  },

  async getRecommendations() {
    const res = await apiClient.get('/prevention/recommendations');
    return res.data;
  },

  async getRootCauses() {
    const res = await apiClient.get('/prevention/root-causes');
    return res.data;
  },

  async getModels() {
    const res = await apiClient.get('/learning/models');
    return res.data;
  },

  async getDatasets() {
    const res = await apiClient.get('/learning/datasets');
    return res.data;
  },

  async processVideo(videoId: string) {
    const res = await apiClient.post(`/videos/${videoId}/process`);
    return res.data;
  },

  async uploadVideo(file: File, cameraId?: string, autoProcess = true) {
    const formData = new FormData();
    formData.append('file', file);
    if (cameraId) formData.append('camera_id', cameraId);
    formData.append('auto_process', String(autoProcess));

    const res = await apiClient.post('/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
};

export const api = GuardianAPI;


