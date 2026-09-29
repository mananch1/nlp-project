import axios from 'axios';

const API_BASE = '/api';

export const auditImages = async (files) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });
  const res = await axios.post(`${API_BASE}/audit/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
};

export const sendChatMessage = async (data) => {
  const res = await axios.post(`${API_BASE}/chat/message`, data);
  return res.data;
};

export const sendVoiceQuery = async (audioBlob, sessionId, rawOcrText, languageCode = 'hi-IN', structuredData = null) => {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'query.wav');
  formData.append('session_id', sessionId);
  formData.append('raw_ocr_text', rawOcrText || '');
  formData.append('language_code', languageCode);
  if (structuredData) {
    formData.append('structured_data', JSON.stringify(structuredData));
  }

  const res = await axios.post(`${API_BASE}/chat/voice`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
};

export const reportIncident = async (incidentData) => {
  const res = await axios.post(`${API_BASE}/incidents/report`, incidentData);
  return res.data;
};

export const getIncidents = async () => {
  const res = await axios.get(`${API_BASE}/incidents`);
  return res.data;
};

export const updateIncident = async (uuid, data) => {
  const res = await axios.patch(`${API_BASE}/incidents/${uuid}`, data);
  return res.data;
};

export const getShowcaseTestCases = async () => {
  const res = await axios.get(`${API_BASE}/test-cases`);
  return res.data;
};

export const auditTextPayload = async (text, sessionId, imageUrl) => {
  const res = await axios.post(`${API_BASE}/audit/audit-text`, {
    text,
    session_id: sessionId,
    image_url: imageUrl
  });
  return res.data;
};
