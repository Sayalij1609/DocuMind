import { useNavigate } from 'react-router-dom';
import FileUploader from '../components/FileUploader';
import './UploadPage.css';

export default function UploadPage() {
  const navigate = useNavigate();

  const handleUploadComplete = (result) => {
    // After short delay, navigate to document detail
    setTimeout(() => {
      navigate(`/documents/${result.document_id}`);
    }, 2500);
  };

  return (
    <div className="upload-page animate-fade-in">
      <div className="page-header">
        <h1>Upload Document</h1>
        <p>Upload documents for AI-powered classification, extraction, and analysis</p>
      </div>

      <div className="upload-container card">
        <FileUploader onUploadComplete={handleUploadComplete} />
      </div>

      <div className="upload-info">
        <div className="info-card card">
          <h4>Processing Pipeline</h4>
          <ol className="pipeline-steps">
            <li>
              <span className="step-num">1</span>
              <span>OCR text extraction (Tesseract)</span>
            </li>
            <li>
              <span className="step-num">2</span>
              <span>Document classification (TF-IDF + SGD)</span>
            </li>
            <li>
              <span className="step-num">3</span>
              <span>Field extraction (regex heuristics)</span>
            </li>
            <li>
              <span className="step-num">4</span>
              <span>Deterministic validation (6 business rules)</span>
            </li>
            <li>
              <span className="step-num">5</span>
              <span>Duplicate detection (TF-IDF cosine similarity)</span>
            </li>
            <li>
              <span className="step-num">6</span>
              <span>Anomaly detection (Isolation Forest)</span>
            </li>
          </ol>
        </div>
      </div>
    </div>
  );
}
