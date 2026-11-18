import React from 'react';
import { Compass, Server, ShieldCheck } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="bg-slate-800/80 backdrop-blur border-b border-slate-700/60 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Compass className="h-6 w-6 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white">PathSnap</h1>
              <span className="px-2 py-0.5 text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full">
                Laptop 2 Interface
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Distributed Map-Matching &amp; Route Reconstruction
            </p>
          </div>
        </div>

        <div className="hidden md:flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1.5 text-slate-400 bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700">
            <Server className="h-3.5 w-3.5 text-indigo-400" />
            <span>Node: <strong className="text-slate-200">Evaluator UI</strong></span>
          </div>
          <div className="flex items-center space-x-1.5 text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-lg border border-emerald-500/20">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Zero Ground-Truth Leakage</span>
          </div>
        </div>
      </div>
    </header>
  );
};

