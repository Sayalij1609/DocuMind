import { useState, useRef } from 'react';
import {
  Upload,
  FileCheck,
  X,
  AlertCircle,
  Sparkles,
  ArrowRight,
  RefreshCw,
  FileText,
  CheckCircle2,
  Settings2,
  Play,
} from 'lucide-react';
import { uploadDocument, startDocumentProcessing } from '../services/api';
import StatusBadge from './StatusBadge';
import './FileUploader.css';

const ACCEPTED_TYPES = ['.pdf', '.jpg', '.jpeg', '.png'];
const MAX_SIZE_MB = 50;

export default function FileUploader({ onUploadComplete, onStartAnalysis }) {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [autoProcess, setAutoProcess] = useState(false);
  const [result, setResult] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const validateFile = (f) => {
    const ext = '.' + f.name.split('.').pop().toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext)) {
      return `Unsupported file format (${ext}). Supported formats: ${ACCEPTED_TYPES.join(', ')}`;
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File exceeds maximum allowed size of ${MAX_SIZE_MB}MB (${(f.size / 1024 / 1024).toFixed(1)}MB).`;
    }
    return null;
  };

  const handleFile = (f) => {
    setError(null);
    setResult(null);
    const validationError = validateFile(f);
    if (validationError) {
      setError(validationError);
      return;
    }
    setFile(f);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => setDragActive(false);

  const handleInputChange = (e) => {
    if (e.target.files?.[0]) handleFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      const res = await uploadDocument(file, (pct) => setProgress(pct), autoProcess);
      setResult(res);
      setFile(null);
      if (autoProcess) {
        onUploadComplete?.(res, true);
      } else {
        onUploadComplete?.(res, false);
      }
    } catch (err) {
      setError(err.message || 'Upload failed. Please check backend connection.');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const handleTriggerAnalysis = async () => {
    if (!result?.document_id || analyzing) return;
    setAnalyzing(true);
    try {
      await startDocumentProcessing(result.document_id);
      if (onStartAnalysis) {
        onStartAnalysis(result.document_id);
      } else if (onUploadComplete) {
        onUploadComplete(result, true);
      }
    } catch (err) {
      setError(err.message || 'Failed to trigger document analysis.');
      setAnalyzing(false);
    }
  };

  const clearAll = () => {
    setFile(null);
    setError(null);
    setResult(null);
    setAnalyzing(false);
    if (inputRef.current) inputRef.current.value = '';
  };

  const formatSize = (bytes) => {
    if (!bytes && bytes !== 0) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div className="file-uploader">
      {/* Upload Drop Zone — when no result yet */}
      {!result && (
        <>
          <div
            className={`drop-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => !file && inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleInputChange}
              hidden
            />

            {!file ? (
              <div className="drop-content">
                <div className="drop-icon-wrapper">
                  <Upload size={36} className="drop-icon" />
                </div>
                <p className="drop-title">
                  Choose a document or drag & drop here
                </p>
                <p className="drop-subtitle">
                  Invoices, Receipts, Contracts, Resumes & Financial Statements
                </p>
                <div className="drop-formats-pills">
                  <span className="format-pill">PDF</span>
                  <span className="format-pill">JPG</span>
                  <span className="format-pill">JPEG</span>
                  <span className="format-pill">PNG</span>
                  <span className="size-pill">Max {MAX_SIZE_MB}MB</span>
                </div>
              </div>
            ) : (
              <div className="staged-file-card">
                <div className="staged-file-icon">
                  <FileText size={32} />
                </div>
                <div className="staged-file-details">
                  <div className="staged-file-name" title={file.name}>
                    {file.name}
                  </div>
                  <div className="staged-file-meta">
                    <span>{formatSize(file.size)}</span>
                    <span className="meta-bullet">•</span>
                    <span className="staged-type-tag">
                      {file.name.split('.').pop().toUpperCase()}
                    </span>
                    <span className="meta-bullet">•</span>
                    <span className="staged-ready-badge">Ready to Upload</span>
                  </div>
                </div>
                <button
                  className="btn-ghost file-remove-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    clearAll();
                  }}
                  title="Remove file"
                  type="button"
                >
                  <X size={18} />
                </button>
              </div>
            )}
          </div>

          {/* Staged Options & Upload Actions */}
          {file && (
            <div className="staged-actions-panel animate-fade-in">
              <div className="upload-options-row">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={autoProcess}
                    onChange={(e) => setAutoProcess(e.target.checked)}
                    disabled={uploading}
                  />
                  <span className="checkbox-text">
                    <strong>Auto-start analysis</strong> immediately after upload
                  </span>
                </label>
              </div>

              <div className="upload-buttons-row">
                <button
                  className="btn btn-primary upload-btn-main"
                  onClick={handleUpload}
                  disabled={uploading}
                  type="button"
                >
                  {uploading ? (
                    <>
                      <span className="upload-spinner" />
                      <span>Uploading {progress}%</span>
                    </>
                  ) : (
                    <>
                      <Upload size={16} />
                      <span>{autoProcess ? 'Upload & Analyze Now' : 'Upload Document'}</span>
                    </>
                  )}
                </button>

                <button
                  className="btn btn-secondary"
                  onClick={clearAll}
                  disabled={uploading}
                  type="button"
                >
                  Cancel
                </button>
              </div>

              {uploading && (
                <div className="upload-progress-container">
                  <div className="upload-progress-bar" style={{ width: `${progress}%` }} />
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Error alert */}
      {error && (
        <div className="upload-error animate-fade-in">
          <AlertCircle size={18} className="error-icon" />
          <span>{error}</span>
        </div>
      )}

      {/* Uploaded Success & Manual Analysis Staging Card */}
      {result && (
        <div className="uploaded-staging-card card animate-fade-in">
          <div className="staging-header">
            <div className="staging-status-badge">
              <CheckCircle2 size={20} className="success-check" />
              <span>Document Uploaded Successfully</span>
            </div>
            <StatusBadge status={result.status || 'uploaded'} />
          </div>

          <div className="staging-body">
            <div className="staging-meta-grid">
              <div className="staging-meta-item">
                <span className="staging-meta-label">File Name</span>
                <span className="staging-meta-value" title={result.filename}>
                  {result.filename}
                </span>
              </div>
              <div className="staging-meta-item">
                <span className="staging-meta-label">Document ID</span>
                <span className="staging-meta-value mono">{result.document_id}</span>
              </div>
              <div className="staging-meta-item">
                <span className="staging-meta-label">Format</span>
                <span className="staging-meta-value uppercase">{result.file_type || 'PDF'}</span>
              </div>
              <div className="staging-meta-item">
                <span className="staging-meta-label">File Size</span>
                <span className="staging-meta-value">{formatSize(result.file_size)}</span>
              </div>
            </div>

            <div className="staging-pipeline-preview">
              <div className="pipeline-preview-title">
                <Settings2 size={16} />
                <span>Ready for 6-Point Intelligence Audit:</span>
              </div>
              <div className="pipeline-preview-chips">
                <span className="chip">1. Tesseract OCR</span>
                <span className="chip">2. SGD Classifier</span>
                <span className="chip">3. Field Extraction</span>
                <span className="chip">4. Rule Validation</span>
                <span className="chip">5. Duplicate Match</span>
                <span className="chip">6. Isolation Forest & Groq AI</span>
              </div>
            </div>
          </div>

          <div className="staging-actions-bar">
            <button
              className="btn btn-primary start-analysis-btn"
              onClick={handleTriggerAnalysis}
              disabled={analyzing}
              type="button"
            >
              {analyzing ? (
                <>
                  <RefreshCw size={16} className="spin-animation" />
                  <span>Starting Analysis...</span>
                </>
              ) : (
                <>
                  <Play size={15} />
                  <span>Run Full Document Audit</span>
                  <ArrowRight size={15} />
                </>
              )}
            </button>

            <button
              className="btn btn-secondary"
              onClick={() => onUploadComplete?.(result, false)}
              type="button"
            >
              View Document Details
            </button>

            <button
              className="btn btn-ghost upload-another-btn"
              onClick={clearAll}
              type="button"
            >
              Upload Another
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
