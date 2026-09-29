import React, { useEffect, useState } from 'react';
import {
  Scale,
  FileDown,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  ExternalLink,
  MessageSquare,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';
import { getIncidents, updateIncident } from '../api';

export default function AdminDashboard() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [officerNotes, setOfficerNotes] = useState('');
  const [updating, setUpdating] = useState(false);

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      const data = await getIncidents();
      setIncidents(data);
      if (data.length > 0 && !selectedIncident) {
        setSelectedIncident(data[0]);
        setOfficerNotes(data[0].officer_notes || '');
      }
    } catch (err) {
      console.error('Failed to fetch incidents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, []);

  const handleSelectIncident = (inc) => {
    setSelectedIncident(inc);
    setOfficerNotes(inc.officer_notes || '');
  };

  const handleStatusChange = async (newStatus) => {
    if (!selectedIncident) return;
    setUpdating(true);
    try {
      const updated = await updateIncident(selectedIncident.report_uuid, {
        status: newStatus,
        officer_notes: officerNotes
      });
      setSelectedIncident(updated);
      setIncidents(incidents.map((i) => (i.report_uuid === updated.report_uuid ? updated : i)));
    } catch (err) {
      console.error('Failed to update status:', err);
      alert('Update failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 text-white rounded-xl p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Scale className="h-5 w-5 text-amber-400" />
            Official Regulatory Deliberation Board
          </h2>
          <p className="text-xs text-slate-400">
            Deliberate on consumer-filed food safety incidents, inspect packaging evidence, and escalate verified violations to FSSAI.
          </p>
        </div>
        <button
          onClick={fetchIncidents}
          disabled={loading}
          className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-3 py-2 rounded-lg border border-slate-700 transition-colors flex items-center gap-1.5"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Queue
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-500">Total Dossiers</span>
          <p className="text-xl font-bold text-slate-900">{incidents.length}</p>
        </div>
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-amber-600">Pending Review</span>
          <p className="text-xl font-bold text-amber-700">
            {incidents.filter((i) => i.status === 'PENDING_REVIEW').length}
          </p>
        </div>
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-red-600">Verified Violations</span>
          <p className="text-xl font-bold text-red-700">
            {incidents.filter((i) => i.status === 'VERIFIED_VIOLATION').length}
          </p>
        </div>
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-green-600">Dismissed</span>
          <p className="text-xl font-bold text-green-700">
            {incidents.filter((i) => i.status === 'DISMISSED').length}
          </p>
        </div>
      </div>

      {/* Main Split: Dossier List vs Detail Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Incident List */}
        <div className="lg:col-span-5 bg-white rounded-xl shadow-sm border border-slate-200 p-4 space-y-2 h-[640px] overflow-y-auto">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
            Incident Queue ({incidents.length})
          </h3>
          {incidents.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-xs">
              No regulatory incidents currently filed.
            </div>
          ) : (
            incidents.map((inc) => (
              <div
                key={inc.report_uuid}
                onClick={() => handleSelectIncident(inc)}
                className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                  selectedIncident?.report_uuid === inc.report_uuid
                    ? 'border-emerald-600 bg-emerald-50/40 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300 bg-white'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-slate-900 truncate max-w-[180px]">
                    {inc.product_name}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                      inc.status === 'VERIFIED_VIOLATION'
                        ? 'bg-red-100 text-red-800'
                        : inc.status === 'PENDING_REVIEW'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-green-100 text-green-800'
                    }`}
                  >
                    {inc.status.replace('_', ' ')}
                  </span>
                </div>

                <p className="text-slate-500">
                  Brand: {inc.brand} • Lic: {inc.fssai_license || 'None'}
                </p>
                <p className="text-[10px] text-slate-400 mt-1 flex items-center justify-between">
                  <span>ID: {inc.report_uuid}</span>
                  <span>{new Date(inc.created_at).toLocaleDateString()}</span>
                </p>
              </div>
            ))
          )}
        </div>

        {/* Selected Incident Detail Dossier */}
        <div className="lg:col-span-7 bg-white rounded-xl shadow-sm border border-slate-200 p-5 h-[640px] overflow-y-auto flex flex-col justify-between">
          {selectedIncident ? (
            <div className="space-y-4">
              {/* Dossier Header */}
              <div className="border-b border-slate-200 pb-3 flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-slate-900">
                      {selectedIncident.product_name}
                    </h3>
                    <span className="text-xs bg-slate-100 text-slate-700 font-mono px-2 py-0.5 rounded border border-slate-300">
                      {selectedIncident.report_uuid}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Brand: {selectedIncident.brand} | FSSAI License:{' '}
                    {selectedIncident.fssai_license || 'MISSING'} | Severity:{' '}
                    <strong className="text-red-600">{selectedIncident.severity}</strong>
                  </p>
                </div>

                {/* PDF Export Button */}
                <a
                  href={`/api/incidents/${selectedIncident.report_uuid}/pdf`}
                  download
                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
                >
                  <FileDown className="h-4 w-4" />
                  <span>Download PDF Dossier</span>
                </a>
              </div>

              {/* Uploaded Evidence Photos */}
              {selectedIncident.image_paths && selectedIncident.image_paths.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                    Packaging Evidence Photos:
                  </h4>
                  <div className="flex gap-2 overflow-x-auto pb-1">
                    {selectedIncident.image_paths.map((imgUrl, i) => (
                      <a
                        key={i}
                        href={imgUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="w-20 h-20 rounded border border-slate-200 overflow-hidden shrink-0 group relative"
                      >
                        <img src={imgUrl} alt="evidence" className="w-full h-full object-cover" />
                        <span className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-[10px] transition-opacity">
                          View
                        </span>
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Flagged Violations */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Flagged Statutory Breaches:
                </h4>
                <div className="space-y-2">
                  {selectedIncident.flagged_violations?.map((v, i) => (
                    <div key={i} className="p-2.5 bg-red-50/70 border border-red-200 rounded-lg text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-red-900">{v.title}</span>
                        <span className="text-[10px] bg-red-200 text-red-900 px-1.5 py-0.5 rounded font-mono">
                          {v.section}
                        </span>
                      </div>
                      <p className="text-slate-700 mt-1">
                        <strong>Evidence:</strong> {v.evidence}
                      </p>
                      <p className="text-slate-500 text-[11px] italic mt-0.5">
                        Statute: {v.statutory_clause}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Officer Deliberation Controls */}
              <div className="border-t border-slate-200 pt-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Deliberation Notes & Action:
                </h4>
                <textarea
                  rows={2}
                  value={officerNotes}
                  onChange={(e) => setOfficerNotes(e.target.value)}
                  placeholder="Enter regulatory review remarks or grounds for escalation..."
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs focus:outline-none focus:border-emerald-600"
                />

                <div className="mt-2 flex flex-wrap gap-2 justify-end">
                  <button
                    disabled={updating}
                    onClick={() => handleStatusChange('DISMISSED')}
                    className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
                  >
                    Dismiss Case
                  </button>
                  <button
                    disabled={updating}
                    onClick={() => handleStatusChange('VERIFIED_VIOLATION')}
                    className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg transition-colors"
                  >
                    Mark as Verified Violation
                  </button>
                  <button
                    disabled={updating}
                    onClick={() => handleStatusChange('ESCALATED_FSSAI')}
                    className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-lg transition-colors"
                  >
                    Escalate to FSSAI Grievance Portal
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-400 text-xs">
              Select an incident from the queue to deliberate.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
