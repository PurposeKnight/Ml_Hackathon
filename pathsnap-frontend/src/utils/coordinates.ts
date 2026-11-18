import { LatLngCoord, GPSObservation } from '../types/api';

/**
 * Validates and converts various coordinate inputs to standard Leaflet [latitude, longitude] pairs.
 * Filters out invalid, non-numeric, or out-of-range coordinates.
 */
export function normalizeCoordinates(coords: unknown[]): LatLngCoord[] {
  if (!Array.isArray(coords)) return [];

  const valid: LatLngCoord[] = [];

  for (const item of coords) {
    if (!item) continue;

    let lat: number | undefined;
    let lng: number | undefined;

    if (Array.isArray(item) && item.length >= 2) {
      const a = Number(item[0]);
      const b = Number(item[1]);

      if (Number.isFinite(a) && Number.isFinite(b)) {
        lat = a;
        lng = b;
      }
    } else if (typeof item === 'object') {
      const obj = item as Record<string, unknown>;
      const latVal = obj.lat ?? obj.latitude ?? obj.y;
      const lngVal = obj.lng ?? obj.lon ?? obj.longitude ?? obj.x;

      if (latVal !== undefined && lngVal !== undefined) {
        const a = Number(latVal);
        const b = Number(lngVal);
        if (Number.isFinite(a) && Number.isFinite(b)) {
          lat = a;
          lng = b;
        }
      }
    }

    if (lat !== undefined && lng !== undefined) {
      // In the PathSnap dataset, coordinates are around 54.0 - 57.0 (latitude / longitude)
      // Standard geographic bounds: latitude between -90 and 90, longitude between -180 and 180
      if (lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        valid.push([lat, lng]);
      }
    }
  }

  return valid;
}

/**
 * Normalizes GPS observations that may contain [lat, lon, timestamp]
 */
export function normalizeGpsObservations(obs: unknown[]): GPSObservation[] {
  if (!Array.isArray(obs)) return [];

  const valid: GPSObservation[] = [];

  for (const item of obs) {
    if (!item) continue;
    if (Array.isArray(item) && item.length >= 2) {
      const lat = Number(item[0]);
      const lng = Number(item[1]);
      if (Number.isFinite(lat) && Number.isFinite(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        const ts = item.length > 2 && Number.isFinite(Number(item[2])) ? Number(item[2]) : undefined;
        if (ts !== undefined) {
          valid.push([lat, lng, ts]);
        } else {
          valid.push([lat, lng]);
        }
      }
    }
  }

  return valid;
}

/**
 * Calculates bounding box [[minLat, minLng], [maxLat, maxLng]] for a set of coordinates
 */
export function computeBoundingBox(coords: LatLngCoord[]): [[number, number], [number, number]] | null {
  if (!coords || coords.length === 0) return null;

  let minLat = Infinity;
  let maxLat = -Infinity;
  let minLng = Infinity;
  let maxLng = -Infinity;

  for (const [lat, lng] of coords) {
    if (lat < minLat) minLat = lat;
    if (lat > maxLat) maxLat = lat;
    if (lng < minLng) minLng = lng;
    if (lng > maxLng) maxLng = lng;
  }

  if (!Number.isFinite(minLat) || !Number.isFinite(maxLat)) return null;

  // Add small padding if it's a single point
  if (minLat === maxLat) {
    minLat -= 0.002;
    maxLat += 0.002;
  }
  if (minLng === maxLng) {
    minLng -= 0.002;
    maxLng += 0.002;
  }

  return [[minLat, minLng], [maxLat, maxLng]];
}

/**
 * Calculates geographic center of a set of coordinates
 */
export function computeCenter(coords: LatLngCoord[]): LatLngCoord {
  if (!coords || coords.length === 0) {
    return [54.96, 56.25]; // Default dataset approximate region
  }

  const box = computeBoundingBox(coords);
  if (!box) return [54.96, 56.25];

  const latCenter = (box[0][0] + box[1][0]) / 2;
  const lngCenter = (box[0][1] + box[1][1]) / 2;
  return [latCenter, lngCenter];
}

/**
 * Haversine formula to compute distance in kilometers between two points
 */
export function haversineDistanceKm(p1: LatLngCoord, p2: LatLngCoord): number {
  const R = 6371; // Earth radius in km
  const dLat = ((p2[0] - p1[0]) * Math.PI) / 180;
  const dLon = ((p2[1] - p1[1]) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((p1[0] * Math.PI) / 180) *
      Math.cos((p2[0] * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Computes total cumulative length of a route in kilometers
 */
export function calculateRouteLengthKm(coords: LatLngCoord[]): number {
  if (!coords || coords.length < 2) return 0;
  let total = 0;
  for (let i = 1; i < coords.length; i++) {
    total += haversineDistanceKm(coords[i - 1], coords[i]);
  }
  return total;
}

