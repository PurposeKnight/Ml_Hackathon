import React from 'react';
import { MapPin, RefreshCw, AlertCircle } from 'lucide-react';
import { TripSummary } from '../types/api';

interface TripSelectorProps {
  trips: TripSummary[];
  selectedTripId: string;
  isLoading: boolean;
  error: string | null;
  disabled: boolean;
  onSelectTrip: (tripId: string) => void;
  onRefreshTrips: () => void;
}

export const TripSelector: React.FC<TripSelectorProps> = ({
  trips,
  selectedTripId,
  isLoading,
  error,
  disabled,
  onSelectTrip,
  onRefreshTrips,
}) => {
  const selectedTrip = trips.find((t) => t.trip_id === selectedTripId);

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <label htmlFor="trip-select" className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
          <MapPin className="h-4 w-4 text-indigo-400" />
          <span>Select Evaluation Trip ({trips.length} Available)</span>
        </label>
        <button
          type="button"
          onClick={onRefreshTrips}
          disabled={disabled || isLoading}
          className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-700 transition-colors disabled:opacity-40"
          title="Refresh Trip List"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="relative">
        <select
          id="trip-select"
          value={selectedTripId}
          onChange={(e) => onSelectTrip(e.target.value)}
          disabled={disabled || isLoading || trips.length === 0}
          className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 font-mono"
        >
          {trips.length === 0 ? (
            <option value="">{isLoading ? 'Loading evaluation trips from Laptop 1...' : 'No trips available'}</option>
          ) : (
            trips.map((trip) => (
              <option key={trip.trip_id} value={trip.trip_id}>
                Trip ID: {trip.trip_id} {trip.num_points ? `(${trip.num_points} GPS observations)` : ''}
              </option>
            ))
          )}
        </select>
      </div>

      {selectedTrip && (
        <div className="mt-2.5 flex items-center gap-3 text-xs text-slate-400">
          <span className="bg-slate-900/60 px-2 py-0.5 rounded border border-slate-700/50">
            Selected: <strong className="text-indigo-300 font-mono">{selectedTrip.trip_id}</strong>
          </span>
          {selectedTrip.num_points !== undefined && (
            <span className="bg-slate-900/60 px-2 py-0.5 rounded border border-slate-700/50">
              Observations: <strong className="text-slate-200">{selectedTrip.num_points}</strong>
            </span>
          )}
          {selectedTrip.description && (
            <span className="text-slate-400 truncate">{selectedTrip.description}</span>
          )}
        </div>
      )}

      {error && (
        <div className="mt-2 text-xs text-rose-300 bg-rose-950/20 border border-rose-800/30 rounded p-2 flex items-center space-x-1.5">
          <AlertCircle className="h-3.5 w-3.5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};

