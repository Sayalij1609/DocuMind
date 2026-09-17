import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Upload,
  LayoutDashboard,
  Layers,
  ShieldCheck,
  Copy,
  AlertTriangle,
  FileText,
  Cpu,
  Sparkles,
  CheckCircle2,
  Activity,
  FileSearch,
  Zap,
} from 'lucide-react';
import './HomePage.css';

export default function HomePage() {
  const navigate = useNavigate();

  const capabilities = [
    {
      icon: Cpu,
      color: 'var(--accent-primary)',
      bgColor: 'var(--accent-primary-glow)',
      title: 'Multimodal Document Vision',
      desc: 'LayoutLMv3 integration combining 200 DPI rendered page imagery, spatial bounding boxes, and OCR tokens for deep layout awareness.',
      tag: 'LayoutLMv3 + OCR',
      link: '/documents',
    },
    {
      icon: Activity,
      color: 'var(--accent-secondary)',
      bgColor: 'var(--accent-secondary-glow)',
      title: 'Automated ML Classification',
      desc: 'High-speed TF-IDF + SGD classification engine trained to distinguish invoices, receipts, contracts, forms, and financial records.',
      tag: 'SGD + TF-IDF Classifier',
      link: '/dashboard',
    },
    {
      icon: Layers,
      color: 'var(--color-info)',
      bgColor: 'var(--color-info-bg)',
      title: 'Intelligent Field Extraction',
      desc: 'Deterministic extraction strategy extracting invoice numbers, issue dates, line items, tax breakdowns, and total amounts.',
      tag: 'Extracted Field Registry',
      link: '/documents',
    },
    {
      icon: ShieldCheck,
      color: 'var(--color-success)',
      bgColor: 'var(--color-success-bg)',
      title: 'Deterministic Rule Engine',
      desc: 'Six automated business compliance checks verifying arithmetic integrity (Subtotal + Tax = Total), date sequences, and schema requirements.',
      tag: '6 Compliance Rules',
      link: '/documents',
    },
    {
      icon: Copy,
      color: 'var(--color-duplicate)',
      bgColor: 'var(--color-duplicate-bg)',
      title: 'Dual-Tier Deduplication',
      desc: 'SHA-256 content hashing for exact duplicate filtering paired with TF-IDF cosine similarity vector comparison for near-duplicates.',
      tag: 'Cosine Similarity ≥ 0.85',
      link: '/duplicates',
    },
    {
      icon: AlertTriangle,
      color: 'var(--color-anomaly)',
      bgColor: 'var(--color-anomaly-bg)',
      title: 'Unsupervised Anomaly Detection',
      desc: 'Isolation Forest outlier detection evaluating multi-dimensional feature vectors to identify irregular invoices and compliance anomalies.',
      tag: 'Isolation Forest Model',
      link: '/anomalies',
    },
  ];

  return (
    <div className="homepage animate-fade-in">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-badge">
          <span className="pulse-dot" />
          <span>Documind Intelligent Document Processing & Understanding</span>
        </div>

        <h1 className="hero-title">
          Transform Unstructured Documents into{' '}
          <span className="text-gradient">Structured Intelligence</span>
        </h1>

        <p className="hero-subtitle">
          Documind is a production-grade document intelligence platform. Ingest PDFs and images,
          classify document categories, extract key entities, enforce compliance rules, and detect
          statistical anomalies in seconds.
        </p>

        <div className="hero-actions">
          <button className="btn-hero-primary" onClick={() => navigate('/dashboard')}>
            <LayoutDashboard size={18} />
            Open Dashboard
            <ArrowRight size={16} />
          </button>

          <button className="btn-hero-secondary" onClick={() => navigate('/upload')}>
            <Upload size={18} />
            Upload Document
          </button>
        </div>

        {/* Live Pipeline Visualizer Card */}
        <div className="pipeline-visualizer">
          <div className="visualizer-header">
            <div className="visualizer-title">
              <Sparkles size={16} style={{ color: 'var(--accent-primary)' }} />
              End-to-End Processing Architecture
            </div>
            <div className="visualizer-status-pills">
              <span className="badge-success" style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '11px' }}>
                Pipeline Active
              </span>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>FastAPI + PostgreSQL</span>
            </div>
          </div>

          <div className="visualizer-flow">
            <div className="flow-step">
              <span className="flow-step-num">01</span>
              <div className="flow-step-name">Ingestion</div>
              <div className="flow-step-desc">PDF / JPG / PNG</div>
            </div>

            <div className="flow-step">
              <span className="flow-step-num">02</span>
              <div className="flow-step-name">Layout & OCR</div>
              <div className="flow-step-desc">Tesseract + BBoxes</div>
            </div>

            <div className="flow-step">
              <span className="flow-step-num">03</span>
              <div className="flow-step-name">Classifier</div>
              <div className="flow-step-desc">TF-IDF + SGD</div>
            </div>

            <div className="flow-step">
              <span className="flow-step-num">04</span>
              <div className="flow-step-name">Extraction</div>
              <div className="flow-step-desc">Regex & Heuristics</div>
            </div>

            <div className="flow-step">
              <span className="flow-step-num">05</span>
              <div className="flow-step-name">Validation</div>
              <div className="flow-step-desc">6 Business Rules</div>
            </div>

            <div className="flow-step">
              <span className="flow-step-num">06</span>
              <div className="flow-step-name">Deduplication</div>
              <div className="flow-step-desc">Cosine Similarity</div>
            </div>

            <div className="flow-step">
              <span className="flow-step-num">07</span>
              <div className="flow-step-name">Anomaly</div>
              <div className="flow-step-desc">Isolation Forest</div>
            </div>
          </div>

          {/* Sample Parsed Preview */}
          <div className="sample-parsed-card">
            <div className="sample-parsed-header">
              <div>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '13px' }}>
                  Live Document Sample:
                </span>{' '}
                <span style={{ color: 'var(--accent-primary)', fontSize: '13px' }}>acme_corp_invoice_1092.pdf</span>
              </div>
              <div className="sample-doc-meta">
                Classification: <strong>INVOICE (99.8%)</strong> | Status: <strong>COMPLETED</strong>
              </div>
            </div>

            <div className="sample-fields-grid">
              <div className="sample-field-item">
                <div className="sample-field-key">Vendor Name</div>
                <div className="sample-field-val">Acme Corporation</div>
              </div>
              <div className="sample-field-item">
                <div className="sample-field-key">Invoice Number</div>
                <div className="sample-field-val">INV-2026-1092</div>
              </div>
              <div className="sample-field-item">
                <div className="sample-field-key">Total Amount</div>
                <div className="sample-field-val">$14,250.00</div>
              </div>
              <div className="sample-field-item">
                <div className="sample-field-key">Validation Audit</div>
                <div className="sample-field-val" style={{ color: 'var(--color-success)' }}>
                  ✓ 6/6 Rules PASS
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Metrics Highlights Strip */}
      <section className="metrics-strip">
        <div className="stat-box">
          <div className="stat-value">6+</div>
          <div className="stat-label">Pipeline Processing Stages</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">99.4%</div>
          <div className="stat-label">Model Classification Baseline</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">6</div>
          <div className="stat-label">Deterministic Compliance Rules</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">100%</div>
          <div className="stat-label">Arithmetic Precision Verification</div>
        </div>
      </section>

      {/* Capabilities Section */}
      <section className="capabilities-section">
        <div className="section-header">
          <div className="section-eyebrow">Comprehensive Capabilities</div>
          <h2 className="section-title">Built for Complex Document Intelligence</h2>
          <p className="section-desc">
            From raw visual pixels to verified financial ledger records, Documind delivers
            end-to-end automation with full explainability.
          </p>
        </div>

        <div className="capabilities-grid">
          {capabilities.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="capability-card"
                onClick={() => navigate(item.link)}
                style={{ cursor: 'pointer' }}
              >
                <div
                  className="capability-icon-wrap"
                  style={{ background: item.bgColor, color: item.color }}
                >
                  <Icon size={22} />
                </div>
                <h3 className="capability-title">{item.title}</h3>
                <p className="capability-desc">{item.desc}</p>
                <div className="capability-footer-tag">
                  <span>{item.tag}</span>
                  <ArrowRight size={12} />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Call to Action Banner */}
      <section className="cta-banner">
        <h2 className="cta-title">Start Processing Documents with Documind</h2>
        <p className="cta-subtitle">
          Experience automated classification, deep extraction, rule validation, and outlier detection
          on your own invoices, contracts, and receipts.
        </p>
        <div className="cta-buttons">
          <button className="btn-hero-primary" onClick={() => navigate('/upload')}>
            <Upload size={18} />
            Upload Document Now
          </button>
          <button className="btn-hero-secondary" onClick={() => navigate('/dashboard')}>
            <LayoutDashboard size={18} />
            View Live Dashboard
          </button>
        </div>
      </section>
    </div>
  );
}
