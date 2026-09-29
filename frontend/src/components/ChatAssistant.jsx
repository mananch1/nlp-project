import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Bot, User, AlertCircle, Loader2, Sparkles, RotateCcw, Volume2 } from 'lucide-react';
import { sendChatMessage, sendVoiceQuery } from '../api';

const QUICK_DOUBTS = [
  "bahi mujhe bata yeh acidity ke liya acche he kya?",
  "क्या इसमें कोई हानिकारक प्रिजर्वेटिव या एडिटिव्स हैं?",
  "Is the trans-fat and saturated fat within legal limits?",
  "Does this product have hidden added sugars (Maltodextrin)?",
  "Is sodium content safe for high BP / hypertension?",
  "Can school kids eat this snack regularly?"
];

export default function ChatAssistant({ auditData, chatHistory, setChatHistory, onResetAll }) {
  const [inputText, setInputText] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('hi');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [speechStatus, setSpeechStatus] = useState('');

  const speechRecognitionRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  // Setup Web Speech API for interactive real-time voice typing
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = selectedLanguage === 'hi' ? 'hi-IN' : 'en-IN';

        recognition.onstart = () => {
          setIsRecording(true);
          setSpeechStatus('Listening... Speak your question');
        };

        recognition.onresult = (event) => {
          let transcript = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
          }
          if (transcript) {
            setInputText(transcript);
          }
        };

        recognition.onerror = (event) => {
          console.warn('Web Speech recognition notice:', event.error);
          setIsRecording(false);
          setSpeechStatus('');
        };

        recognition.onend = () => {
          setIsRecording(false);
          setSpeechStatus('');
        };

        speechRecognitionRef.current = recognition;
      } catch (err) {
        console.warn('SpeechRecognition initialization error:', err);
      }
    }
  }, [selectedLanguage]);

  const handleNewChat = () => {
    const lang = selectedLanguage;
    const isHindi = lang === 'hi';
    const prodName = auditData?.structured_data?.product_name;

    const initialGreeting = prodName
      ? isHindi
        ? `नया संवाद आरंभ! मैंने "${prodName}" के लेबल की जानकारी सुरक्षित रखी है। आप एसिडिटी, प्रिजर्वेटिव्स, ट्रांस फैट, या FSSAI नियमों पर कोई भी सवाल पूछ सकते हैं।`
        : `New chat session started for "${prodName}". Ask any question regarding acidity, preservatives, trans fat, or statutory FSSAI compliance.`
      : isHindi
      ? `नमस्ते! मैं FoodSafe-Indic हूँ, भारतीय खाद्य सुरक्षा एवं मानक प्राधिकरण (FSSAI) का कानूनी AI सहायक। आप पैकेजिंग नियमों, मिलावट, या लेबलिंग मानकों पर कोई भी सवाल पूछ सकते हैं।`
      : `Hello! I am FoodSafe-Indic, your AI legal advisor for Indian FSSAI food safety regulations. You can ask any question about labelling rules, nutritional claims, or upload packaging photos to audit.`;

    setChatHistory([
      {
        role: 'assistant',
        content: initialGreeting,
        timestamp: new Date().toLocaleTimeString()
      }
    ]);
  };

  const handleSend = async (queryText = null) => {
    const textToSend = queryText || inputText;
    if (!textToSend.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString()
    };
    setChatHistory((prev) => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

    try {
      const res = await sendChatMessage({
        session_id: auditData?.session_id || 'manual_session',
        query: textToSend,
        language: selectedLanguage,
        structured_data: auditData?.structured_data,
        conversation_history: chatHistory
      });

      const botMessage = {
        role: 'assistant',
        content: res.response,
        timestamp: new Date().toLocaleTimeString(),
        cited_clauses: res.cited_clauses,
        potential_violation_detected: res.potential_violation_detected,
        violation_details: res.violation_details
      };
      setChatHistory((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      setChatHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, could not process query. Please ensure backend server is running.',
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    // 1. Try Browser Web Speech Recognition first
    if (speechRecognitionRef.current) {
      try {
        speechRecognitionRef.current.lang = selectedLanguage === 'hi' ? 'hi-IN' : 'en-IN';
        speechRecognitionRef.current.start();
        setIsRecording(true);
        return;
      } catch (err) {
        console.warn('Web Speech start failed, falling back to MediaRecorder:', err);
      }
    }

    // 2. Fallback to MediaRecorder Audio stream upload
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await handleVoiceUpload(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setSpeechStatus('Recording audio...');
    } catch (err) {
      console.error('Mic access denied:', err);
      alert('Microphone access was denied or not supported on this browser.');
    }
  };

  const stopRecording = () => {
    if (speechRecognitionRef.current && isRecording) {
      try {
        speechRecognitionRef.current.stop();
      } catch (e) {}
    }
    if (mediaRecorderRef.current && isRecording) {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {}
    }
    setIsRecording(false);
    setSpeechStatus('');
  };

  const handleVoiceUpload = async (audioBlob) => {
    setLoading(true);
    try {
      const sessionId = auditData?.session_id || 'voice_session';
      const rawOcr = auditData?.raw_ocr_text || '';
      const res = await sendVoiceQuery(
        audioBlob,
        sessionId,
        rawOcr,
        selectedLanguage === 'hi' ? 'hi-IN' : 'en-IN',
        auditData?.structured_data
      );

      const userMessage = {
        role: 'user',
        content: `🎙️ Spoken Doubt (${selectedLanguage}): "${res.original_query}"`,
        timestamp: new Date().toLocaleTimeString()
      };
      const botMessage = {
        role: 'assistant',
        content: res.response,
        timestamp: new Date().toLocaleTimeString(),
        cited_clauses: res.cited_clauses,
        potential_violation_detected: res.potential_violation_detected
      };
      setChatHistory((prev) => [...prev, userMessage, botMessage]);
    } catch (err) {
      console.error('Voice query error:', err);
      alert('Voice query failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col h-[580px]">
      {/* Chat Header */}
      <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50 rounded-t-xl">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-emerald-600" />
          <div>
            <h3 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
              <span>Interactive Compliance Chat</span>
              <span className="text-[10px] font-semibold bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded">
                Indic RAG
              </span>
            </h3>
            <p className="text-[11px] text-slate-500">
              {auditData?.structured_data?.product_name
                ? `Auditing: ${auditData.structured_data.product_name}`
                : 'Ask questions about ingredients, health concerns, or FSSAI laws.'}
            </p>
          </div>
        </div>

        {/* Header Actions: New Chat & Language Selector */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleNewChat}
            title="Start a new conversation thread"
            className="flex items-center gap-1 bg-white hover:bg-slate-100 text-slate-700 font-semibold px-2.5 py-1 rounded border border-slate-300 transition-colors text-xs shadow-2xs"
          >
            <RotateCcw className="h-3.5 w-3.5 text-emerald-600" />
            <span>New Chat</span>
          </button>

          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="bg-white border border-slate-300 rounded px-2 py-1 text-slate-700 text-xs font-semibold focus:outline-none focus:border-emerald-600"
          >
            <option value="hi">हिन्दी (Hindi)</option>
            <option value="en">English</option>
            <option value="ta">தமிழ் (Tamil)</option>
            <option value="te">తెలుగు (Telugu)</option>
            <option value="bn">বাংলা (Bengali)</option>
          </select>
        </div>
      </div>

      {/* Quick Doubt Chips */}
      <div className="px-4 py-2 bg-slate-50/70 border-b border-slate-200 flex items-center gap-1.5 overflow-x-auto text-[11px]">
        <span className="text-slate-400 shrink-0 font-medium flex items-center gap-1">
          <Sparkles className="h-3 w-3 text-amber-500" /> Quick Queries:
        </span>
        {QUICK_DOUBTS.map((doubt, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSend(doubt)}
            className="px-2.5 py-1 bg-white hover:bg-emerald-50 text-slate-600 hover:text-emerald-700 rounded-full border border-slate-200 shrink-0 transition-colors"
          >
            {doubt}
          </button>
        ))}
      </div>

      {/* Listening Status Bar */}
      {isRecording && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-1.5 flex items-center justify-between text-xs text-red-700">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-red-600 rounded-full animate-ping" />
            <span className="font-semibold">{speechStatus || 'Listening... Speak now'}</span>
          </div>
          <button
            type="button"
            onClick={stopRecording}
            className="text-xs bg-red-600 hover:bg-red-700 text-white font-medium px-2 py-0.5 rounded transition-colors"
          >
            Stop
          </button>
        </div>
      )}

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {chatHistory.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 p-6">
            <Bot className="h-10 w-10 text-slate-300 mb-2" />
            <p className="text-sm font-medium text-slate-600">No queries asked yet</p>
            <p className="text-xs max-w-sm mt-1">
              Ask doubts by typing in Hindi, Hinglish, or English, or click the microphone to speak your question directly.
            </p>
          </div>
        ) : (
          chatHistory.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0 text-xs mt-1">
                  <Bot className="h-4 w-4" />
                </div>
              )}

              <div
                className={`max-w-[88%] rounded-xl px-3.5 py-2.5 text-xs ${
                  msg.role === 'user'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-800 border border-slate-200'
                }`}
              >
                <div className="whitespace-pre-line leading-relaxed">{msg.content}</div>

                {msg.potential_violation_detected && (
                  <div className="mt-2 p-1.5 bg-red-100 text-red-800 font-semibold rounded border border-red-200 flex items-center gap-1.5">
                    <AlertCircle className="h-3.5 w-3.5 text-red-600 shrink-0" />
                    <span>Potential Regulatory Breach Flagged</span>
                  </div>
                )}

                <span
                  className={`block text-[10px] mt-1 text-right ${
                    msg.role === 'user' ? 'text-emerald-100' : 'text-slate-400'
                  }`}
                >
                  {msg.timestamp}
                </span>
              </div>

              {msg.role === 'user' && (
                <div className="w-7 h-7 rounded-full bg-slate-800 text-white flex items-center justify-center shrink-0 text-xs mt-1">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))
        )}

        {loading && (
          <div className="flex gap-2 items-center text-slate-400 text-xs">
            <Bot className="h-5 w-5 text-emerald-600" />
            <div className="flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200">
              <Loader2 className="h-3 w-3 animate-spin text-emerald-600" />
              <span>Analyzing product facts with FSSAI regulations...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="p-3 border-t border-slate-200 bg-white rounded-b-xl flex items-center gap-2">
        <button
          type="button"
          onClick={isRecording ? stopRecording : startRecording}
          title={isRecording ? 'Stop Recording' : 'Speak doubt in Hindi or English'}
          className={`p-2.5 rounded-lg transition-colors ${
            isRecording
              ? 'bg-red-600 text-white animate-pulse'
              : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
          }`}
        >
          {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
        </button>

        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={`Ask doubt in ${selectedLanguage === 'hi' ? 'Hindi / Hinglish' : 'English'} (e.g. Acidity ke liye accha hai kya?)...`}
          className="flex-1 bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-emerald-600"
        />

        <button
          type="button"
          disabled={loading || !inputText.trim()}
          onClick={() => handleSend()}
          className="p-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
