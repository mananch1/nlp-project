import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Send,
  Scale,
  Award,
  Calendar,
  Layers,
  UtensilsCrossed,
  Tag
} from 'lucide-react';
import { reportIncident } from '../api';

export default function AuditResults({ auditData, chatHistory, onReportFiled }) {
  const [reporting, setReporting] = useState(false);
  const [userNotes, setUserNotes] = useState('');
  const [filedUuid, setFiledUuid] = useState(null);

  if (!auditData) return null;

  const structured_data = auditData.structured_data || {};
  const audit = auditData.audit || {
    total_checks: 0,
    passed_checks: 0,
    failed_checks: 0,
    warning_checks: 0,
    overall_status: 'UNKNOWN',
    overall_confidence: 0.9,
    items: []
  };
  const session_id = auditData.session_id || '';
  const image_urls = auditData.image_urls || [];
  const raw_ocr_text = auditData.raw_ocr_text || '';
  const nutrition = structured_data.nutrition || {};
  const auditItems = Array.isArray(audit.items) ? audit.items : [];

  const handleFileReport = async () => {
    setReporting(true);
    try {
      const flagged = auditItems.filter((itm) => itm.status === 'FAIL' || itm.status === 'WARNING');
      const payload = {
        session_id,
        product_name: structured_data.product_name || 'Unspecified Product',
        brand: structured_data.brand || 'Unspecified Brand',
        image_urls,
        raw_ocr_text,
        structured_data,
        conversation_history: chatHistory || [],
        flagged_violations: flagged,
        severity: (audit.failed_checks ?? 0) > 0 ? 'CRITICAL' : 'MAJOR',
        confidence_score: audit.overall_confidence ?? 0.9,
        user_notes: userNotes
      };
      const res = await reportIncident(payload);
      setFiledUuid(res.report_uuid);
      if (onReportFiled) onReportFiled(res);
    } catch (err) {
      console.error('Failed to report incident:', err);
      alert('Failed to submit incident report: ' + (err.response?.data?.detail || err.message));
    } finally {
      setReporting(false);
    }
  };

  const isCompliant = (audit.overall_status || '').toUpperCase() === 'COMPLIANT';
  const isSuspected = (audit.overall_status || '').toUpperCase() === 'SUSPECTED_VIOLATION';

  return (
    <div className="space-y-6">
      {/* Product Summary Header Card */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900">
                {structured_data.product_name || 'Packaged Product'}
              </h2>
              {structured_data.veg_nonveg === 'VEG' && (
                <span className="flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded border border-green-600 text-green-700 bg-green-50">
                  <span className="w-2 h-2 rounded-full bg-green-600 inline-block"></span>
                  VEG
                </span>
              )}
              {structured_data.veg_nonveg === 'NON_VEG' && (
                <span className="flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded border border-amber-800 text-amber-900 bg-amber-50">
                  <span className="w-2 h-2 rounded-full bg-amber-800 inline-block"></span>
                  NON-VEG
                </span>
              )}
            </div>
            <p className="text-sm text-slate-500 font-medium mt-0.5">
              Brand: {structured_data.brand || 'Unspecified'} | Primary Script:{' '}
              {structured_data.detected_scripts?.join(', ') || 'Latin'}
            </p>
          </div>

          {/* Quick Badges */}
          <div className="flex flex-wrap gap-2 text-xs">
            <span
              className={`px-2.5 py-1 rounded-md font-medium border ${
                structured_data.fssai_license
                  ? 'bg-slate-100 text-slate-800 border-slate-300'
                  : 'bg-red-50 text-red-700 border-red-200'
              }`}
            >
              FSSAI Lic: {structured_data.fssai_license || 'MISSING'}
            </span>
            {structured_data.expiry_date && (
              <span className="px-2.5 py-1 bg-slate-100 text-slate-800 rounded-md font-medium border border-slate-300 flex items-center gap-1">
                <Calendar className="h-3 w-3 text-slate-500" />
                Exp: {structured_data.expiry_date}
              </span>
            )}
            {structured_data.net_quantity && (
              <span className="px-2.5 py-1 bg-slate-100 text-slate-800 rounded-md font-medium border border-slate-300">
                Net Qty: {structured_data.net_quantity}
              </span>
            )}
          </div>
        </div>

        {/* Marketing Claims */}
        {Array.isArray(structured_data.claims) && structured_data.claims.length > 0 && (
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold text-slate-500 flex items-center gap-1">
              <Tag className="h-3.5 w-3.5" />
              Detected Claims:
            </span>
            {structured_data.claims.map((claim, idx) => (
              <span
                key={idx}
                className="text-xs font-semibold px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded-full"
              >
                {claim}
              </span>
            ))}
          </div>
        )}

        {/* Ingredients & Nutrition Facts Grid */}
        <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Ingredients */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center gap-1">
              <UtensilsCrossed className="h-3.5 w-3.5" />
              Declared Ingredients
            </h4>
            {Array.isArray(structured_data.ingredients) && structured_data.ingredients.length > 0 ? (
              <div className="flex flex-wrap gap-1.5 mt-1">
                {structured_data.ingredients.map((ingr, i) => (
                  <span
                    key={i}
                    className="text-xs px-2 py-0.5 bg-slate-100 text-slate-700 rounded border border-slate-200"
                  >
                    {ingr}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No structured ingredients detected.</p>
            )}

            {structured_data.allergen_advice && (
              <div className="mt-2 text-xs font-semibold text-amber-800 bg-amber-50 p-2 rounded border border-amber-200 whitespace-pre-line">
                ⚠️ {structured_data.allergen_advice}
              </div>
            )}
          </div>

          {/* Nutrition Table */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center gap-1">
              <Layers className="h-3.5 w-3.5" />
              Nutrition Facts (per 100g / serve)
            </h4>
            <div className="text-xs grid grid-cols-2 gap-x-4 gap-y-1 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
              <div>
                <span className="text-slate-500">Energy:</span>{' '}
                <span className="font-semibold text-slate-800">
                  {nutrition.energy_kcal ?? '—'} kcal
                </span>
              </div>
              <div>
                <span className="text-slate-500">Protein:</span>{' '}
                <span className="font-semibold text-slate-800">
                  {nutrition.protein_g ?? '—'} g
                </span>
              </div>
              <div>
                <span className="text-slate-500">Total Sugars:</span>{' '}
                <span className="font-semibold text-slate-800">
                  {nutrition.total_sugars_g ?? '—'} g
                </span>
              </div>
              <div>
                <span className="text-slate-500">Added Sugars:</span>{' '}
                <span className="font-semibold text-slate-800">
                  {nutrition.added_sugars_g ?? '—'} g
                </span>
              </div>
              <div>
                <span className="text-slate-500">Saturated Fat:</span>{' '}
                <span
                  className={`font-semibold ${
                    nutrition.saturated_fat_g === null || nutrition.saturated_fat_g === undefined
                      ? 'text-red-600'
                      : 'text-slate-800'
                  }`}
                >
                  {nutrition.saturated_fat_g ?? 'MISSING'} g
                </span>
              </div>
              <div>
                <span className="text-slate-500">Trans Fat:</span>{' '}
                <span
                  className={`font-semibold ${
                    nutrition.trans_fat_g === null || nutrition.trans_fat_g === undefined
                      ? 'text-red-600'
                      : 'text-slate-800'
                  }`}
                >
                  {nutrition.trans_fat_g ?? 'MISSING'} g
                </span>
              </div>
              <div>
                <span className="text-slate-500">Sodium:</span>{' '}
                <span className="font-semibold text-slate-800">
                  {nutrition.sodium_mg ?? '—'} mg
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Baseline Compliance Audit Summary Card */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Scale className="h-5 w-5 text-emerald-600" />
            <h3 className="text-base font-bold text-slate-900">
              FSSAI Automated Compliance Audit
            </h3>
          </div>

          {/* Status Badge */}
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase border ${
              isCompliant
                ? 'bg-green-100 text-green-800 border-green-300'
                : isSuspected
                ? 'bg-amber-100 text-amber-800 border-amber-300'
                : 'bg-red-100 text-red-800 border-red-300'
            }`}
          >
            {isCompliant
              ? '✓ Compliant'
              : isSuspected
              ? '⚠️ Suspected Violation'
              : '⛔ Non-Compliant (Violations Detected)'}
          </span>
        </div>

        {/* Audit Metric Counters */}
        <div className="grid grid-cols-4 gap-2 mb-4 text-center">
          <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-xs text-slate-500 font-medium">Total Checks</span>
            <p className="text-base font-bold text-slate-800">{audit.total_checks ?? 0}</p>
          </div>
          <div className="p-2 bg-green-50 rounded-lg border border-green-100">
            <span className="text-xs text-green-700 font-medium">Passed</span>
            <p className="text-base font-bold text-green-800">{audit.passed_checks ?? 0}</p>
          </div>
          <div className="p-2 bg-red-50 rounded-lg border border-red-100">
            <span className="text-xs text-red-700 font-medium">Failed</span>
            <p className="text-base font-bold text-red-800">{audit.failed_checks ?? 0}</p>
          </div>
          <div className="p-2 bg-amber-50 rounded-lg border border-amber-100">
            <span className="text-xs text-amber-700 font-medium">Warnings</span>
            <p className="text-base font-bold text-amber-800">{audit.warning_checks ?? 0}</p>
          </div>
        </div>

        {/* Statutory Audit Items Checklist */}
        <div className="space-y-3">
          {auditItems.map((item, idx) => (
            <div
              key={idx}
              className={`p-3.5 rounded-lg border text-sm transition-all ${
                item.status === 'PASS'
                  ? 'bg-green-50/40 border-green-200'
                  : item.status === 'FAIL'
                  ? 'bg-red-50/60 border-red-200'
                  : 'bg-amber-50/50 border-amber-200'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2">
                  {item.status === 'PASS' && <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5 shrink-0" />}
                  {item.status === 'FAIL' && <XCircle className="h-5 w-5 text-red-600 mt-0.5 shrink-0" />}
                  {item.status === 'WARNING' && <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />}
                  <div>
                    <span className="font-semibold text-slate-900 block">{item.title}</span>
                    <span className="text-xs text-slate-500 font-medium">
                      {item.section} • {item.regulation}
                    </span>
                  </div>
                </div>

                <span
                  className={`text-[11px] font-bold px-2 py-0.5 rounded uppercase ${
                    item.status === 'PASS'
                      ? 'bg-green-100 text-green-800'
                      : item.status === 'FAIL'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}
                >
                  {item.status} ({item.severity})
                </span>
              </div>

              <div className="mt-2 text-xs text-slate-700 pl-7">
                <p>
                  <strong>Evidence:</strong> {item.evidence}
                </p>
                <p className="text-slate-500 mt-1 italic">
                  <strong>Statute:</strong> {item.statutory_clause}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Deliberation Escalation Box */}
        {(audit.failed_checks ?? 0) > 0 || (audit.warning_checks ?? 0) > 0 ? (
          <div className="mt-5 p-4 bg-slate-900 text-white rounded-xl">
            <h4 className="font-bold text-sm flex items-center gap-2 text-amber-400">
              <Scale className="h-4 w-4" />
              Hybrid Escalation: File Regulatory Incident for Deliberation
            </h4>
            <p className="text-xs text-slate-300 mt-1">
              Genuine packaging non-compliance detected. You can submit this incident dossier along with
              your packaging photos, extracted OCR facts, and query logs to the backend database for deliberation.
            </p>

            {filedUuid ? (
              <div className="mt-3 p-2.5 bg-emerald-900/60 border border-emerald-500 rounded-lg text-emerald-200 text-xs flex items-center justify-between">
                <span>
                  ✓ <strong>Dossier Filed Successfully!</strong> Reference ID: <code>{filedUuid}</code>
                </span>
                <span className="text-[11px] bg-emerald-800 px-2 py-0.5 rounded text-white font-medium">
                  Logged in Admin Queue
                </span>
              </div>
            ) : (
              <div className="mt-3 flex flex-col sm:flex-row gap-2">
                <input
                  type="text"
                  placeholder="Optional notes for the review officer..."
                  value={userNotes}
                  onChange={(e) => setUserNotes(e.target.value)}
                  className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-amber-400"
                />
                <button
                  type="button"
                  disabled={reporting}
                  onClick={handleFileReport}
                  className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs px-4 py-2 rounded-lg transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50"
                >
                  <Send className="h-3.5 w-3.5" />
                  <span>{reporting ? 'Filing Dossier...' : 'File for Deliberation'}</span>
                </button>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
