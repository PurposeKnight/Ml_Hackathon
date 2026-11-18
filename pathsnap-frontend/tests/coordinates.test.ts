import { describe, it, expect } from 'vitest';
import {
  normalizeCoordinates,
  normalizeGpsObservations,
  computeBoundingBox,
  computeCenter,
  calculateRouteLengthKm,
  haversineDistanceKm,
} from '../src/utils/coordinates';

describe('Coordinate Utilities', () => {
  it('normalizes valid [latitude, longitude] arrays', () => {
    const raw = [
      [54.9635, 56.2515],
      [54.9631, 56.2515],
    ];
    const result = normalizeCoordinates(raw);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual([54.9635, 56.2515]);
  });

  it('filters out invalid or non-finite coordinates', () => {
    const raw = [
      [54.9635, 56.2515],
      [NaN, 56.2515],
      null,
      [120.0, 56.2515], // Invalid latitude (> 90)
      ['invalid', 'data'],
      [54.9627, 56.2515],
    ];
    const result = normalizeCoordinates(raw);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual([54.9635, 56.2515]);
    expect(result[1]).toEqual([54.9627, 56.2515]);
  });

  it('normalizes object coordinate representations', () => {
    const raw = [
      { lat: 54.9635, lon: 56.2515 },
      { latitude: 54.9631, longitude: 56.2515 },
    ];
    const result = normalizeCoordinates(raw);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual([54.9635, 56.2515]);
    expect(result[1]).toEqual([54.9631, 56.2515]);
  });

  it('normalizes GPS observations with timestamps', () => {
    const raw = [
      [54.9635, 56.2515, 1.0],
      [54.9631, 56.2515, 2.0],
    ];
    const result = normalizeGpsObservations(raw);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual([54.9635, 56.2515, 1.0]);
  });

  it('computes correct bounding box and center', () => {
    const coords: [number, number][] = [
      [54.0, 56.0],
      [55.0, 57.0],
    ];
    const bbox = computeBoundingBox(coords);
    expect(bbox).toEqual([
      [54.0, 56.0],
      [55.0, 57.0],
    ]);

    const center = computeCenter(coords);
    expect(center).toEqual([54.5, 56.5]);
  });

  it('computes accurate route distances using Haversine formula', () => {
    const p1: [number, number] = [54.0, 56.0];
    const p2: [number, number] = [54.0, 56.0];
    expect(haversineDistanceKm(p1, p2)).toBe(0);

    const route: [number, number][] = [
      [54.9635, 56.2515],
      [54.9645, 56.2515],
    ];
    const dist = calculateRouteLengthKm(route);
    expect(dist).toBeGreaterThan(0.05);
    expect(dist).toBeLessThan(0.2);
  });
});

