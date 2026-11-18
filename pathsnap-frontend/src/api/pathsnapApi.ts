import { apiRequest } from './client';
import {
  HealthResponse,
  TripListResponse,
  PredictResponse,
  TripSummary,
} from '../types/api';

/**
 * Checks the FastAPI health endpoint on Laptop 1
 */
export async function checkBackendHealth(): Promise<{ data: HealthResponse; latencyMs: number }> {
  const start = performance.now();
  const data = await apiRequest<HealthResponse>('/health', {
    method: 'GET',
    timeoutMs: 4000,
  });
  const latencyMs = Math.round(performance.now() - start);
  return { data, latencyMs };
}

/**
 * Fetches the list of available evaluation trips from Laptop 1
 */
export async function getEvaluationTrips(): Promise<TripSummary[]> {
  const res = await apiRequest<TripListResponse | TripSummary[] | string[]>('/api/trips', {
    method: 'GET',
    timeoutMs: 8000,
  });

  // Handle various potential backend shapes gracefully
  let rawList: unknown[] = [];
  if (Array.isArray(res)) {
    rawList = res;
  } else if (res && Array.isArray((res as TripListResponse).trips)) {
    rawList = (res as TripListResponse).trips;
  }

  const trips: TripSummary[] = rawList.map((item) => {
    if (typeof item === 'string') {
      return { trip_id: item };
    }
    if (typeof item === 'object' && item !== null) {
      const obj = item as Record<string, unknown>;
      return {
        trip_id: String(obj.trip_id ?? obj.id ?? ''),
        num_points: typeof obj.num_points === 'number' ? obj.num_points : undefined,
        time_span_s: typeof obj.time_span_s === 'number' ? obj.time_span_s : undefined,
        description: typeof obj.description === 'string' ? obj.description : undefined,
      };
    }
    return { trip_id: String(item) };
  }).filter((t) => t.trip_id.trim() !== '');

  return trips;
}

/**
 * Sends a trip ID to Laptop 1 to run preprocessing, ML inference, and HMM/Viterbi decoding
 */
export async function runPrediction(
  tripId: string,
  signal?: AbortSignal
): Promise<PredictResponse> {
  if (!tripId || tripId.trim() === '') {
    throw new Error('A valid evaluation trip must be selected.');
  }

  return await apiRequest<PredictResponse>('/api/predict', {
    method: 'POST',
    body: JSON.stringify({ trip_id: tripId }),
    timeoutMs: 30000, // ML inference & HMM decoding can take several seconds
    signal,
  });
}

