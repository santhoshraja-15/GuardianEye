import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Camera as CameraIcon, CheckCircle2, Crosshair, Plus, Radar, Trash2 } from 'lucide-react';
import { appConfig } from '../config/app';
import {
  createCamera,
  deleteCamera,
  getCameraCalibration,
  getCameras,
  saveCameraCalibration,
  updateCamera,
} from '../api/cameras';
import { useDigitalTwinTopology } from '../hooks/useDigitalTwinTopology';
import { GuardianAPI } from '../services/api';
import { CalibrationRecord, CameraRecord, VideoResponse } from '../types';

interface DraftPoint {
  videoPoint: [number, number]; // normalized 0-1, clicked on the reference frame
  worldX: string;
  worldY: string;
}

/**
 * Camera registry + calibration workflow — the admin-facing half of the
 * "MOST IMPORTANT architectural requirement" (video pixel <-> warehouse
 * meters transform). The backend (Camera CRUD, calibration_service,
 * coordinate_transform.solve_homography) already existed; this page is
 * what was still missing: somewhere an operator can actually register
 * a camera, position it, and calibrate it.
 *
 * Calibration flow: pick a camera, pick one of its videos as a visual
 * reference, click points on the paused frame, enter the matching
 * warehouse-meter coordinate for each, save once >= 4 pairs exist. The
 * backend solves the homography and reports its own reprojection error
 * — this page never claims a calibration is good, only shows what the
 * math actually measured.
 */
export const CalibrationPage: React.FC = () => {
  const { data: topology } = useDigitalTwinTopology();
  const [cameras, setCameras] = useState<CameraRecord[]>([]);
  const [videos, setVideos] = useState<VideoResponse[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState<string | null>(null);
  const [calibration, setCalibration] = useState<CalibrationRecord | null>(null);
  const [draftPoints, setDraftPoints] = useState<DraftPoint[]>([]);
  const [showNewCameraForm, setShowNewCameraForm] = useState(false);
  const [newCameraName, setNewCameraName] = useState('');
  const [newCameraCode, setNewCameraCode] = useState('');
  const [positionDraft, setPositionDraft] = useState({ x: '', y: '', orientation: '', fov: '' });
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const refreshCameras = async () => {
    const list = await getCameras();
    setCameras(list);
    return list;
  };

  useEffect(() => {
    refreshCameras().then((list) => {
      if (!selectedCameraId && list.length > 0) setSelectedCameraId(list[0].id);
    });
    GuardianAPI.getVideos().then(setVideos);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedCamera = useMemo(
    () => cameras.find((camera) => camera.id === selectedCameraId) ?? null,
    [cameras, selectedCameraId],
  );

  const referenceVideo = useMemo(
    () => videos.find((video) => video.camera_id === selectedCameraId) ?? null,
    [videos, selectedCameraId],
  );

  useEffect(() => {
    if (!selectedCameraId) {
      setCalibration(null);
      return;
    }
    setDraftPoints([]);
    setSaveState('idle');
    setErrorMessage(null);
    getCameraCalibration(selectedCameraId).then(setCalibration);
  }, [selectedCameraId]);

  useEffect(() => {
    if (!selectedCamera) return;
    setPositionDraft({
      x: selectedCamera.is_positioned ? String(selectedCamera.location_x) : '',
      y: selectedCamera.is_positioned ? String(selectedCamera.location_y) : '',
      orientation: selectedCamera.orientation_degrees != null ? String(selectedCamera.orientation_degrees) : '',
      fov: String(selectedCamera.fov_degrees),
    });
  }, [selectedCamera]);

  const handleVideoClick = (event: React.MouseEvent<HTMLVideoElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const nx = (event.clientX - rect.left) / rect.width;
    const ny = (event.clientY - rect.top) / rect.height;
    setDraftPoints((prev) => [...prev, { videoPoint: [nx, ny], worldX: '', worldY: '' }]);
  };

  const updateDraftPoint = (index: number, field: 'worldX' | 'worldY', value: string) => {
    setDraftPoints((prev) => prev.map((point, i) => (i === index ? { ...point, [field]: value } : point)));
  };

  const removeDraftPoint = (index: number) => {
    setDraftPoints((prev) => prev.filter((_, i) => i !== index));
  };

  const readyPoints = draftPoints.filter((p) => p.worldX.trim() !== '' && p.worldY.trim() !== '');
  const canSaveCalibration = selectedCameraId && readyPoints.length >= 4;

  const handleSaveCalibration = async () => {
    if (!selectedCameraId || !canSaveCalibration) return;
    setSaveState('saving');
    setErrorMessage(null);
    try {
      const record = await saveCameraCalibration(
        selectedCameraId,
        readyPoints.map((p) => ({
          video_point: p.videoPoint,
          world_point: [Number(p.worldX), Number(p.worldY)],
        })),
      );
      setCalibration(record);
      setDraftPoints([]);
      setSaveState('saved');
      await refreshCameras();
    } catch (err) {
      setSaveState('error');
      setErrorMessage(err instanceof Error ? err.message : 'Calibration could not be solved from these points.');
    }
  };

  const handleCreateCamera = async () => {
    if (!newCameraName.trim() || !newCameraCode.trim() || !topology) return;
    const created = await createCamera({
      warehouse_id: topology.warehouse_id,
      name: newCameraName.trim(),
      camera_code: newCameraCode.trim(),
    });
    setNewCameraName('');
    setNewCameraCode('');
    setShowNewCameraForm(false);
    await refreshCameras();
    setSelectedCameraId(created.id);
  };

  const handleDeleteCamera = async (cameraId: string) => {
    await deleteCamera(cameraId);
    if (selectedCameraId === cameraId) setSelectedCameraId(null);
    await refreshCameras();
  };

  const handleSavePosition = async () => {
    if (!selectedCameraId) return;
    const payload: Record<string, number> = {};
    if (positionDraft.x !== '') payload.location_x = Number(positionDraft.x);
    if (positionDraft.y !== '') payload.location_y = Number(positionDraft.y);
    if (positionDraft.orientation !== '') payload.orientation_degrees = Number(positionDraft.orientation);
    if (positionDraft.fov !== '') payload.fov_degrees = Number(positionDraft.fov);
    await updateCamera(selectedCameraId, payload);
    await refreshCameras();
  };

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h1 className="text-xl font-bold text-[#18243A] tracking-tight">Camera Registry &amp; Calibration</h1>
        <p className="text-xs text-[#6F7F98]">
          Register cameras, set their warehouse position, and solve a real video-pixel-to-warehouse-meters
          homography from operator-supplied point pairs — the one piece of the spatial pipeline that can never
          be inferred automatically.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-panel rounded-xl p-4 space-y-3 lg:sticky lg:top-24 lg:self-start">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#6F7F98]">
              <CameraIcon className="w-3.5 h-3.5 text-[#2F52D6]" />
              Cameras
            </div>
            <button
              type="button"
              onClick={() => setShowNewCameraForm((v) => !v)}
              className="inline-flex items-center gap-1 rounded-full border border-[#5D87FF] bg-[#5D87FF]/10 px-2 py-1 text-[10px] font-semibold text-[#2F52D6]"
            >
              <Plus className="w-3 h-3" /> Add
            </button>
          </div>

          {showNewCameraForm && (
            <div className="rounded-lg border border-[#E9EDF2] bg-[#F8FAFC] p-3 space-y-2">
              <input
                value={newCameraName}
                onChange={(e) => setNewCameraName(e.target.value)}
                placeholder="Camera name"
                className="w-full rounded border border-[#E9EDF2] bg-white px-2 py-1.5 text-xs text-[#18243A]"
              />
              <input
                value={newCameraCode}
                onChange={(e) => setNewCameraCode(e.target.value.toUpperCase())}
                placeholder="CAM-CODE-01"
                className="w-full rounded border border-[#E9EDF2] bg-white px-2 py-1.5 text-xs text-[#18243A]"
              />
              <button
                type="button"
                onClick={handleCreateCamera}
                disabled={!topology}
                className="w-full rounded-lg bg-[#5D87FF] px-3 py-1.5 text-[11px] font-semibold text-white disabled:opacity-50"
              >
                {topology ? 'Register camera' : 'Loading warehouse…'}
              </button>
            </div>
          )}

          <div className="ge-scroll-panel space-y-2 max-h-[calc(100vh-360px)] pr-1">
            {cameras.map((camera) => (
              <button
                key={camera.id}
                type="button"
                onClick={() => setSelectedCameraId(camera.id)}
                className={`w-full rounded-lg border p-3 text-left transition ${
                  selectedCameraId === camera.id
                    ? 'border-[#5D87FF] bg-[#5D87FF]/10'
                    : 'border-[#E9EDF2] bg-[#F8FAFC] hover:border-[#CBD5E1]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#18243A]">{camera.camera_code}</span>
                  {camera.is_calibrated ? (
                    <span className="inline-flex items-center gap-1 rounded border border-[rgba(21,128,61,0.25)] bg-[rgba(21,128,61,0.08)] px-1.5 py-0.5 text-[9px] text-[#15803d]">
                      <CheckCircle2 className="w-2.5 h-2.5" /> calibrated
                    </span>
                  ) : (
                    <span className="rounded border border-[#E9EDF2] bg-[#F1F5F9] px-1.5 py-0.5 text-[9px] text-[#9DAFC5]">
                      uncalibrated
                    </span>
                  )}
                </div>
                <div className="mt-1 text-[11px] text-[#334155]">{camera.name}</div>
                <div className="mt-1 text-[10px] text-[#9DAFC5]">
                  {camera.is_positioned ? `(${camera.location_x.toFixed(1)}, ${camera.location_y.toFixed(1)}) m` : 'not positioned'}
                </div>
              </button>
            ))}
            {cameras.length === 0 && (
              <div className="text-xs text-[#9DAFC5]">No cameras registered yet.</div>
            )}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          {!selectedCamera ? (
            <div className="glass-panel rounded-xl p-8 text-center text-xs text-[#6F7F98]">
              Select or register a camera to configure its position and calibration.
            </div>
          ) : (
            <>
              <div className="glass-panel rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#6F7F98]">
                    <Radar className="w-3.5 h-3.5 text-[#2F52D6]" />
                    Position &amp; orientation
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteCamera(selectedCamera.id)}
                    className="inline-flex items-center gap-1 text-[10px] text-[#9a3412] hover:text-[#7c2d12]"
                  >
                    <Trash2 className="w-3 h-3" /> Remove camera
                  </button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  <label className="text-[10px] text-[#6F7F98]">
                    X (m)
                    <input
                      value={positionDraft.x}
                      onChange={(e) => setPositionDraft((p) => ({ ...p, x: e.target.value }))}
                      className="mt-1 w-full rounded border border-[#E9EDF2] bg-white px-2 py-1 text-xs"
                    />
                  </label>
                  <label className="text-[10px] text-[#6F7F98]">
                    Y (m)
                    <input
                      value={positionDraft.y}
                      onChange={(e) => setPositionDraft((p) => ({ ...p, y: e.target.value }))}
                      className="mt-1 w-full rounded border border-[#E9EDF2] bg-white px-2 py-1 text-xs"
                    />
                  </label>
                  <label className="text-[10px] text-[#6F7F98]">
                    Orientation (°)
                    <input
                      value={positionDraft.orientation}
                      onChange={(e) => setPositionDraft((p) => ({ ...p, orientation: e.target.value }))}
                      className="mt-1 w-full rounded border border-[#E9EDF2] bg-white px-2 py-1 text-xs"
                    />
                  </label>
                  <label className="text-[10px] text-[#6F7F98]">
                    FOV (°)
                    <input
                      value={positionDraft.fov}
                      onChange={(e) => setPositionDraft((p) => ({ ...p, fov: e.target.value }))}
                      className="mt-1 w-full rounded border border-[#E9EDF2] bg-white px-2 py-1 text-xs"
                    />
                  </label>
                </div>
                <button
                  type="button"
                  onClick={handleSavePosition}
                  className="rounded-lg border border-[#5D87FF] bg-[#5D87FF]/10 px-3 py-1.5 text-[11px] font-semibold text-[#2F52D6]"
                >
                  Save position
                </button>
              </div>

              <div className="glass-panel rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#6F7F98]">
                    <Crosshair className="w-3.5 h-3.5 text-[#2F52D6]" />
                    Calibration
                  </div>
                  {calibration && (
                    <span className="text-[10px] text-[#6F7F98]">
                      reprojection error: {calibration.reprojection_error?.toFixed(4) ?? 'n/a'} (normalized units) ·
                      calibrated {new Date(calibration.calibrated_at).toLocaleString()}
                    </span>
                  )}
                </div>

                {!referenceVideo ? (
                  <div className="rounded-lg border border-dashed border-[#E9EDF2] bg-[#F8FAFC] p-5 text-xs text-[#9DAFC5]">
                    No processed video is assigned to this camera yet — a reference frame is needed to click
                    calibration points on. Assign a video to this camera at upload time first.
                  </div>
                ) : (
                  <>
                    <p className="text-[11px] text-[#6F7F98]">
                      Click at least 4 points on the frame below, then enter the real warehouse (x, y) in meters
                      each one corresponds to.
                    </p>
                    <div className="relative overflow-hidden rounded-xl border border-[#E9EDF2] bg-black">
                      <video
                        ref={videoRef}
                        src={`${appConfig.apiBaseUrl}/videos/${referenceVideo.id}/stream`}
                        className="block w-full cursor-crosshair"
                        onClick={handleVideoClick}
                        muted
                      />
                      <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                        {draftPoints.map((point, index) => (
                          <g key={index}>
                            <circle cx={point.videoPoint[0] * 100} cy={point.videoPoint[1] * 100} r={1.2} fill="#facc15" stroke="#78350f" strokeWidth={0.3} />
                            <text x={point.videoPoint[0] * 100 + 1.5} y={point.videoPoint[1] * 100} fill="#facc15" fontSize={3}>
                              {index + 1}
                            </text>
                          </g>
                        ))}
                      </svg>
                    </div>

                    <div className="space-y-2">
                      {draftPoints.map((point, index) => (
                        <div key={index} className="flex items-center gap-2 rounded border border-[#E9EDF2] bg-[#F8FAFC] px-2 py-1.5">
                          <span className="text-[10px] text-[#9DAFC5] w-6">#{index + 1}</span>
                          <span className="text-[10px] text-[#6F7F98] w-28">
                            video ({point.videoPoint[0].toFixed(2)}, {point.videoPoint[1].toFixed(2)})
                          </span>
                          <input
                            value={point.worldX}
                            onChange={(e) => updateDraftPoint(index, 'worldX', e.target.value)}
                            placeholder="world x (m)"
                            className="w-24 rounded border border-[#E9EDF2] bg-white px-2 py-1 text-[11px]"
                          />
                          <input
                            value={point.worldY}
                            onChange={(e) => updateDraftPoint(index, 'worldY', e.target.value)}
                            placeholder="world y (m)"
                            className="w-24 rounded border border-[#E9EDF2] bg-white px-2 py-1 text-[11px]"
                          />
                          <button type="button" onClick={() => removeDraftPoint(index)} className="text-[#9a3412]">
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                      {draftPoints.length === 0 && (
                        <div className="text-[11px] text-[#9DAFC5]">No points clicked yet.</div>
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={handleSaveCalibration}
                      disabled={!canSaveCalibration || saveState === 'saving'}
                      className="w-full rounded-lg bg-[#5D87FF] px-3 py-2 text-[11px] font-semibold text-white disabled:opacity-40"
                    >
                      {saveState === 'saving'
                        ? 'Solving homography…'
                        : `Save calibration (${readyPoints.length}/4 minimum points ready)`}
                    </button>
                    {saveState === 'error' && (
                      <div className="text-[11px] text-[#9a3412]">{errorMessage}</div>
                    )}
                    {saveState === 'saved' && (
                      <div className="text-[11px] text-[#15803d]">
                        Calibration saved — reprojection error {calibration?.reprojection_error?.toFixed(4)}.
                      </div>
                    )}
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
