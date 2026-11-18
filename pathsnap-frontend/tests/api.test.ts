import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getEvaluationTrips, runPrediction } from '../src/api/pathsnapApi';
import * as client from '../src/api/client';

describe('PathSnap API Integration Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

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
  });

  it('throws an error if empty tripId is passed to runPrediction', async () => {
    await expect(runPrediction('')).rejects.toThrow('A valid evaluation trip must be selected');
  });
});

