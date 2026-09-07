import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { LiveStreamsPage } from '../pages/LiveStreamsPage';

const { mockVideos, mockTracks, mockBehaviours, mockAlerts, mockIncidents } = vi.hoisted(() => ({
  mockVideos: [
    {
      id: 'vid-001',
      filename: 'dock-01-live.mp4',
      camera_id: 'cam-01',
      storage_path: '/storage/videos/dock-01-live.mp4',
      file_size_bytes: 2048000,
      duration_seconds: 16.5,
      fps: 30,
      width: 1920,
      height: 1080,
      codec: 'h264',
      checksum_sha256: 'abc123',
      status: 'PROCESSED',
      created_at: '2026-09-06T10:00:00Z',
      updated_at: '2026-09-06T10:01:00Z',
      processing_jobs: [],
    },
    {
      id: 'vid-002',
      filename: 'dock-02-live.mp4',
      camera_id: 'cam-02',
      storage_path: '/storage/videos/dock-02-live.mp4',
      file_size_bytes: 1800000,
      duration_seconds: 14.2,
      fps: 30,
      width: 1920,
      height: 1080,
      codec: 'h264',
      checksum_sha256: 'def456',
      status: 'PROCESSED',
      created_at: '2026-09-06T10:00:10Z',
      updated_at: '2026-09-06T10:01:10Z',
      processing_jobs: [],
    },
  ],
  mockTracks: {
    video_id: 'vid-001',
    total_tracks: 1,
    tracks: [
      {
        id: 'track-14',
        video_id: 'vid-001',
        track_id: 14,
        class_name: 'person',
        confidence: 0.97,
        first_frame: 12,
        last_frame: 48,
        duration_seconds: 1.2,
        max_velocity: 4.2,
        trajectory_points: [
          {
            frame_number: 12,
            timestamp_seconds: 0.4,
            bbox_xyxy: [0.22, 0.28, 0.52, 0.63],
            centroid_xy: [0.35, 0.42],
            velocity_xy: [2.1, 1.8],
            confidence: 0.95,
            zone_id: 'dock-01',
          },
        ],
      },
    ],
  },
  mockBehaviours: [
    {
      id: 'beh-1',
      video_id: 'vid-001',
      behaviour_type: 'DROP',
      severity: 'HIGH',
      start_frame: 20,
      end_frame: 40,
      start_time_seconds: 0.7,
      end_time_seconds: 1.3,
      duration_seconds: 0.6,
      confidence: 0.9,
      description: 'Heavy object drop near loading dock',
      evidence: {
        trigger_rule: 'drop',
        primary_entity_id: 14,
        primary_class: 'person',
        peak_velocity_px_s: 4.2,
        impact_deceleration: 0.8,
        duration_seconds: 0.6,
        zone_code: 'dock-01',
      },
      keyframe_indices: [20, 30],
    },
  ],
  mockAlerts: [
    {
      id: 'alert-1',
      behaviour_event_id: 'beh-1',
      zone_id: 'dock-01',
      alert_level: 'HIGH',
      message: 'Heavy object drop detected',
      status: 'OPEN',
      deduplication_key: 'dedupe-1',
      created_at: '2026-09-06T10:15:00Z',
    },
  ],
  mockIncidents: [
    {
      id: 'inc-1',
      incident_code: 'INC-1001',
      behaviour_event_id: 'beh-1',
      warehouse_id: 'wh-01',
      zone_id: 'dock-01',
      camera_id: 'cam-01',
      title: 'Drop incident in Dock 01',
      summary: 'Heavy object drop observed near loading dock.',
      severity: 'HIGH',
      status: 'DETECTED',
      assigned_to: null,
      resolved_at: null,
      resolution_notes: null,
      created_at: '2026-09-06T10:14:00Z',
      updated_at: '2026-09-06T10:14:00Z',
    },
  ],
}));

vi.mock('../services/api', () => ({
  GuardianAPI: {
    getVideos: vi.fn().mockResolvedValue(mockVideos),
    getVideoTracks: vi.fn().mockResolvedValue(mockTracks),
    getBehavioursForVideo: vi.fn().mockResolvedValue(mockBehaviours),
  },
}));
vi.mock('../hooks/useAlerts', () => ({
  useAlerts: () => ({ data: mockAlerts }),
}));
vi.mock('../hooks/useIncidents', () => ({
  useIncidents: () => ({ data: mockIncidents }),
}));

describe('live monitoring page', () => {
  it('renders the selected camera, real track data, and behaviour intelligence from the backend', async () => {
    render(<LiveStreamsPage />);

    await waitFor(() => {
      expect(screen.getByText('Multi-Camera Live Intelligence Matrix')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Camera Rail')).toBeInTheDocument();
      expect(screen.getByText('Selected Camera')).toBeInTheDocument();
      expect(screen.getAllByText(/Track #14/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/DROP/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Heavy object drop detected/i).length).toBeGreaterThan(0);
    });
  });
});
