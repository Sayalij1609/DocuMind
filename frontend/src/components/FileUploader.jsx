import { useState, useRef } from 'react';
import { Upload, FileCheck, X, AlertCircle } from 'lucide-react';
import { uploadDocument } from '../services/api';
import './FileUploader.css';

const ACCEPTED_TYPES = ['.pdf', '.jpg', '.jpeg', '.png'];
const MAX_SIZE_MB = 50;

export default function FileUploader({ onUploadComplete }) {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const validateFile = (f) => {
    const ext = '.' + f.name.split('.').pop().toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext)) {
      return `Unsupported file type: ${ext}. Accepted: ${ACCEPTED_TYPES.join(', ')}`;
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File too large (${(f.size / 1024 / 1024).toFixed(1)}MB). Maximum: ${MAX_SIZE_MB}MB`;
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
      const res = await uploadDocument(file, (pct) => setProgress(pct));
      setResult(res);
      setFile(null);
      onUploadComplete?.(res);
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const clearFile = () => {
    setFile(null);
    setError(null);
    setResult(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div className="file-uploader">
      {/* Drop zone */}
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
            <Upload size={40} className="drop-icon" />
            <p className="drop-title">
              Drag & drop your document here
            </p>
            <p className="drop-subtitle">
              or click to browse files
            </p>
            <p className="drop-formats">
              Supported: PDF, JPG, JPEG, PNG (max {MAX_SIZE_MB}MB)
            </p>
          </div>
        ) : (
          <div className="file-preview">
            <FileCheck size={28} className="file-icon" />
            <div className="file-info">
              <p className="file-name">{file.name}</p>
              <p className="file-size">{formatSize(file.size)}</p>
            </div>
            <button className="btn-ghost file-remove" onClick={(e) => { e.stopPropagation(); clearFile(); }}>
              <X size={18} />
            </button>
          </div>
        )}
      </div>

      {/* Upload button & progress */}
      {file && !result && (
        <div className="upload-actions">
          <button
            className="btn btn-primary upload-btn"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? (
              <>
                <span className="upload-spinner" />
                Uploading {progress}%
              </>
            ) : (
              <>
                <Upload size={16} />
                Upload & Process
              </>
            )}
          </button>

          {uploading && (
            <div className="progress-bar-wrapper">
              <div className="progress-bar" style={{ width: `${progress}%` }} />
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="upload-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Success */}
      {result && (
        <div className="upload-success animate-fade-in">
          <FileCheck size={20} />
          <div>
            <p className="success-title">Upload successful!</p>
            <p className="success-detail">
              Document ID: <code>{result.document_id}</code>
            </p>
            <p className="success-detail">
              Status: <strong>{result.status}</strong> — Processing will begin automatically.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
