import { QueryClient } from '@tanstack/react-query';
import { appConfig } from '../config/app';

export type RealtimeConnectionState = 'LIVE' | 'DEGRADED' | 'RECONNECTING' | 'OFFLINE';

export type RealtimeEventName =
  | 'connection_ok'
  | 'connection_error'
  | 'ALERT_CREATED'
  | 'ALERT_ACKNOWLEDGED'
  | 'INCIDENT_STATUS_CHANGED'
  | 'INCIDENT_CREATED'
  | 'VIDEO_PROGRESS'
  | 'VIDEO_COMPLETED'
  | 'SPATIAL_EVENT_CREATED';

export interface RealtimeEventEnvelope {
  event?: string;
  warehouse_id?: string | null;
  data?: Record<string, unknown>;
  timestamp?: string;
}

const INITIAL_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 15_000;

export function buildRealtimeConnectionUrl(token: string | null = null, warehouseId: string | null = null): string {
  // window.location.host includes the port (hostname alone does not) — the
  // REST API client resolves its relative baseURL against the same origin
  // (including port) the page was served from, so the WebSocket must match
  // it exactly or it silently targets the wrong port (e.g. the protocol's
  // default 80/443) whenever the app isn't served from one of those.
  const host = typeof window !== 'undefined' ? window.location.host : 'localhost:3000';
  const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const base = `${protocol}//${host}${appConfig.apiBaseUrl.replace('/api/v1', '')}`;
  const url = new URL(`${base}/api/v1/ws/events`);

  if (token) {
    url.searchParams.set('token', token);
  }
  if (warehouseId) {
    url.searchParams.set('warehouse_id', warehouseId);
  }

  return url.toString();
}

export class RealtimeSocketManager {
  private socket: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempt = 0;
  private isExplicitDisconnect = false;

  constructor(
    private readonly queryClient: QueryClient,
    private readonly getToken: () => string | null,
    private readonly getWarehouseId: () => string | null,
    private readonly setConnectionState: (state: RealtimeConnectionState) => void,
  ) {}

  public connect(): void {
    const warehouseId = this.getWarehouseId();

    if (!warehouseId) {
      this.isExplicitDisconnect = true;
      this.clearReconnectTimer();
      this.closeSocket(true);
      this.setConnectionState('OFFLINE');
      return;
    }

    const token = this.getToken();

    this.isExplicitDisconnect = false;

    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.clearReconnectTimer();

    if (this.socket) {
      this.isExplicitDisconnect = true;
      this.closeSocket(true);
      this.isExplicitDisconnect = false;
    }

    const socket = new WebSocket(buildRealtimeConnectionUrl(token, warehouseId));
    this.socket = socket;

    socket.onopen = () => {
      this.reconnectAttempt = 0;
      this.setConnectionState('LIVE');
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const payload = JSON.parse(event.data) as unknown;
        routeRealtimeEvent(payload, this.queryClient, warehouseId);
      } catch {
        this.setConnectionState('DEGRADED');
      }
    };

    socket.onerror = () => {
      this.setConnectionState('DEGRADED');
    };

    socket.onclose = () => {
      this.socket = null;

      if (this.isExplicitDisconnect) {
        return;
      }

      this.scheduleReconnect();
    };
  }

  public disconnect(): void {
    this.isExplicitDisconnect = true;
    this.clearReconnectTimer();
    this.closeSocket(true);
    this.setConnectionState('OFFLINE');
  }

  private scheduleReconnect(): void {
    if (this.isExplicitDisconnect) {
      return;
    }

    const warehouseId = this.getWarehouseId();

    if (!warehouseId) {
      this.setConnectionState('OFFLINE');
      return;
    }


    if (this.reconnectTimer) {
      return;
    }

    const delay = Math.min(INITIAL_RECONNECT_DELAY_MS * 2 ** this.reconnectAttempt, MAX_RECONNECT_DELAY_MS);
    this.reconnectAttempt += 1;
    this.setConnectionState('RECONNECTING');

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private closeSocket(suppressReconnect = false): void {
    if (!this.socket) {
      return;
    }

    const currentSocket = this.socket;
    this.socket = null;
    currentSocket.onopen = null;
    currentSocket.onmessage = null;
    currentSocket.onerror = null;
    currentSocket.onclose = null;

    if (suppressReconnect) {
      this.isExplicitDisconnect = true;
    }

    if (currentSocket.readyState !== WebSocket.CLOSED) {
      currentSocket.close();
    }
  }
}

export function routeRealtimeEvent(
  payload: unknown,
  queryClient: QueryClient,
  activeWarehouseId?: string | null,
): void {
  if (!payload || typeof payload !== 'object') {
    return;
  }

  const event = payload as RealtimeEventEnvelope;
  const eventName = typeof event.event === 'string' ? event.event : null;

  if (!eventName || !activeWarehouseId) {
    return;
  }

  if (typeof event.warehouse_id === 'string' && event.warehouse_id !== activeWarehouseId) {
    return;
  }

  if (event.warehouse_id == null) {
    return;
  }

  if (eventName === 'ALERT_CREATED' || eventName === 'ALERT_ACKNOWLEDGED') {
    void queryClient.invalidateQueries({ queryKey: ['alerts'] });
    return;
  }

  if (eventName === 'INCIDENT_CREATED' || eventName === 'INCIDENT_STATUS_CHANGED') {
    void queryClient.invalidateQueries({ queryKey: ['incidents'] });
    return;
  }

  if (eventName === 'VIDEO_COMPLETED') {
    void queryClient.invalidateQueries({ queryKey: ['videos'] });
    void queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    return;
  }

  if (eventName === 'SPATIAL_EVENT_CREATED') {
    void queryClient.invalidateQueries({ queryKey: ['digital-twin'] });
    void queryClient.invalidateQueries({ queryKey: ['spatial-events'] });
  }
}
