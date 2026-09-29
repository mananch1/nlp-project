import React from 'react';
import { ShieldAlert, ShieldCheck, Scale, FileText, Sparkles } from 'lucide-react';

export default function Header({ activeTab, setActiveTab }) {
  return (
    <header className="bg-slate-900 text-white shadow-md border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-tr from-emerald-600 to-teal-500 rounded-lg shadow-sm">
              <ShieldCheck className="h-6 w-6 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-white flex items-center gap-2">
                FoodSafe-Indic
                <span className="text-xs bg-emerald-950 text-emerald-300 font-semibold px-2 py-0.5 rounded-full border border-emerald-800">
                  FSSAI RAG
                </span>
              </span>
              <p className="text-xs text-slate-400">
                Multilingual Packaging Compliance & Regulatory Violation Checker
              </p>
            </div>
          </div>

          <div className="flex space-x-1 sm:space-x-2">
            <button
              onClick={() => setActiveTab('audit')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
                activeTab === 'audit'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <ShieldAlert className="h-4 w-4" />
              <span>Audit & Chat</span>
            </button>

            <button
              onClick={() => setActiveTab('samples')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
                activeTab === 'samples'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Sparkles className="h-4 w-4" />
              <span>Viva Samples</span>
            </button>

            <button
              onClick={() => setActiveTab('admin')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
                activeTab === 'admin'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Scale className="h-4 w-4" />
              <span>Admin Deliberation</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
