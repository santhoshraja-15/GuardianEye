import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { EvidencePage } from '../pages/EvidencePage';

const { mockIncidents, mockEvidence, mockReplay } = vi.hoisted(() => ({
  mockIncidents: [
    {
      id: 'inc-1',
      incident_code: 'INC-1001',
      behaviour_event_id: 'evt-1',
      warehouse_id: 'wh-1',
      zone_id: 'zone-1',
      camera_id: 'cam-1',
      title: 'Carton drop in loading bay',
      summary: 'Heavy carton dropped from lift.',
      severity: 'CRITICAL',
      status: 'DETECTED',
      assigned_to: null,
      resolved_at: null,
      resolution_notes: null,
      created_at: '2024-01-01T10:15:00Z',
      updated_at: '2024-01-01T10:15:00Z',
    },
  ],
  mockEvidence: {
    id: 'ev-1',
    incident_id: 'inc-1',
    snapshot_path: 'https://example.com/snapshot.jpg',
    clip_path: 'https://example.com/clip.mp4',
    pre_event_seconds: 3,
    post_event_seconds: 3,
    sha256_checksum: 'abc123',
    overlay_data: '{}',
  },
  mockReplay: {
    incident_id: 'inc-1',
    video_id: 'vid-1',
    behaviour_code: 'DROP',
    clip_url: 'https://example.com/clip.mp4',
    snapshot_url: 'https://example.com/snapshot.jpg',
    sha256_checksum: 'abc123',
    duration_seconds: 6,
    keyframes: [
      {
        frame_index: 1,
        timestamp_seconds: 0.5,
        image_url: 'https://example.com/frame-1.jpg',
        sha256_hash: 'hash-1',
        boxes: [{ track_id: 7, class_name: 'box', bbox_xyxy: [0, 0, 10, 10], state_label: 'DROP', is_primary: true }],
      },
    ],
  },
}));

vi.mock('../hooks/useIncidents', () => ({
  useIncidents: () => ({ data: mockIncidents }),
}));
vi.mock('../services/api', () => ({
  GuardianAPI: {
    getEvidenceForIncident: vi.fn().mockResolvedValue(mockEvidence),
    getIncidentReplay: vi.fn().mockResolvedValue(mockReplay),
  },
}));

describe('evidence page', () => {
  it('loads backend evidence and replay context without inventing prediction data', async () => {
    render(<EvidencePage />);

    await waitFor(() => {
      expect(screen.getByText('Evidence Vault & Replay')).toBeInTheDocument();
    });

    expect(screen.getByText('Observed evidence')).toBeInTheDocument();
    expect(screen.getByText('Predictions')).toBeInTheDocument();
    expect(screen.getByText('PRE-EVENT')).toBeInTheDocument();
    expect(screen.getByText('EVENT')).toBeInTheDocument();
    expect(screen.getByText('POST-EVENT')).toBeInTheDocument();
  });
});
