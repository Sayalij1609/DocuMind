import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft, Sparkles, Layers, ShieldCheck, Copy,
  AlertTriangle, FileCode, Upload, CheckCircle2,
  XCircle, Loader2, Files, FileUp
} from 'lucide-react';
import FileUploader from '../components/FileUploader';
import { uploadBatch, getBatchStatus } from '../services/api';
import './UploadPage.css';

export default function UploadPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('single'); // 'single' | 'batch'

  /* ── Batch State ── */
  const [batchFiles, setBatchFiles] = useState([]);
  const [batchUploading, setBatchUploading] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);
  const [batchResult, setBatchResult] = useState(null);
  const [batchStatus, setBatchStatus] = useState(null);
  const [batchError, setBatchError] = useState(null);
  const pollRef = useRef(null);

  /* ── Single upload handlers ── */
  const handleUploadComplete = (result, autoProcessed = false) => {
    if (autoProcessed) {
      setTimeout(() => navigate(`/documents/${result.document_id}`), 1200);
    } else {
      navigate(`/documents/${result.document_id}`);
    }
  };

  const handleStartAnalysis = (documentId) => {
    navigate(`/documents/${documentId}`);
  };

  /* ── Batch: file selection ── */
  const handleBatchDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    const droppedFiles = Array.from(e.dataTransfer?.files || []);
    if (droppedFiles.length > 0) {
      setBatchFiles((prev) => [...prev, ...droppedFiles].slice(0, 20));
    }
  }, []);

  const handleBatchFileSelect = (e) => {
    const selected = Array.from(e.target.files || []);
    setBatchFiles((prev) => [...prev, ...selected].slice(0, 20));
    e.target.value = '';
  };

  const removeBatchFile = (index) => {
    setBatchFiles((prev) => prev.filter((_, i) => i !== index));
  };

  /* ── Batch: upload + poll ── */
  const handleBatchUpload = async () => {
    if (batchFiles.length === 0) return;
    setBatchUploading(true);
    setBatchError(null);
    setBatchProgress(0);
    setBatchResult(null);
    setBatchStatus(null);

    try {
      const result = await uploadBatch(batchFiles, (pct) => setBatchProgress(pct));
      setBatchResult(result);
      setBatchProgress(100);

      // Start polling for processing status
      if (result.batch_id) {
        pollRef.current = setInterval(async () => {
          try {
            const status = await getBatchStatus(result.batch_id);
            setBatchStatus(status);
            if (
              status.status === 'completed' ||
              status.status === 'partial' ||
              status.status === 'failed'
            ) {
              clearInterval(pollRef.current);
              pollRef.current = null;
            }
          } catch {
            // ignore polling errors
          }
        }, 2000);
      }
    } catch (err) {
      setBatchError(err.message || 'Batch upload failed');
    } finally {
      setBatchUploading(false);
    }
  };

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const resetBatch = () => {
    setBatchFiles([]);
    setBatchResult(null);
    setBatchStatus(null);
    setBatchError(null);
    setBatchProgress(0);
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle2 size={16} className="batch-icon-success" />;
      case 'failed': return <XCircle size={16} className="batch-icon-error" />;
      case 'processing': return <Loader2 size={16} className="batch-icon-processing spin" />;
      default: return <Loader2 size={16} className="batch-icon-pending" />;
    }
  };

  const formatBytes = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="upload-page animate-fade-in">
      <div className="page-header">
        <div className="page-header-top-nav">
          <Link to="/dashboard" className="inline-back-nav" title="Back to Dashboard">
            <ArrowLeft size={14} />
            <span>Dashboard</span>
          </Link>
        </div>
        <h1>Upload Documents</h1>
        <p>Stage documents for OCR extraction, deterministic validation, anomaly detection, and AI semantic audit.</p>
      </div>

      {/* ── Mode Toggle ── */}
      <div className="upload-mode-toggle">
        <button
          className={`mode-btn ${mode === 'single' ? 'active' : ''}`}
          onClick={() => { setMode('single'); resetBatch(); }}
        >
          <FileUp size={16} />
          Single Upload
        </button>
        <button
          className={`mode-btn ${mode === 'batch' ? 'active' : ''}`}
          onClick={() => setMode('batch')}
        >
          <Files size={16} />
          Batch Upload
        </button>
      </div>

      {/* ── Single Upload Mode ── */}
      {mode === 'single' && (
        <div className="upload-container card">
          <FileUploader
            onUploadComplete={handleUploadComplete}
            onStartAnalysis={handleStartAnalysis}
          />
        </div>
      )}

      {/* ── Batch Upload Mode ── */}
      {mode === 'batch' && (
        <div className="batch-upload-section">
          {/* Drop Zone */}
          {!batchResult && (
            <div
              className="batch-dropzone card"
              onDrop={handleBatchDrop}
              onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
            >
              <div className="batch-dropzone-inner">
                <Upload size={36} className="batch-drop-icon" />
                <h3>Drop files here or click to browse</h3>
                <p>Support PDF, JPG, PNG, TIFF — up to 20 files per batch</p>
                <label className="batch-browse-btn">
                  <span>Browse Files</span>
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.jpg,.jpeg,.png,.tiff,.tif"
                    onChange={handleBatchFileSelect}
                    style={{ display: 'none' }}
                  />
                </label>
              </div>
            </div>
          )}

          {/* File List */}
          {batchFiles.length > 0 && !batchResult && (
            <div className="batch-file-list card">
              <div className="batch-file-list-header">
                <h4>{batchFiles.length} file{batchFiles.length !== 1 ? 's' : ''} selected</h4>
                <button className="batch-clear-btn" onClick={resetBatch}>Clear All</button>
              </div>
              <div className="batch-file-items">
                {batchFiles.map((file, idx) => (
                  <div key={idx} className="batch-file-item">
                    <div className="batch-file-info">
                      <FileUp size={14} />
                      <span className="batch-file-name">{file.name}</span>
                      <span className="batch-file-size">{formatBytes(file.size)}</span>
                    </div>
                    <button className="batch-file-remove" onClick={() => removeBatchFile(idx)}>×</button>
                  </div>
                ))}
              </div>
              <div className="batch-actions">
                {batchError && <p className="batch-error">{batchError}</p>}
                <button
                  className="batch-upload-btn"
                  onClick={handleBatchUpload}
                  disabled={batchUploading}
                >
                  {batchUploading ? (
                    <><Loader2 size={16} className="spin" /> Uploading {batchProgress}%</>
                  ) : (
                    <><Upload size={16} /> Upload & Process All</>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Batch Processing Status */}
          {batchResult && (
            <div className="batch-status-panel card">
              <div className="batch-status-header">
                <h3>Batch Processing</h3>
                <span className={`batch-status-badge ${batchStatus?.status || 'processing'}`}>
                  {batchStatus?.status || 'processing'}
                </span>
              </div>

              {/* Progress bar */}
              <div className="batch-progress-bar">
                <div
                  className="batch-progress-fill"
                  style={{ width: `${batchStatus?.progress_percent || 0}%` }}
                />
              </div>
              <div className="batch-progress-label">
                {batchStatus?.completed || 0} / {batchStatus?.total || batchResult.total} completed
                {(batchStatus?.failed || 0) > 0 && (
                  <span className="batch-failed-count"> • {batchStatus.failed} failed</span>
                )}
              </div>

              {/* Per-item status */}
              <div className="batch-items-status">
                {(batchStatus?.items || batchResult.document_ids.map((id) => ({
                  document_id: id,
                  filename: batchFiles.find((_, i) => batchResult.document_ids[i] === id)?.name || id,
                  status: 'pending',
                }))).map((item) => (
                  <div key={item.document_id} className={`batch-item-row ${item.status}`}>
                    {getStatusIcon(item.status)}
                    <span className="batch-item-name">{item.filename}</span>
                    <span className={`batch-item-status-text ${item.status}`}>{item.status}</span>
                    {item.status === 'completed' && (
                      <button
                        className="batch-item-view"
                        onClick={() => navigate(`/documents/${item.document_id}`)}
                      >
                        View
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {/* Actions after completion */}
              {(batchStatus?.status === 'completed' || batchStatus?.status === 'partial') && (
                <div className="batch-done-actions">
                  <button className="batch-new-btn" onClick={resetBatch}>
                    <Upload size={14} /> New Batch
                  </button>
                  <button className="batch-docs-btn" onClick={() => navigate('/documents')}>
                    View All Documents
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Pipeline Info ── */}
      <div className="upload-info">
        <div className="info-card card">
          <div className="pipeline-header">
            <h4>Documind Intelligent Processing Pipeline</h4>
            <span className="pipeline-badge">6 Automated Audits</span>
          </div>
          <p className="pipeline-intro">
            When you click <strong>Start Analysis</strong>, Documind processes the document through an enterprise-grade extraction and compliance pipeline:
          </p>

          <div className="pipeline-grid">
            <div className="pipeline-card">
              <div className="pipeline-step-header">
                <span className="step-num">1</span>
                <FileCode size={18} className="step-icon" />
              </div>
              <h5>OCR & Normalization</h5>
              <p>Tesseract OCR engine extracts raw text and normalizes whitespace and layout coordinates.</p>
            </div>

            <div className="pipeline-card">
              <div className="pipeline-step-header">
                <span className="step-num">2</span>
                <Layers size={18} className="step-icon" />
              </div>
              <h5>ML Classification</h5>
              <p>TF-IDF + SGD model predicts document type (Invoice, Receipt, Contract, Resume) with confidence scoring.</p>
            </div>

            <div className="pipeline-card">
              <div className="pipeline-step-header">
                <span className="step-num">3</span>
                <Sparkles size={18} className="step-icon" />
              </div>
              <h5>Field & Entity Extraction</h5>
              <p>Deterministic regex heuristics extract financial amounts, dates, vendor names, and invoice IDs.</p>
            </div>

            <div className="pipeline-card">
              <div className="pipeline-step-header">
                <span className="step-num">4</span>
                <ShieldCheck size={18} className="step-icon" />
              </div>
              <h5>Deterministic Validation</h5>
              <p>6 enterprise business rules verify arithmetic totals, date sequences, and mandatory fields.</p>
            </div>

            <div className="pipeline-card">
              <div className="pipeline-step-header">
                <span className="step-num">5</span>
                <Copy size={18} className="step-icon" />
              </div>
              <h5>Duplicate Detection</h5>
              <p>Cosine similarity & SHA-256 hash matching against repository documents to flag exact or near duplicates.</p>
            </div>

            <div className="pipeline-card">
              <div className="pipeline-step-header">
                <span className="step-num">6</span>
                <AlertTriangle size={18} className="step-icon" />
              </div>
              <h5>Anomaly Detection</h5>
              <p>Isolation Forest flags statistical outliers and unusual patterns for review.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
