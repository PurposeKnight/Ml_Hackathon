import React from 'react';
import { Loader2, Server, Cpu, Network } from 'lucide-react';

interface LoadingStateProps {
  tripId: string;
  elapsedMs: number;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ tripId, elapsedMs }) => {
  const seconds = (elapsedMs / 1000).toFixed(1);

  return (
    <div className="bg-slate-800/90 border border-indigo-500/30 rounded-xl p-5 shadow-lg">
      <div className="flex items-center space-x-3 mb-4">
        <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
        <div>
          <h4 className="text-sm font-semibold text-white">
            Distributed Inference in Progress...
          </h4>
          <p className="text-xs text-slate-400 font-mono">
            Trip ID: {tripId} &bull; Elapsed: {seconds}s
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
        <div className="flex items-center space-x-2 bg-slate-900/60 p-2.5 rounded-lg border border-slate-700/50">
          <Server className="h-4 w-4 text-indigo-400 shrink-0" />
          <span className="text-slate-300">1. Laptop 1 Preprocessing</span>
        </div>
        <div className="flex items-center space-x-2 bg-slate-900/60 p-2.5 rounded-lg border border-slate-700/50">
          <Cpu className="h-4 w-4 text-violet-400 shrink-0" />
          <span className="text-slate-300">2. ML Emission Scoring</span>
        </div>
        <div className="flex items-center space-x-2 bg-slate-900/60 p-2.5 rounded-lg border border-slate-700/50">
          <Network className="h-4 w-4 text-emerald-400 shrink-0" />
          <span className="text-slate-300">3. Viterbi Route Decoding</span>
        </div>
      </div>
    </div>
  );
};

