import { QueryClient } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { RealtimeSocketManager, buildRealtimeConnectionUrl, routeRealtimeEvent } from '../services/realtime';
import { useAppStore } from '../stores/app-store';

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  public readyState = 0;
  public onopen: ((event?: Event) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event?: Event) => void) | null = null;
  public onclose: ((event?: CloseEvent) => void) | null = null;
  public close = vi.fn(() => {
    this.readyState = 3;
    this.onclose?.(new CloseEvent('close'));
  });

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
  }
}

describe('realtime websocket contract', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useAppStore.setState({ connectionState: 'LIVE' });
    MockWebSocket.instances = [];
    vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket);
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('builds a websocket URL with the JWT and selected warehouse', () => {
    const url = buildRealtimeConnectionUrl('token-123', 'warehouse-01');

    expect(url).toContain('ws://');
    expect(url).toContain('token=token-123');
    expect(url).toContain('warehouse_id=warehouse-01');
    expect(url).toContain('/api/v1/ws/events');
  });

  it('preserves a non-default port from the page origin (regression: hostname alone drops it)', () => {
    vi.stubGlobal('location', {
      ...window.location,
      hostname: 'localhost',
      host: 'localhost:3000',
      protocol: 'http:',
    });

    const url = buildRealtimeConnectionUrl('token-123', 'warehouse-01');
    expect(url).toContain('ws://localhost:3000/api/v1/ws/events');
  });

  it('1. initial connection: opens a websocket once authenticated with a warehouse selected', () => {
    const manager = new RealtimeSocketManager(new QueryClient(), () => 'token-123', () => 'warehouse-01', vi.fn());

    manager.connect();

    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toContain('token=token-123');
    expect(MockWebSocket.instances[0].url).toContain('warehouse_id=warehouse-01');
  });

  it('2. connection_ok: sets connection state to LIVE when the socket opens', () => {
    const states: string[] = [];
    const manager = new RealtimeSocketManager(
      new QueryClient(),
      () => 'token-123',
      () => 'warehouse-01',
      (state) => states.push(state),
    );

    manager.connect();
    MockWebSocket.instances[0].readyState = 1;
    MockWebSocket.instances[0].onopen?.(new Event('open'));

    expect(states).toContain('LIVE');
  });

  it('3. connection_error: sets connection state to DEGRADED', () => {
    const states: string[] = [];
    const manager = new RealtimeSocketManager(new QueryClient(), () => 'token-123', () => 'warehouse-01', (state) => states.push(state));

    manager.connect();
    MockWebSocket.instances[0].onerror?.(new Event('error'));

    expect(states).toContain('DEGRADED');
  });

  it('4. ALERT_CREATED: invalidates the alerts query', () => {
    const queryClient = new QueryClient();
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');

    routeRealtimeEvent({
      event: 'ALERT_CREATED',
      warehouse_id: 'warehouse-01',
      data: { alert_id: 'alert-1' },
    }, queryClient, 'warehouse-01');

    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['alerts'] });
  });

  it('5. ALERT_ACKNOWLEDGED: invalidates the alerts query', () => {
    const queryClient = new QueryClient();
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');

    routeRealtimeEvent({
      event: 'ALERT_ACKNOWLEDGED',
      warehouse_id: 'warehouse-01',
      data: { alert_id: 'alert-1' },
    }, queryClient, 'warehouse-01');

    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['alerts'] });
  });

  it('6. INCIDENT_CREATED: invalidates the incidents query', () => {
    const queryClient = new QueryClient();
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');

    routeRealtimeEvent({
      event: 'INCIDENT_CREATED',
      warehouse_id: 'warehouse-01',
      data: { incident_id: 'incident-1' },
    }, queryClient, 'warehouse-01');

    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['incidents'] });
  });

  it('7. INCIDENT_STATUS_CHANGED: invalidates the incidents query', () => {
    const queryClient = new QueryClient();
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');

    routeRealtimeEvent({
      event: 'INCIDENT_STATUS_CHANGED',
      warehouse_id: 'warehouse-01',
      data: { incident_id: 'incident-1', from_status: 'DETECTED', to_status: 'ALERTED' },
    }, queryClient, 'warehouse-01');

    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['incidents'] });
  });

  it('8. unknown event: ignored without crashing or invalidating', () => {
    const queryClient = new QueryClient();
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');

    expect(() => routeRealtimeEvent({
      event: 'UNKNOWN_EVENT',
      warehouse_id: 'warehouse-01',
      data: {},
    }, queryClient, 'warehouse-01')).not.toThrow();
    expect(() => routeRealtimeEvent({} as never, queryClient, 'warehouse-01')).not.toThrow();

    expect(invalidate).not.toHaveBeenCalled();
  });

  it('9. malformed JSON: ignored without crashing the socket handler', () => {
    const queryClient = new QueryClient();
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');
    const manager = new RealtimeSocketManager(queryClient, () => 'token-123', () => 'warehouse-01', () => undefined);

    manager.connect();

    expect(() => MockWebSocket.instances[0].onmessage?.({ data: '{bad json' } as MessageEvent)).not.toThrow();
    expect(invalidate).not.toHaveBeenCalled();
  });

  it('10. warehouse mismatch: events for a different warehouse are ignored', () => {
    const queryClient = new QueryClient();
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');

    routeRealtimeEvent({
      event: 'ALERT_CREATED',
      warehouse_id: 'warehouse-02',
      data: { alert_id: 'alert-1' },
    }, queryClient, 'warehouse-01');

    routeRealtimeEvent({
      event: 'INCIDENT_STATUS_CHANGED',
      warehouse_id: 'warehouse-02',
      data: { incident_id: 'incident-1', from_status: 'DETECTED', to_status: 'ALERTED' },
    }, queryClient, 'warehouse-01');

    expect(invalidate).not.toHaveBeenCalled();
  });

  it('10b. warehouse mismatch: no selected warehouse means no state mutation', () => {
    const queryClient = new QueryClient();
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');

    routeRealtimeEvent({
      event: 'ALERT_CREATED',
      warehouse_id: 'warehouse-01',
      data: { alert_id: 'alert-1' },
    }, queryClient, null);

    expect(invalidate).not.toHaveBeenCalled();
  });

  it('11. warehouse switch: closes the previous socket', () => {
    let currentWarehouse = 'warehouse-01';
    const manager = new RealtimeSocketManager(
      new QueryClient(),
      () => 'token-123',
      () => currentWarehouse,
      vi.fn(),
    );

    manager.connect();
    const firstSocket = MockWebSocket.instances[0];
    expect(firstSocket).toBeDefined();

    currentWarehouse = 'warehouse-02';
    manager.connect();

    expect(firstSocket.close).toHaveBeenCalledTimes(1);
  });

  it('12. warehouse switch: opens a new connection scoped to the new warehouse', () => {
    let currentWarehouse = 'warehouse-01';
    const manager = new RealtimeSocketManager(
      new QueryClient(),
      () => 'token-123',
      () => currentWarehouse,
      vi.fn(),
    );

    manager.connect();
    currentWarehouse = 'warehouse-02';
    manager.connect();

    expect(MockWebSocket.instances).toHaveLength(2);
    expect(MockWebSocket.instances[1].url).toContain('warehouse_id=warehouse-02');
  });

  it('13. logout: closes the socket', () => {
    const manager = new RealtimeSocketManager(
      new QueryClient(),
      () => 'token-123',
      () => 'warehouse-01',
      vi.fn(),
    );

    manager.connect();
    expect(MockWebSocket.instances).toHaveLength(1);

    manager.disconnect();

    expect(MockWebSocket.instances[0].close).toHaveBeenCalledTimes(1);
  });

  it('14. open access: socket connects without token, and no socket is created without warehouse', () => {
    const noWarehouseManager = new RealtimeSocketManager(new QueryClient(), () => null, () => null, vi.fn());
    noWarehouseManager.connect();
    expect(MockWebSocket.instances).toHaveLength(0);

    const openAccessManager = new RealtimeSocketManager(new QueryClient(), () => null, () => 'warehouse-01', vi.fn());
    openAccessManager.connect();
    expect(MockWebSocket.instances).toHaveLength(1);
  });


  it('15. unexpected close: triggers an automatic reconnect', () => {
    const states: string[] = [];
    const manager = new RealtimeSocketManager(
      new QueryClient(),
      () => 'token-123',
      () => 'warehouse-01',
      (state) => states.push(state),
    );

    manager.connect();
    expect(MockWebSocket.instances).toHaveLength(1);

    MockWebSocket.instances[0].onclose?.(new CloseEvent('close'));
    expect(states).toContain('RECONNECTING');

    vi.advanceTimersByTime(1000);
    expect(MockWebSocket.instances).toHaveLength(2);
  });

  it('16. reconnect: does not create duplicate sockets', () => {
    const manager = new RealtimeSocketManager(new QueryClient(), () => 'token-123', () => 'warehouse-01', vi.fn());

    manager.connect();
    MockWebSocket.instances[0].onclose?.(new CloseEvent('close'));

    // Advance in two partial steps across the single scheduled delay - only one
    // reconnect attempt should fire, never more than one socket for one close.
    vi.advanceTimersByTime(500);
    vi.advanceTimersByTime(500);

    expect(MockWebSocket.instances).toHaveLength(2);
  });

  it('17. reconnect: uses the current token', () => {
    let currentToken = 'token-123';
    const manager = new RealtimeSocketManager(
      new QueryClient(),
      () => currentToken,
      () => 'warehouse-01',
      vi.fn(),
    );

    manager.connect();
    currentToken = 'token-456';
    MockWebSocket.instances[0].onclose?.(new CloseEvent('close'));
    vi.advanceTimersByTime(1000);

    expect(MockWebSocket.instances).toHaveLength(2);
    expect(MockWebSocket.instances[1].url).toContain('token=token-456');
  });

  it('18. reconnect: uses the current warehouse', () => {
    let currentWarehouse = 'warehouse-01';
    const manager = new RealtimeSocketManager(
      new QueryClient(),
      () => 'token-123',
      () => currentWarehouse,
      vi.fn(),
    );

    manager.connect();
    currentWarehouse = 'warehouse-02';
    MockWebSocket.instances[0].onclose?.(new CloseEvent('close'));
    vi.advanceTimersByTime(1000);

    expect(MockWebSocket.instances).toHaveLength(2);
    expect(MockWebSocket.instances[1].url).toContain('warehouse_id=warehouse-02');
  });

  it('19. explicit disconnect: prevents further reconnect attempts', () => {
    const manager = new RealtimeSocketManager(
      new QueryClient(),
      () => 'token-123',
      () => 'warehouse-01',
      vi.fn(),
    );

    manager.connect();
    manager.disconnect();

    // A close event arriving after an explicit disconnect must not schedule a reconnect.
    MockWebSocket.instances[0].onclose?.(new CloseEvent('close'));
    vi.advanceTimersByTime(30_000);

    expect(MockWebSocket.instances).toHaveLength(1);
  });

  it('20. explicit disconnect: clears the pending reconnect timer', () => {
    const manager = new RealtimeSocketManager(new QueryClient(), () => 'token-123', () => 'warehouse-01', vi.fn());

    manager.connect();
    MockWebSocket.instances[0].onclose?.(new CloseEvent('close'));
    expect(vi.getTimerCount()).toBeGreaterThan(0);

    manager.disconnect();
    expect(vi.getTimerCount()).toBe(0);

    vi.advanceTimersByTime(30_000);
    expect(MockWebSocket.instances).toHaveLength(1);
  });

  it('reconnect backoff is exponential and bounded by the configured maximum delay', () => {
    const manager = new RealtimeSocketManager(new QueryClient(), () => 'token-123', () => 'warehouse-01', vi.fn());
    manager.connect();

    // Each successive unexpected close (without an intervening successful open,
    // so reconnectAttempt never resets) should wait roughly double the previous
    // delay, up to the configured cap - never firing early and never retrying
    // on every tick (which would be a reconnect storm).
    const expectedDelaysMs = [1000, 2000, 4000, 8000, 15000, 15000];

    for (const delay of expectedDelaysMs) {
      const beforeCount = MockWebSocket.instances.length;
      MockWebSocket.instances[beforeCount - 1].onclose?.(new CloseEvent('close'));

      vi.advanceTimersByTime(delay - 1);
      expect(MockWebSocket.instances).toHaveLength(beforeCount);

      vi.advanceTimersByTime(1);
      expect(MockWebSocket.instances).toHaveLength(beforeCount + 1);
    }
  });
});
