import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Home, Sparkles, Layers, ShieldCheck, Copy, AlertTriangle, FileCode } from 'lucide-react';
import FileUploader from '../components/FileUploader';
import './UploadPage.css';

export default function UploadPage() {
  const navigate = useNavigate();

  const handleUploadComplete = (result, autoProcessed = false) => {
    if (autoProcessed) {
      setTimeout(() => {
        navigate(`/documents/${result.document_id}`);
      }, 1200);
    } else {
      // Manual mode: user stays on page or clicks "View Details"
      navigate(`/documents/${result.document_id}`);
    }
  };

  const handleStartAnalysis = (documentId) => {
    navigate(`/documents/${documentId}`);
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
        <h1>Upload Document</h1>
        <p>Stage documents for OCR extraction, deterministic validation, anomaly detection, and AI semantic audit.</p>
      </div>

      <div className="upload-container card">
        <FileUploader
          onUploadComplete={handleUploadComplete}
          onStartAnalysis={handleStartAnalysis}
        />
      </div>

      <div className="upload-info">
        <div className="info-card card">
          <div className="pipeline-header">
            <h4>Nexora Intelligent Processing Pipeline</h4>
            <span className="pipeline-badge">6 Automated Audits</span>
          </div>
          <p className="pipeline-intro">
            When you click <strong>Start Analysis</strong>, Nexora processes the document through an enterprise-grade extraction and compliance pipeline:
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
              <h5>Anomaly & AI Copilot</h5>
              <p>Isolation Forest flags statistical outliers; Groq Llama-3.3-70B synthesizes executive summaries and insights.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
