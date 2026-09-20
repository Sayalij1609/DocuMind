import { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Bot,
  Send,
  FileText,
  Key,
  X,
  RefreshCw,
} from 'lucide-react';
import {
  getDocuments,
  askDocumentQuestion,
  getAIStatus,
  updateAIConfig,
} from '../services/api';
import './QAPage.css';

export default function QAPage() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
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
    if (!input.trim() || !selectedDocId || loading) return;

    const question = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: question }]);
    setLoading(true);

    try {
      const result = await askDocumentQuestion(selectedDocId, question);
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: result.answer,
        citations: result.citations || [],
        method: result.method,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: 'Failed to get a response. Please check your AI configuration and try again.',
        error: true,
      }]);
    } finally {
      setLoading(false);
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
        <label className="qa-doc-label">
          <FileText size={16} />
          Select Document
        </label>
        <select
          className="qa-doc-select"
          value={selectedDocId}
          onChange={e => {
            setSelectedDocId(e.target.value);
            setMessages([]);
          }}
        >
          <option value="">— Choose a document —</option>
          {documents
            .filter(d => d.status === 'completed')
            .map(doc => (
            <option key={doc.document_id} value={doc.document_id}>
              {doc.filename} ({doc.document_type || 'unclassified'})
            </option>
          ))}
        </select>
        {selectedDoc && (
          <div className="qa-doc-info">
            <span className="meta-pill">{selectedDoc.file_type}</span>
            <span className="meta-pill" style={{ textTransform: 'capitalize' }}>{selectedDoc.document_type || 'Unknown'}</span>
            <span className="meta-pill">{(selectedDoc.file_size / 1024).toFixed(1)} KB</span>
          </div>
        )}
      </div>

      {/* Chat Area */}
      <div className="qa-chat-card card">
        <div className="qa-chat-messages">
          {messages.length === 0 && (
            <div className="qa-chat-welcome">
              <Bot size={36} className="qa-welcome-icon" />
              <h3>DocuMind AI Assistant</h3>
              <p>Select a document above and ask any question about it.</p>

              {selectedDocId && (
                <div className="qa-chat-suggestions">
                  {[
                    'What is the total amount?',
                    'Who issued this document?',
                    'What are the key dates?',
                    'Summarize this document',
                    'List all line items',
                    'What is the tax breakdown?',
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
              )}
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
                {msg.text}
                {msg.citations && msg.citations.length > 0 && (
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
            placeholder={selectedDocId ? 'Ask a question about this document...' : 'Select a document first...'}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            disabled={!selectedDocId || loading}
          />
          <button
            className="btn btn-accent qa-send-btn"
            onClick={handleSend}
            disabled={!selectedDocId || !input.trim() || loading}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
