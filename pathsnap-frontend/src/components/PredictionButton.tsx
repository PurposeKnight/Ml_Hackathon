import React from 'react';
import { Play, Loader2, StopCircle } from 'lucide-react';

interface PredictionButtonProps {
  isPredicting: boolean;
  disabled: boolean;
  elapsedMs: number;
  onRunPrediction: () => void;
  onCancel?: () => void;
}

export const PredictionButton: React.FC<PredictionButtonProps> = ({
  isPredicting,
  disabled,
  elapsedMs,
  onRunPrediction,
  onCancel,
}) => {
  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={onRunPrediction}
        disabled={disabled || isPredicting}
        className={`w-full flex items-center justify-center space-x-2 px-5 py-3 rounded-xl font-semibold text-sm transition-all shadow-lg ${
          isPredicting
            ? 'bg-indigo-700/80 text-white cursor-wait'
            : disabled
            ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
            : 'bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-indigo-500/25 active:scale-[0.99]'
        }`}
      >
        {isPredicting ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin text-white" />
            <span>Processing on Laptop 1... ({(elapsedMs / 1000).toFixed(1)}s)</span>
          </>
        ) : (
          <>
            <Play className="h-4 w-4 fill-current" />
            <span>Run Prediction &amp; Reconstruction</span>
          </>
        )}
      </button>

      {isPredicting && onCancel && (
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-3 rounded-xl font-medium text-xs bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 transition-colors flex items-center space-x-1"
          title="Abort in-flight prediction"
        >
          <StopCircle className="h-4 w-4" />
          <span className="hidden sm:inline">Abort</span>
        </button>
      )}
    </div>
  );
};

