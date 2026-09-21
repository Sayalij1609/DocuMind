/* ==========================================
   API Service Layer — Documind Frontend
   All backend calls go through this file.
   ========================================== */

const BASE_URL = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL.replace(/\/+$/, '') : '';
const API_BASE_URL = `${BASE_URL}/api/documents`;

/**
 * Fetch wrapper with consistent error handling.
 */
async function request(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    if (data?.detail) {
      if (typeof data.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail
          .map((item) => item.msg || item.message || JSON.stringify(item))
          .join(', ');
      } else if (typeof data.detail === 'object') {
        message = data.detail.message || JSON.stringify(data.detail);
      }
    } else if (data?.message) {
      message = typeof data.message === 'string' ? data.message : JSON.stringify(data.message);
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return data;
}

/* --- Health --- */

export async function checkHealth() {
  return request(`${BASE_URL}/health`);
}

/* --- Documents --- */

export async function getDocuments(page = 1, pageSize = 100) {
  return request(`${API_BASE_URL}?page=${page}&page_size=${pageSize}`);
}

export async function getDocument(documentId) {
  return request(`${API_BASE_URL}/${documentId}`);
}

export async function deleteDocument(documentId) {
  return request(`${API_BASE_URL}/${documentId}`, { method: 'DELETE' });
}

/* --- Upload --- */

export async function uploadDocument(file, onProgress, autoProcess = false) {
  const formData = new FormData();
  formData.append('file', file);
  const uploadUrl = `${API_BASE_URL}/upload?auto_process=${Boolean(autoProcess)}`;

  // Use XMLHttpRequest for progress tracking
  if (onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      });

      xhr.addEventListener('load', () => {
        try {
          const data = JSON.parse(xhr.responseText);
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(data);
          } else {
            reject(new Error(data.detail || 'Upload failed'));
          }
        } catch {
          reject(new Error('Upload failed — invalid response'));
        }
      });

      xhr.addEventListener('error', () => reject(new Error('Upload failed — network error')));
      xhr.addEventListener('abort', () => reject(new Error('Upload cancelled')));

      xhr.open('POST', uploadUrl);
      xhr.send(formData);
    });
  }

  return request(uploadUrl, {
    method: 'POST',
    body: formData,
  });
}

/* --- Processing / Analysis Trigger --- */

export async function startDocumentProcessing(documentId) {
  return request(`${API_BASE_URL}/${documentId}/process`, {
    method: 'POST',
  });
}

/* --- Analysis --- */

export async function getDocumentAnalysis(documentId) {
  return request(`${API_BASE_URL}/${documentId}/analysis`);
}

/* --- Content --- */

export async function getDocumentContent(documentId) {
  return request(`${API_BASE_URL}/${documentId}/content`);
}

/* --- Validation --- */

export async function getDocumentValidation(documentId) {
  return request(`${API_BASE_URL}/${documentId}/validation`);
}

/* --- Duplicates --- */

export async function getDocumentDuplicates(documentId) {
  return request(`${API_BASE_URL}/${documentId}/duplicates`);
}

/* --- Anomaly --- */

export async function getDocumentAnomaly(documentId) {
  return request(`${API_BASE_URL}/${documentId}/anomaly`);
}

/* --- AI Semantic Analysis --- */

export async function askDocumentQuestion(documentId, question) {
  return request(`${API_BASE_URL}/${documentId}/qa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
}

export async function askMultiDocumentQuestion(question, documentIds = null) {
  return request(`${API_BASE_URL}/qa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, document_ids: documentIds }),
  });
}

export async function reindexDocumentRAG(documentId) {
  return request(`${API_BASE_URL}/${documentId}/reindex`, {
    method: 'POST',
  });
}

export async function reanalyzeDocument(documentId, apiKey = null) {
  return request(`${API_BASE_URL}/${documentId}/reanalyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey }),
  });
}

export async function getAIStatus() {
  return request(`${API_BASE_URL}/ai/status`);
}

export async function updateAIConfig(apiKey) {
  return request(`${API_BASE_URL}/ai/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey }),
  });
}