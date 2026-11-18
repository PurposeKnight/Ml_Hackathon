/**
 * PathSnap TypeScript API Contract Definitions
 * Shared between Laptop 1 (FastAPI Backend) and Laptop 2 (React Frontend)
 */

export interface HealthResponse {
  status: 'healthy' | 'ok' | string;
  version?: string;
  model_loaded?: boolean;
  hmm_ready?: boolean;
  timestamp?: number | string;
}

export interface TripSummary {
  trip_id: string;
  num_points?: number;
  time_span_s?: number;
  description?: string;
}

export interface TripListResponse {
  trips: (TripSummary | string)[];
  count?: number;
}

export interface PredictRequest {
  trip_id: string;
}

export interface RouteMetrics {
  accuracy?: number | null;
  route_continuity?: number | null;
  num_gps_points?: number | null;
  num_predicted_segments?: number | null;
  classifier_only_accuracy?: number | null;
  hmm_accuracy?: number | null;
  [key: string]: string | number | boolean | null | undefined;
}

/**
 * Coordinate representations:
 * Leaflet standard: [latitude, longitude]
 * GeoJSON standard: [longitude, latitude]
 */
export type LatLngCoord = [number, number]; // [lat, lng]
export type GPSObservation = [number, number, ...number[]]; // [lat, lng, timestamp?]

export interface PredictResponse {
  trip_id: string;
  status: 'success' | 'completed' | 'error' | string;
  predicted_segments: (number | string)[];
  predicted_route_coordinates: LatLngCoord[];
  gps_coordinates: GPSObservation[];
  road_network_coordinates?: LatLngCoord[][];
  metrics: RouteMetrics;
  inference_time_ms?: number | null;
  folium_html?: string | null;
  message?: string;
  detail?: string;
}

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

export interface BackendStatusState {
  status: ConnectionStatus;
  url: string;
  latencyMs: number | null;
  lastChecked: Date | null;
  errorMessage?: string;
  details?: HealthResponse | null;
}

