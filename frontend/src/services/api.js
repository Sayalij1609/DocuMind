/* ==========================================
   API Service Layer — Nexora Frontend
   All backend calls go through this file.
   ========================================== */

const API_BASE_URL = '/api/documents';

/**
 * Fetch wrapper with consistent error handling.
 */
async function request(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message = data?.detail || data?.message || `Request failed (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return data;
}

/* --- Health --- */

export async function checkHealth() {
  return request('/health');
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

export async function uploadDocument(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

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

      xhr.open('POST', `${API_BASE_URL}/upload`);
      xhr.send(formData);
    });
  }

  return request(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
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