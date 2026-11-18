import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getEvaluationTrips, runPrediction, checkBackendHealth } from '../src/api/pathsnapApi';
import * as client from '../src/api/client';
import { normalizeCoordinates } from '../src/utils/coordinates';

describe('PathSnap API Contract & Resilience Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  // 1. Trip list rendering & parsing
  it('fetches and normalizes evaluation trips list from Laptop 1', async () => {
    const mockApiResponse = {
      trips: [
        { trip_id: '00000000', num_points: 582 },
        { trip_id: '00000007', num_points: 412 },
        '00000009',
      ],
      count: 3,
    };

    vi.spyOn(client, 'apiRequest').mockResolvedValue(mockApiResponse);

    const trips = await getEvaluationTrips();
    expect(trips).toHaveLength(3);
    expect(trips[0].trip_id).toBe('00000000');
    expect(trips[0].num_points).toBe(582);
    expect(trips[2].trip_id).toBe('00000009');
  });

  // 2. API request construction & successful prediction
  it('sends correct prediction request payload and validates response', async () => {
    const mockPrediction = {
      trip_id: '00000000',
      status: 'success',
      predicted_segments: [17630, 17633, 211],
      predicted_route_coordinates: [
        [54.9635, 56.2515],
        [54.9631, 56.2515],
      ],
      gps_coordinates: [
        [54.963519, 56.251559, 1.0],
      ],
      metrics: {
        accuracy: 0.892,
        route_continuity: 0.95,
        num_gps_points: 582,
        num_predicted_segments: 3,
      },
      inference_time_ms: 120.4,
    };

    const spy = vi.spyOn(client, 'apiRequest').mockResolvedValue(mockPrediction);

    const response = await runPrediction('00000000');
    expect(spy).toHaveBeenCalledWith(
      '/api/predict',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ trip_id: '00000000' }),
      })
    );
    expect(response.trip_id).toBe('00000000');
    expect(response.metrics.accuracy).toBe(0.892);
    expect(response.metrics.route_continuity).toBe(0.95);
  });

  // 3. Invalid trip handling
  it('throws an error if empty tripId is passed to runPrediction', async () => {
    await expect(runPrediction('')).rejects.toThrow('A valid evaluation trip must be selected');
    await expect(runPrediction('   ')).rejects.toThrow('A valid evaluation trip must be selected');
  });

  // 4. Backend connection failure
  it('handles backend connection failure gracefully during health check', async () => {
    vi.spyOn(client, 'apiRequest').mockRejectedValue(
      new client.ApiError('Cannot reach Laptop 1 at http://localhost:8000', 503)
    );

    await expect(checkBackendHealth()).rejects.toThrow('Cannot reach Laptop 1');
  });

  // 5. Trip does not exist (404)
  it('handles non-existent evaluation trip response (404)', async () => {
    vi.spyOn(client, 'apiRequest').mockRejectedValue(
      new client.ApiError("Evaluation trip '99999999' not found.", 404)
    );

    await expect(runPrediction('99999999')).rejects.toThrow("Evaluation trip '99999999' not found.");
  });

  // 6. Missing metrics fallback
  it('handles incomplete or missing metrics gracefully without failing', async () => {
    const incompletePrediction = {
      trip_id: '00000007',
      status: 'success',
      predicted_segments: [101, 102],
      predicted_route_coordinates: [[54.96, 56.25]],
      gps_coordinates: [[54.96, 56.25, 1.0]],
      metrics: {
        accuracy: null, // Metric not yet computed or withheld
        route_continuity: undefined,
      },
      inference_time_ms: null,
    };

    vi.spyOn(client, 'apiRequest').mockResolvedValue(incompletePrediction);

    const response = await runPrediction('00000007');
    expect(response.metrics.accuracy).toBeNull();
    expect(response.metrics.route_continuity).toBeUndefined();
    expect(response.inference_time_ms).toBeNull();
  });

  // 7. Request cancellation on switching trips
  it('supports AbortSignal to cancel in-flight request when user changes trips', async () => {
    const controller = new AbortController();

    vi.spyOn(client, 'apiRequest').mockImplementation((_url, options) => {
      return new Promise((_resolve, reject) => {
        if (options?.signal) {
          options.signal.addEventListener('abort', () => {
            const err = new Error('The operation was aborted');
            err.name = 'AbortError';
            reject(err);
          });
        }
      });
    });

    const predictionPromise = runPrediction('00000000', controller.signal);
    // User switches trip immediately
    controller.abort();

    await expect(predictionPromise).rejects.toThrow('The operation was aborted');
  });

  // 8. Sanitizes invalid or malformed coordinates from responses
  it('sanitizes and normalizes malformed coordinates from prediction responses', () => {
    const dirtyCoordinates = [
      [54.9635, 56.2515],
      [NaN, 56.2515],
      null,
      [999.0, 56.2515], // Out of geographic range
      { lat: 54.9620, lon: 56.2510 },
    ];

    const clean = normalizeCoordinates(dirtyCoordinates);
    expect(clean).toHaveLength(2);
    expect(clean[0]).toEqual([54.9635, 56.2515]);
    expect(clean[1]).toEqual([54.9620, 56.2510]);
  });

  // 9. URL configuration and sanitization
  it('handles trailing slashes and dynamic base URL setting', () => {
    client.setBackendBaseUrl('http://192.168.1.50:8000///');
    expect(client.getBackendBaseUrl()).toBe('http://192.168.1.50:8000');

    client.resetBackendBaseUrl();
    expect(client.getBackendBaseUrl()).toMatch(/http:\/\/(localhost|127\.0\.0\.1|.*):[0-9]+/);
  });
});
