import React, { useEffect, useState } from 'react';
import { Sparkles, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';
import { getShowcaseTestCases } from '../api';
import axios from 'axios';

export default function ShowcaseSamples({ onLoadSample }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCases = async () => {
      try {
        const data = await getShowcaseTestCases();
        setCases(data);
      } catch (err) {
        console.error('Failed to load showcase cases:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchCases();
  }, []);

  const handleSelectCase = async (c) => {
    try {
      // Simulate audit response using sample OCR text
      const parseRes = await axios.post('/api/chat/message', {
        session_id: `showcase-${c.id}`,
        query: "Perform initial compliance verification",
        language: "en"
      });
      // Trigger load in parent
      if (onLoadSample) {
        onLoadSample(c);
      }
    } catch (err) {
      console.error(err);
      if (onLoadSample) onLoadSample(c);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-emerald-800 to-teal-900 text-white rounded-xl p-6 shadow-sm">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-amber-400" />
          Viva Showcase & Ground-Truth Test Cases
        </h2>
        <p className="text-sm text-emerald-100 mt-1 max-w-2xl">
          Instantly evaluate and demonstrate FoodSafe-Indic on real-world Indian packaged goods scenarios
          without needing to upload new photos during your presentation.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {cases.map((c) => (
          <div
            key={c.id}
            className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                  {c.brand}
                </span>
                <span
                  className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                    c.expected_violations.length === 0
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {c.expected_violations.length === 0 ? '✓ Compliant' : '⛔ Non-Compliant'}
                </span>
              </div>

              <h3 className="text-base font-bold text-slate-900 mb-1">{c.title}</h3>
              <p className="text-xs text-slate-600 mb-3">{c.description}</p>

              {c.image_url && (
                <div className="mb-3 rounded-lg overflow-hidden border border-slate-200 bg-slate-50 relative group">
                  <img
                    src={c.image_url}
                    alt={c.title}
                    className="w-full h-36 object-contain bg-white group-hover:scale-105 transition-transform duration-200"
                  />
                  <a
                    href={c.image_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="absolute bottom-2 right-2 bg-slate-900/80 hover:bg-slate-900 text-white text-[10px] font-semibold px-2 py-1 rounded shadow backdrop-blur-sm transition-colors"
                  >
                    View Full Image ↗
                  </a>
                </div>
              )}

              {c.expected_violations.length > 0 ? (
                <div className="p-2.5 bg-red-50/70 border border-red-200 rounded-lg text-xs space-y-1 mb-4">
                  <span className="font-semibold text-red-900 block">Ground-Truth Non-Compliance:</span>
                  {c.expected_violations.map((v, i) => (
                    <p key={i} className="text-red-800 text-[11px] flex items-center gap-1">
                      • {v}
                    </p>
                  ))}
                </div>
              ) : (
                <div className="p-2.5 bg-green-50/70 border border-green-200 rounded-lg text-xs text-green-900 mb-4 flex items-center gap-1.5 font-medium">
                  <ShieldCheck className="h-4 w-4 text-green-600" />
                  Statutory declarations verified: All mandatory FSSAI parameters declared.
                </div>
              )}
            </div>

            <button
              onClick={() => handleSelectCase(c)}
              className="w-full bg-slate-900 hover:bg-emerald-700 text-white text-xs font-bold py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <span>Load This Showcase Product for Audit & Chat</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
