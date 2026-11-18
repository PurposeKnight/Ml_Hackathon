import React from 'react';
import { Header } from './components/Header';
import { BackendStatus } from './components/BackendStatus';
import { TripSelector } from './components/TripSelector';
import { PredictionButton } from './components/PredictionButton';
import { RouteMap } from './components/RouteMap';
import { MetricsPanel } from './components/MetricsPanel';
import { LoadingState } from './components/LoadingState';
import { ErrorMessage } from './components/ErrorMessage';
import { useBackendStatus } from './hooks/useBackendStatus';
import { usePrediction } from './hooks/usePrediction';
import { Terminal, Laptop, HelpCircle } from 'lucide-react';

export const App: React.FC = () => {
  const {
    status,
    url,
    latencyMs,
    lastChecked,
    errorMessage: backendError,
    details,
    checkConnection,
    updateUrl,
    isConnected,
  } = useBackendStatus(15000);

  const {
    trips,
    selectedTripId,
    isLoadingTrips,
    tripFetchError,
    refreshTrips,
    selectTrip,
    isPredicting,
    predictionResult,
    predictionError,
    elapsedMs,
    executePrediction,
    resetPrediction,
  } = usePrediction(isConnected);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Backend Status Bar */}
        <BackendStatus
          status={status}
          url={url}
          latencyMs={latencyMs}
          lastChecked={lastChecked}
          errorMessage={backendError}
          details={details}
          onRetry={checkConnection}
          onUpdateUrl={updateUrl}
        />

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Controls & Metrics (5 cols on lg) */}
          <div className="lg:col-span-5 space-y-5">
            {/* Trip Selector */}
            <TripSelector
              trips={trips}
              selectedTripId={selectedTripId}
              isLoading={isLoadingTrips}
              error={tripFetchError}
              disabled={isPredicting}
              onSelectTrip={selectTrip}
              onRefreshTrips={refreshTrips}
            />

            {/* Run Prediction Button */}
            <PredictionButton
              isPredicting={isPredicting}
              disabled={!isConnected || !selectedTripId}
              elapsedMs={elapsedMs}
              onRunPrediction={executePrediction}
              onCancel={resetPrediction}
            />

            {/* In-Flight Inference Indicator */}
            {isPredicting && (
              <LoadingState tripId={selectedTripId} elapsedMs={elapsedMs} />
            )}

            {/* Prediction Error */}
            {predictionError && (
              <ErrorMessage
                message={predictionError}
                onRetry={executePrediction}
                onDismiss={() => resetPrediction()}
              />
            )}

            {/* Server-Side Evaluation Metrics */}
            <MetricsPanel
              metrics={predictionResult?.metrics || null}
              inferenceTimeMs={predictionResult?.inference_time_ms}
              tripId={predictionResult?.trip_id || null}
              predictedSegmentsCount={predictionResult?.predicted_segments?.length || 0}
              gpsPointsCount={predictionResult?.gps_coordinates?.length || 0}
            />

            {/* System Architecture Explanatory Card */}
            <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/60 text-xs text-slate-400 space-y-2">
              <div className="flex items-center space-x-1.5 text-slate-300 font-semibold">
                <Laptop className="h-4 w-4 text-indigo-400" />
                <span>Distributed Pipeline Verification</span>
              </div>
              <p>
                When you click <strong>Run Prediction</strong>, the selected trip ID is sent to Laptop 1 over HTTP.
                Laptop 1 runs preprocessing, candidate road segment matching, ML classifier inference, and Viterbi sequence decoding, then evaluates accuracy server-side against ground-truth labels.
              </p>
              <div className="flex items-center space-x-2 pt-1 text-[11px] text-slate-400">
                <Terminal className="h-3.5 w-3.5 text-indigo-400" />
                <span>Inspect Laptop 1 terminal logs during inference to observe FastAPI processing.</span>
              </div>
            </div>
          </div>

          {/* Right Column: Interactive Map (7 cols on lg) */}
          <div className="lg:col-span-7">
            <RouteMap
              gpsCoordinates={predictionResult?.gps_coordinates || []}
              predictedRouteCoordinates={predictionResult?.predicted_route_coordinates || []}
              roadNetworkCoordinates={predictionResult?.road_network_coordinates || []}
              foliumHtml={predictionResult?.folium_html || null}
              tripId={predictionResult?.trip_id || selectedTripId || null}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/80 py-4 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>PathSnap &bull; Distributed Map-Matching &amp; Route Reconstruction</span>
          <span className="flex items-center space-x-1">
            <HelpCircle className="h-3 w-3 text-slate-400" />
            <span>Laptop 2 Evaluator Client &bull; PES University UE24CS352A</span>
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;

