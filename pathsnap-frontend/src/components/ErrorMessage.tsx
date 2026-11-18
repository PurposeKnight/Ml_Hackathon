import React from 'react';
import { AlertTriangle, XCircle, RotateCcw } from 'lucide-react';

interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'Inference Error',
  message,
  onRetry,
  onDismiss,
}) => {
  return (
    <div className="bg-rose-950/40 border border-rose-800/60 rounded-xl p-4 shadow-sm text-xs">
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-2.5">
          <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-rose-200">{title}</h4>
            <p className="text-slate-300 mt-1 leading-relaxed">{message}</p>
          </div>
        </div>

        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-slate-400 hover:text-slate-200 p-1"
            title="Dismiss error"
          >
            <XCircle className="h-4 w-4" />
          </button>
        )}
      </div>

      {onRetry && (
        <div className="mt-3 flex justify-end">
          <button
            onClick={onRetry}
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-rose-900/60 hover:bg-rose-800/80 text-rose-200 border border-rose-700/50 font-medium transition-colors"
          >
            <RotateCcw className="h-3 w-3" />
            <span>Retry Request</span>
          </button>
        </div>
      )}
    </div>
  );
};

