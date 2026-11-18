/**
 * HTTP Client for PathSnap Laptop 2 -> Laptop 1 communication
 */

const STORAGE_KEY = 'pathsnap_backend_url';
let memoryUrlOverride: string | null = null;

export function getBackendBaseUrl(): string {
  if (memoryUrlOverride) {
    return memoryUrlOverride;
  }

  // Allow evaluator or user to override dynamically via UI
  try {
    const stored = typeof window !== 'undefined' && window.localStorage ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (stored && stored.trim() !== '') {
      return stored.trim().replace(/\/+$/, '');
    }
  } catch {
    // LocalStorage inaccessible
  }

  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim() !== '') {
    return envUrl.trim().replace(/\/+$/, '');
  }

  return 'http://localhost:8000';
}

export function setBackendBaseUrl(url: string): void {
  const sanitized = url.trim().replace(/\/+$/, '');
  memoryUrlOverride = sanitized;
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(STORAGE_KEY, sanitized);
    }
  } catch {
    // LocalStorage inaccessible
  }
}

export function resetBackendBaseUrl(): void {
  memoryUrlOverride = null;
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // LocalStorage inaccessible
  }
}

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

export class ApiError extends Error {
  statusCode?: number;
  data?: unknown;

  constructor(message: string, statusCode?: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.data = data;
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { timeoutMs = 15000, ...fetchOptions } = options;
  const baseUrl = getBackendBaseUrl();
  const url = `${baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  // Link signal with any external signal provided
  if (fetchOptions.signal) {
    fetchOptions.signal.addEventListener('abort', () => controller.abort());
  }

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...fetchOptions.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
      let errorData: unknown = null;
      try {
        errorData = await response.json();
        if (typeof errorData === 'object' && errorData !== null) {
          const dict = errorData as Record<string, unknown>;
          if (typeof dict.detail === 'string') {
            errorMessage = dict.detail;
          } else if (typeof dict.message === 'string') {
            errorMessage = dict.message;
          }
        }
      } catch {
        // Not a JSON error body
      }
      throw new ApiError(errorMessage, response.status, errorData);
    }

    const data = await response.json();
    return data as T;
  } catch (err: unknown) {
    clearTimeout(timeoutId);

    if (err instanceof ApiError) {
      throw err;
    }

    if (err instanceof Error) {
      if (err.name === 'AbortError') {
        throw new ApiError(
          `Request to Laptop 1 timed out after ${timeoutMs / 1000}s. Check if the backend is running and network is stable.`,
          408
        );
      }
      if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        throw new ApiError(
          `Cannot reach Laptop 1 at ${baseUrl}. Ensure FastAPI is started on 0.0.0.0, the port is open, and both laptops are on the same subnet.`,
          503
        );
      }
      throw new ApiError(err.message);
    }

    throw new ApiError('An unknown communication error occurred with Laptop 1.');
  }
}
