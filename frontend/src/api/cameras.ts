import {
  CalibrationPointPair,
  CalibrationRecord,
  CameraCreatePayload,
  CameraRecord,
  CameraUpdatePayload,
} from '../types';
import { apiClient } from './client';

export async function getCameras(warehouseId?: string): Promise<CameraRecord[]> {
  const { data } = await apiClient.get<CameraRecord[]>('/cameras/', {
    params: warehouseId ? { warehouse_id: warehouseId } : undefined,
  });
  return data;
}

export async function createCamera(payload: CameraCreatePayload): Promise<CameraRecord> {
  const { data } = await apiClient.post<CameraRecord>('/cameras/', payload);
  return data;
}

export async function updateCamera(cameraId: string, payload: CameraUpdatePayload): Promise<CameraRecord> {
  const { data } = await apiClient.patch<CameraRecord>(`/cameras/${cameraId}`, payload);
  return data;
}

export async function deleteCamera(cameraId: string): Promise<void> {
  await apiClient.delete(`/cameras/${cameraId}`);
}

export async function getCameraCalibration(cameraId: string): Promise<CalibrationRecord | null> {
  try {
    const { data } = await apiClient.get<CalibrationRecord>(`/cameras/${cameraId}/calibration`);
    return data;
  } catch {
    // 404 means "not yet calibrated" — a real, expected state, not an error to surface.
    return null;
  }
}

export async function saveCameraCalibration(
  cameraId: string,
  points: CalibrationPointPair[],
): Promise<CalibrationRecord> {
  const { data } = await apiClient.post<CalibrationRecord>(`/cameras/${cameraId}/calibration`, { points });
  return data;
}
