import React, { useState } from 'react';
import { Wifi, WifiOff, RefreshCw, Settings, Check, Clock } from 'lucide-react';
import { ConnectionStatus, HealthResponse } from '../types/api';

interface BackendStatusProps {
  status: ConnectionStatus;
  url: string;
  latencyMs: number | null;
  lastChecked: Date | null;
  errorMessage?: string;
  details?: HealthResponse | null;
  onRetry: () => void;
  onUpdateUrl: (url: string) => void;
}

export const BackendStatus: React.FC<BackendStatusProps> = ({
  status,
  url,
  latencyMs,
  errorMessage,
  details,
  onRetry,
  onUpdateUrl,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [inputUrl, setInputUrl] = useState(url);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputUrl.trim()) {
      onUpdateUrl(inputUrl.trim());
      setIsEditing(false);
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case 'connected':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping inline-block mr-1"></span>
            <Wifi className="h-3.5 w-3.5" />
            <span>Connected</span>
          </span>
        );
      case 'connecting':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            <span>Connecting...</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <WifiOff className="h-3.5 w-3.5" />
            <span>Disconnected</span>
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          {getStatusBadge()}
          <div className="text-sm">
            <span className="text-slate-400">Laptop 1 Host: </span>
            <code className="text-indigo-300 font-mono text-xs bg-slate-900/60 px-2 py-0.5 rounded border border-slate-700/50">
              {url}
            </code>
          </div>
          {latencyMs !== null && status === 'connected' && (
            <span className="hidden sm:inline-flex items-center text-xs text-slate-400 bg-slate-900/40 px-2 py-0.5 rounded">
              <Clock className="h-3 w-3 mr-1 text-slate-500" />
              {latencyMs}ms
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => onRetry()}
            className="p-1.5 text-slate-400 hover:text-white bg-slate-700/60 hover:bg-slate-700 rounded-lg transition-colors border border-slate-600/50 text-xs flex items-center space-x-1"
            title="Retry Connection"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Retry</span>
          </button>

          <button
            onClick={() => {
              setInputUrl(url);
              setIsEditing(!isEditing);
            }}
            className="p-1.5 text-slate-400 hover:text-white bg-slate-700/60 hover:bg-slate-700 rounded-lg transition-colors border border-slate-600/50 text-xs flex items-center space-x-1"
            title="Change Laptop 1 IP"
          >
            <Settings className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Configure IP</span>
          </button>
        </div>
      </div>

      {isEditing && (
        <form onSubmit={handleSave} className="mt-3 pt-3 border-t border-slate-700 flex items-center gap-2">
          <div className="flex-1">
            <input
              type="text"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="http://192.168.1.10:8000"
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium flex items-center space-x-1"
          >
            <Check className="h-3.5 w-3.5" />
            <span>Apply</span>
          </button>
          <button
            type="button"
            onClick={() => setIsEditing(false)}
            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-xs"
          >
            Cancel
          </button>
        </form>
      )}

      {status === 'disconnected' && errorMessage && (
        <div className="mt-2 text-xs text-rose-300/90 bg-rose-950/30 border border-rose-800/40 rounded-lg p-2 flex items-start space-x-2">
          <WifiOff className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Backend Unreachable</p>
            <p className="text-slate-300 mt-0.5">{errorMessage}</p>
            <p className="text-slate-400 text-[11px] mt-1">
              Check: 1) Laptop 1 FastAPI running (<code className="text-slate-200">uvicorn backend.main:app --host 0.0.0.0 --port 8000</code>). 2) Wi-Fi/Ethernet IP matches. 3) Port 8000 allowed in firewall.
            </p>
          </div>
        </div>
      )}

      {status === 'connected' && details && (
        <div className="mt-2 text-[11px] text-slate-400 flex flex-wrap gap-x-4 gap-y-1">
          {details.ready !== undefined && (
            <span>Backend Ready: <strong className={details.ready ? 'text-emerald-400' : 'text-amber-400'}>{details.ready ? 'Yes' : 'No'}</strong></span>
          )}
          {details.model_loaded !== undefined && (
            <span>Model Loaded: <strong className={details.model_loaded ? 'text-emerald-400' : 'text-amber-400'}>{details.model_loaded ? 'Yes' : 'No'}</strong></span>
          )}
          {details.hmm_ready !== undefined && (
            <span>HMM Ready: <strong className={details.hmm_ready ? 'text-emerald-400' : 'text-amber-400'}>{details.hmm_ready ? 'Yes' : 'No'}</strong></span>
          )}
          {details.version && (
            <span>Version: <strong className="text-slate-200">{details.version}</strong></span>
          )}
        </div>
      )}
    </div>
  );
};

