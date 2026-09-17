import {
  MessageSquare,
  Sparkles,
  Bot,
  Layers,
  Search,
  BookOpen,
} from 'lucide-react';
import './QAPage.css';

export default function QAPage() {
  return (
    <div className="qa-page animate-fade-in">
      <div className="page-header">
        <h1>Document Q&A</h1>
        <p>Conversational document intelligence powered by Large Language Models</p>
      </div>

      <div className="qa-card">
        <div className="qa-phase-badge">
          <Sparkles size={14} />
          Phase 12 Preview
        </div>

        <div className="qa-icon-wrap">
          <Bot size={32} />
        </div>

        <h2 className="qa-title">Ask Anything About Your Documents</h2>
        <p className="qa-subtitle">
          Documind Q&A will allow you to query your entire corpus of invoices, receipts, and contracts in natural language with source grounding and exact citations.
        </p>

        <div className="mock-chat-box">
          <div className="mock-chat-bubble-user">
            What was the total invoiced amount for Acme Corp in Q3 2026?
          </div>
          <div className="mock-chat-bubble-bot">
            <strong style={{ color: 'var(--accent-primary)', display: 'block', marginBottom: '4px' }}>
              Documind AI Assistant
            </strong>
            Based on 3 invoices found for <strong>Acme Corp</strong>, the total amount is <strong>$14,250.00</strong>.
            <div style={{ marginTop: '8px', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              Sources: INV-2026-089 ($5,100), INV-2026-102 ($4,150), INV-2026-118 ($5,000)
            </div>
          </div>
        </div>
      </div>

      <div className="qa-features-grid">
        <div className="qa-feature-item">
          <Search size={20} style={{ color: 'var(--accent-primary)' }} />
          <h4>Semantic Search & Retrieval</h4>
          <p>
            Dense vector embeddings capture document concepts beyond exact keywords for high-precision retrieval.
          </p>
        </div>

        <div className="qa-feature-item">
          <BookOpen size={20} style={{ color: 'var(--accent-secondary)' }} />
          <h4>Source Grounding & Citations</h4>
          <p>
            Every answer links directly to verified extracted fields, bounding boxes, and document page references.
          </p>
        </div>

        <div className="qa-feature-item">
          <Layers size={20} style={{ color: 'var(--color-success)' }} />
          <h4>Multi-Document Aggregation</h4>
          <p>
            Synthesize calculations, cross-document reconciliations, and supplier summaries across your pipeline.
          </p>
        </div>
      </div>
    </div>
  );
}
