import { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Bot,
  Send,
  FileText,
  Key,
  X,
  RefreshCw,
  Layers,
  Database,
  Search,
} from 'lucide-react';
import {
  getDocuments,
  askDocumentQuestion,
  askMultiDocumentQuestion,
  reindexDocumentRAG,
  getAIStatus,
  updateAIConfig,
} from '../services/api';
import './QAPage.css';

export default function QAPage() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('__all__');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [aiStatus, setAiStatus] = useState(null);
  const [showKeyDialog, setShowKeyDialog] = useState(false);
  const [keyInput, setKeyInput] = useState('');
  const endRef = useRef(null);

  useEffect(() => {
    async function init() {
      try {
        const [docsRes, statusRes] = await Promise.allSettled([
          getDocuments(1, 100),
          getAIStatus(),
        ]);
        if (docsRes.status === 'fulfilled') {
          setDocuments(docsRes.value.documents || []);
        }
        if (statusRes.status === 'fulfilled') {
          setAiStatus(statusRes.value);
        }
      } catch {
        // ignore
      }
    }
    init();
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: question }]);
    setLoading(true);

    try {
      let result;
      if (!selectedDocId || selectedDocId === '__all__') {
        result = await askMultiDocumentQuestion(question);
      } else {
        result = await askDocumentQuestion(selectedDocId, question);
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        text: result.answer,
        sources: result.sources || [],
        citations: result.citations || [],
        method: result.method,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: 'Failed to retrieve an answer. Please verify document status and try again.',
        error: true,
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleReindex = async () => {
    if (!selectedDocId || selectedDocId === '__all__' || reindexing) return;
    setReindexing(true);
    try {
      const res = await reindexDocumentRAG(selectedDocId);
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: `Vector index updated: successfully re-indexed ${res.indexed_chunks} page chunks for ${res.filename}.`,
        sources: [],
        citations: [],
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: 'Failed to re-index document.',
        error: true,
      }]);
    } finally {
      setReindexing(false);
    }
  };

  const handleSaveKey = async () => {
    if (!keyInput.trim()) return;
    try {
      const status = await updateAIConfig(keyInput.trim());
      setAiStatus(status);
      setShowKeyDialog(false);
      setKeyInput('');
    } catch {
      // ignore
    }
  };

  const selectedDoc = documents.find(d => d.document_id === selectedDocId);

  return (
    <div className="qa-page animate-fade-in">
      <div className="page-header">
        <div>
          <h1>Document Q&A</h1>
          <p>Ask questions about your documents using AI-powered analysis</p>
        </div>
        <button
          className="btn btn-accent-outline"
          onClick={() => setShowKeyDialog(true)}
        >
          <Key size={15} />
          {aiStatus?.configured ? 'AI Active' : 'Configure AI'}
        </button>
      </div>

      {/* API Key Dialog */}
      {showKeyDialog && (
        <div className="dialog-overlay animate-fade-in" onClick={() => setShowKeyDialog(false)}>
          <div className="dialog-box" onClick={e => e.stopPropagation()}>
            <div className="dialog-header">
              <h3><Key size={18} /> Configure Groq API Key</h3>
              <button className="dialog-close" onClick={() => setShowKeyDialog(false)}>
                <X size={18} />
              </button>
            </div>
            <p className="dialog-desc">
              Enter your Groq API key to enable AI-powered Q&A. Get your key at{' '}
              <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer">console.groq.com</a>.
            </p>
            <div className="dialog-input-row">
              <input
                type="password"
                className="dialog-input"
                placeholder="gsk_..."
                value={keyInput}
                onChange={e => setKeyInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSaveKey()}
              />
              <button className="btn btn-accent" onClick={handleSaveKey}>Save</button>
            </div>
            {aiStatus && (
              <div className={`dialog-status ${aiStatus.configured ? 'active' : ''}`}>
                <span className={`status-dot ${aiStatus.configured ? 'dot-active' : 'dot-inactive'}`} />
                {aiStatus.configured
                  ? `AI Active — ${aiStatus.model} (${aiStatus.source})`
                  : 'AI not configured'}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Document Selector */}
      <div className="qa-doc-selector card">
        <div className="qa-doc-selector-top">
          <label className="qa-doc-label">
            <Database size={16} />
            Target Knowledge Base
          </label>
          {selectedDoc && (
            <button
              className="btn btn-secondary btn-sm qa-reindex-btn"
              onClick={handleReindex}
              disabled={reindexing}
              title="Re-chunk and update vector embeddings for this document"
            >
              <RefreshCw size={13} className={reindexing ? 'spin' : ''} />
              {reindexing ? 'Indexing Chunks...' : 'Re-index for RAG'}
            </button>
          )}
        </div>

        <select
          className="qa-doc-select"
          value={selectedDocId}
          onChange={e => {
            setSelectedDocId(e.target.value);
            setMessages([]);
          }}
        >
          <option value="__all__">🌐 All Documents (Repository-Wide Search)</option>
          <optgroup label="Single Documents">
            {documents
              .filter(d => d.status === 'completed')
              .map(doc => (
                <option key={doc.document_id} value={doc.document_id}>
                  📄 {doc.filename} ({doc.document_type || 'unclassified'})
                </option>
              ))}
          </optgroup>
        </select>

        {selectedDoc ? (
          <div className="qa-doc-info">
            <span className="meta-pill">{selectedDoc.file_type}</span>
            <span className="meta-pill" style={{ textTransform: 'capitalize' }}>
              {selectedDoc.document_type || 'Unknown'}
            </span>
            <span className="meta-pill">{(selectedDoc.file_size / 1024).toFixed(1)} KB</span>
          </div>
        ) : (
          <div className="qa-doc-info">
            <span className="meta-pill meta-repo">
              <Search size={12} />
              Cross-Document Retrieval Active ({documents.filter(d => d.status === 'completed').length} completed documents)
            </span>
          </div>
        )}
      </div>

      {/* Chat Area */}
      <div className="qa-chat-card card">
        <div className="qa-chat-messages">
          {messages.length === 0 && (
            <div className="qa-chat-welcome">
              <Bot size={36} className="qa-welcome-icon" />
              <h3>Nexora RAG Assistant</h3>
              <p>
                {selectedDocId === '__all__'
                  ? 'Ask questions across your entire document repository with grounded citations.'
                  : `Ask grounded questions about ${selectedDoc?.filename || 'this document'}.`}
              </p>

              <div className="qa-chat-suggestions">
                {[
                  'What is the invoice total?',
                  'Who issued this document?',
                  'What are the key dates?',
                  'Summarize this document',
                  'List all line items',
                  'What is the tax amount?',
                ].map((q, i) => (
                  <button
                    key={i}
                    className="qa-suggestion-btn"
                    onClick={() => setInput(q)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`qa-msg ${msg.role}`}>
              {msg.role === 'assistant' && (
                <div className="qa-msg-avatar">
                  <Bot size={16} />
                </div>
              )}
              <div className={`qa-msg-bubble ${msg.error ? 'error-bubble' : ''}`}>
                <div className="qa-msg-text">{msg.text}</div>

                {/* Structured RAG Evidence Sources */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="qa-sources-container">
                    <div className="qa-sources-title">
                      <Layers size={13} />
                      <span>Retrieved Evidence ({msg.sources.length} {msg.sources.length === 1 ? 'source' : 'sources'})</span>
                    </div>
                    <div className="qa-sources-list">
                      {msg.sources.map((src, sIdx) => (
                        <div key={sIdx} className="qa-source-card">
                          <div className="qa-source-header">
                            <span className="qa-source-badge">
                              <FileText size={12} />
                              {src.filename} — Page {src.page_number}
                            </span>
                            {src.similarity_score > 0 && (
                              <span className="qa-source-score">
                                {(src.similarity_score * 100).toFixed(0)}% match
                              </span>
                            )}
                          </div>
                          {src.snippet && (
                            <p className="qa-source-snippet">"{src.snippet}"</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Citations Pills fallback */}
                {(!msg.sources || msg.sources.length === 0) && msg.citations && msg.citations.length > 0 && (
                  <div className="qa-citations">
                    {msg.citations.map((c, ci) => (
                      <span key={ci} className="qa-citation-tag">{c}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="qa-msg assistant">
              <div className="qa-msg-avatar">
                <Bot size={16} />
              </div>
              <div className="qa-msg-bubble typing">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}

          <div ref={endRef} />
        </div>

        <div className="qa-input-bar">
          <input
            type="text"
            className="qa-input"
            placeholder={
              selectedDocId === '__all__'
                ? 'Ask a question across all uploaded documents...'
                : `Ask a question about ${selectedDoc?.filename || 'this document'}...`
            }
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            disabled={loading}
          />
          <button
            className="btn btn-accent qa-send-btn"
            onClick={handleSend}
            disabled={!input.trim() || loading}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
