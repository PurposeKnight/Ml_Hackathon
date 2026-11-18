import { useState, useEffect, useCallback, useRef } from 'react';
import { checkBackendHealth } from '../api/pathsnapApi';
import { getBackendBaseUrl, setBackendBaseUrl } from '../api/client';
import { BackendStatusState } from '../types/api';

export function useBackendStatus(pollIntervalMs = 20000) {
  const [state, setState] = useState<BackendStatusState>(() => ({
    status: 'connecting',
    url: getBackendBaseUrl(),
    latencyMs: null,
    lastChecked: null,
    details: null,
  }));

  const isCheckingRef = useRef(false);

  const checkConnection = useCallback(async () => {
    if (isCheckingRef.current) return;
    isCheckingRef.current = true;

    setState((prev) => ({
      ...prev,
      status: prev.status === 'connected' ? 'connected' : 'connecting',
      url: getBackendBaseUrl(),
    }));

    try {
      const { data, latencyMs } = await checkBackendHealth();
      setState({
        status: 'connected',
        url: getBackendBaseUrl(),
        latencyMs,
        lastChecked: new Date(),
        errorMessage: undefined,
        details: data,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Backend unreachable';
      setState({
        status: 'disconnected',
        url: getBackendBaseUrl(),
        latencyMs: null,
        lastChecked: new Date(),
        errorMessage: msg,
        details: null,
      });
    } finally {
      isCheckingRef.current = false;
    }
  }, []);

  const updateUrl = useCallback((newUrl: string) => {
    setBackendBaseUrl(newUrl);
    setState((prev) => ({ ...prev, url: newUrl, status: 'connecting' }));
    checkConnection();
  }, [checkConnection]);

  useEffect(() => {
    checkConnection();

    if (pollIntervalMs > 0) {
      const timer = setInterval(() => {
        checkConnection();
      }, pollIntervalMs);
      return () => clearInterval(timer);
    }
  }, [checkConnection, pollIntervalMs]);

  return {
    ...state,
    checkConnection,
    updateUrl,
    isConnected: state.status === 'connected',
  };
}

