import React from 'react';
import { Activity, CheckCircle2, Clock, Route, Compass, Database, ShieldAlert } from 'lucide-react';
import { RouteMetrics } from '../types/api';

interface MetricsPanelProps {
  metrics: RouteMetrics | null;
  inferenceTimeMs: number | null | undefined;
  tripId: string | null;
  predictedSegmentsCount: number;
  gpsPointsCount: number;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({
  metrics,
  inferenceTimeMs,
  tripId,
  predictedSegmentsCount,
  gpsPointsCount,
}) => {
  if (!metrics && !tripId) {
    return (
      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 shadow-sm flex flex-col items-center justify-center text-center py-8">
        <Activity className="h-8 w-8 text-slate-600 mb-2" />
        <h3 className="text-sm font-semibold text-slate-300">No Evaluation Metrics Yet</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-xs">
          Select an evaluation trip and click &ldquo;Run Prediction&rdquo; to receive server-evaluated metrics from Laptop 1.
        </p>
      </div>
    );
  }

  const formatPercent = (val: unknown): string => {
    if (typeof val === 'number' && Number.isFinite(val)) {
      // If decimal 0-1, multiply by 100
      const pct = val <= 1 && val >= 0 ? val * 100 : val;
      return `${pct.toFixed(2)}%`;
    }
    return 'N/A';
  };

  const accuracy = metrics?.accuracy;
  const continuity = metrics?.route_continuity;
  const classifierAccuracy = metrics?.classifier_only_accuracy;
  const hmmAccuracy = metrics?.hmm_accuracy;

  return (
    <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-700/70 pb-3">
        <div className="flex items-center space-x-2">
          <Activity className="h-4 w-4 text-indigo-400" />
          <h3 className="text-sm font-bold text-white tracking-wide">
            Server Evaluation Results
          </h3>
        </div>
        {tripId && (
          <span className="text-xs font-mono bg-indigo-950/60 text-indigo-300 border border-indigo-700/50 px-2 py-0.5 rounded">
            Trip: {tripId}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {/* Accuracy Card */}
        <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700/60">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Accuracy</span>
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-extrabold text-emerald-400">
            {formatPercent(accuracy)}
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">Calculated on Laptop 1</p>
        </div>

        {/* Route Continuity */}
        <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700/60">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Continuity</span>
            <Route className="h-3.5 w-3.5 text-violet-400" />
          </div>
          <div className="text-xl font-extrabold text-violet-400">
            {formatPercent(continuity)}
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">Viterbi sequence metric</p>
        </div>

        {/* Inference Latency */}
        <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700/60 col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Inference Time</span>
            <Clock className="h-3.5 w-3.5 text-amber-400" />
          </div>
          <div className="text-xl font-extrabold text-amber-400">
            {inferenceTimeMs !== null && inferenceTimeMs !== undefined
              ? `${Number(inferenceTimeMs).toFixed(1)} ms`
              : 'N/A'}
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">ML + HMM decoding</p>
        </div>

        {/* GPS Points */}
        <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700/60">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>GPS Points</span>
            <Compass className="h-3.5 w-3.5 text-blue-400" />
          </div>
          <div className="text-lg font-bold text-slate-200">
            {metrics?.num_gps_points ?? gpsPointsCount}
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">Observation track</p>
        </div>

        {/* Predicted Segments */}
        <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700/60">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Road Segments</span>
            <Database className="h-3.5 w-3.5 text-cyan-400" />
          </div>
          <div className="text-lg font-bold text-slate-200">
            {metrics?.num_predicted_segments ?? predictedSegmentsCount}
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">Matched network arcs</p>
        </div>

        {/* Comparative Model Metrics (Classifier vs HMM) */}
        {(classifierAccuracy !== undefined || hmmAccuracy !== undefined) && (
          <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700/60 col-span-2 sm:col-span-1">
            <div className="text-xs text-slate-400 mb-1">Classifier vs HMM</div>
            <div className="text-xs font-semibold text-slate-300">
              Raw: <span className="text-amber-400">{formatPercent(classifierAccuracy)}</span>
            </div>
            <div className="text-xs font-semibold text-slate-300">
              HMM: <span className="text-emerald-400">{formatPercent(hmmAccuracy)}</span>
            </div>
          </div>
        )}
      </div>

      {/* Ground Truth Safety Note */}
      <div className="flex items-start space-x-2 bg-slate-900/40 border border-slate-700/50 rounded-lg p-2.5 text-[11px] text-slate-400">
        <ShieldAlert className="h-4 w-4 text-indigo-400 shrink-0 mt-0.5" />
        <span>
          <strong>Academic Integrity Notice:</strong> All evaluation ground-truth and accuracy computations are isolated on Laptop 1. Laptop 2 only receives and displays authorized telemetry.
        </span>
      </div>
    </div>
  );
};

