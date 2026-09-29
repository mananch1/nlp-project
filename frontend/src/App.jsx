import React, { useState } from 'react';
import Header from './components/Header';
import ImageUploader from './components/ImageUploader';
import AuditResults from './components/AuditResults';
import ChatAssistant from './components/ChatAssistant';
import AdminDashboard from './components/AdminDashboard';
import ShowcaseSamples from './components/ShowcaseSamples';
import { PlusCircle, RotateCcw } from 'lucide-react';
import { auditImages, auditTextPayload } from './api';
import axios from 'axios';

const DEFAULT_GREETING = {
  role: 'assistant',
  content: 'नमस्ते! मैं FoodSafe-Indic हूँ, FSSAI खाद्य सुरक्षा एवं विनियामक AI सलाहकार। आप भारतीय खाद्य लेबलिंग, भ्रामक दावों, या पोषण मानकों पर कोई भी प्रश्न पूछ सकते हैं, या पैकेजिंग की तस्वीरें अपलोड कर सकते हैं।\n\nHello! I am FoodSafe-Indic, your AI legal advisor for Indian FSSAI food regulations. You can ask any legal doubt or upload 1-5 packaging photos to run an automated compliance audit.',
  timestamp: new Date().toLocaleTimeString()
};

export default function App() {
  const [activeTab, setActiveTab] = useState('audit');
  const [files, setFiles] = useState([]);
  const [auditData, setAuditData] = useState(null);
  const [chatHistory, setChatHistory] = useState([DEFAULT_GREETING]);
  const [loading, setLoading] = useState(false);

  const handleResetAll = () => {
    setFiles([]);
    setAuditData(null);
    setChatHistory([
      {
        role: 'assistant',
        content: 'नया सत्र आरंभ! आप FSSAI नियमों, पोषण मानकों, या पैकेजिंग दावों पर कोई भी प्रश्न पूछ सकते हैं, या नई तस्वीरें अपलोड कर सकते हैं।\n\nFresh session started! Ask any regulatory question or upload new packaging photos to audit.',
        timestamp: new Date().toLocaleTimeString()
      }
    ]);
  };

  const handleAnalyzeImages = async () => {
    if (files.length === 0) return;
    setLoading(true);
    try {
      const data = await auditImages(files);
      if (!data || typeof data !== 'object') {
        throw new Error('Received invalid response from server.');
      }
      setAuditData(data);
      // Seed product-specific chat greeting
      const lang = data.structured_data?.primary_language || 'en';
      const prodName = data.structured_data?.product_name || 'the product';
      setChatHistory([
        {
          role: 'assistant',
          content:
            lang === 'hi'
              ? `नमस्ते! मैंने "${prodName}" के पैकेजिंग लेबल का विश्लेषण कर लिया है। आप इस उत्पाद या FSSAI नियमों के संबंध में कोई भी प्रश्न पूछ सकते हैं।`
              : `Hello! I have analyzed the packaging label for "${prodName}". You can ask any doubts regarding ingredients, nutritional claims, or FSSAI legal guidelines.`,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    } catch (err) {
      console.error('Audit failed:', err);
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
        ? detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
        : (detail ? JSON.stringify(detail) : err.message);
      alert('Analysis failed: ' + msg);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadShowcaseSample = async (sample) => {
    setLoading(true);
    try {
      const data = await auditTextPayload(
        sample.sample_ocr_text,
        `showcase-${sample.id}`,
        sample.image_url
      );
      if (!data || typeof data !== 'object') {
        throw new Error('Received invalid response from server.');
      }
      setAuditData(data);

      const lang = data.structured_data?.primary_language || 'en';
      const prodName = data.structured_data?.product_name || sample.product_name || 'the product';
      const status = data.audit?.overall_status || 'ANALYZED';
      const passed = data.audit?.passed_checks ?? 0;
      const total = data.audit?.total_checks ?? 0;
      setChatHistory([
        {
          role: 'assistant',
          content:
            lang === 'hi'
              ? `नमस्ते! मैंने "${prodName}" के पैकेजिंग लेबल का विश्लेषण कर लिया है। आप इस उत्पाद या FSSAI नियमों के संबंध में कोई भी प्रश्न पूछ सकते हैं।`
              : `Loaded showcase sample "${prodName}". FSSAI Audit complete: ${status} (${passed}/${total} checks passed). Ask me any legal doubts!`,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
      setActiveTab('audit');
    } catch (err) {
      console.error('Failed to audit showcase sample:', err);
      alert('Failed to audit showcase sample: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'audit' && (
          <div className="space-y-6">
            {/* Top Bar when a product is actively being analyzed */}
            {auditData && (
              <div className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-sm flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span className="text-xs font-bold text-slate-700">Currently Auditing:</span>
                  <span className="text-xs font-bold text-slate-900 bg-emerald-50 text-emerald-800 px-2.5 py-1 rounded border border-emerald-200">
                    {auditData?.structured_data?.product_name || 'Packaged Food Product'}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleResetAll}
                  className="flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs px-3.5 py-1.5 rounded-lg shadow-sm transition-colors"
                >
                  <PlusCircle className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Start New Product Analysis</span>
                </button>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Column: Image Uploader OR Audit Results */}
              <div className="lg:col-span-7 space-y-6">
                {!auditData ? (
                  <div className="space-y-4">
                    <ImageUploader
                      files={files}
                      setFiles={setFiles}
                      onAnalyze={handleAnalyzeImages}
                      loading={loading}
                    />

                    {/* Quick Guidance Card */}
                    <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
                      <h3 className="text-sm font-bold text-slate-800 mb-1 flex items-center gap-2">
                        <span>💡 How to use FoodSafe-Indic:</span>
                      </h3>
                      <ul className="text-xs text-slate-600 space-y-1.5 list-disc list-inside">
                        <li><strong>Upload 1-5 Packaging Photos:</strong> Capture front label, nutrition table, ingredient list, or FSSAI license logo to trigger an automated compliance audit.</li>
                        <li><strong>Or Ask Any Doubt Directly:</strong> You can start chatting on the right panel right now—ask about Indian food laws, trans fat rules, deceptive claims, or banned additives!</li>
                        <li><strong>Or Try Showcase Viva Cases:</strong> Head to the <strong>"Viva Samples"</strong> tab to load real-world test cases with 1-click.</li>
                      </ul>
                    </div>
                  </div>
                ) : (
                  <AuditResults
                    auditData={auditData}
                    chatHistory={chatHistory}
                    onReportFiled={() => setActiveTab('admin')}
                  />
                )}
              </div>

              {/* Right Column: Always Active Interactive Chat Assistant */}
              <div className="lg:col-span-5 sticky top-20">
                <ChatAssistant
                  auditData={auditData}
                  chatHistory={chatHistory}
                  setChatHistory={setChatHistory}
                  onResetAll={handleResetAll}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'samples' && (
          <ShowcaseSamples onLoadSample={handleLoadShowcaseSample} />
        )}

        {activeTab === 'admin' && <AdminDashboard />}
      </main>

      <footer className="bg-slate-900 border-t border-slate-800 text-slate-400 text-xs py-4 text-center">
        FoodSafe-Indic • Capstone Project (Sem 7 NLP) • Powered by FSSAI Legal RAG, EasyOCR & Sarvam AI
      </footer>
    </div>
  );
}
