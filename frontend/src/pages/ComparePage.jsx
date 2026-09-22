import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft, GitCompare, CheckCircle2, XCircle,
  MinusCircle, Loader2, FileText
} from 'lucide-react';
import { getDocuments, compareDocuments } from '../services/api';
import './ComparePage.css';

export default function ComparePage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [docA, setDocA] = useState('');
  const [docB, setDocB] = useState('');
  const [comparing, setComparing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await getDocuments(1, 200);
        const completed = (data.documents || []).filter(
          (d) => d.status === 'completed'
        );
        setDocuments(completed);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleCompare = async () => {
    if (!docA || !docB || docA === docB) return;
    setComparing(true);
    setError(null);
    setResult(null);
    try {
      const data = await compareDocuments(docA, docB);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Comparison failed');
    } finally {
      setComparing(false);
    }
  };

  const getSimilarityColor = (score) => {
    if (score >= 0.8) return 'high';
    if (score >= 0.5) return 'medium';
    return 'low';
  };

  return (
    <div className="compare-page animate-fade-in">
      <div className="page-header">
        <div className="page-header-top-nav">
          <Link to="/dashboard" className="inline-back-nav" title="Back to Dashboard">
            <ArrowLeft size={14} />
            <span>Dashboard</span>
          </Link>
        </div>
        <h1>
          <GitCompare size={24} />
          Document Comparison
        </h1>
        <p>Select two processed documents to compare their extracted fields, similarity, and validation status.</p>
      </div>

      {/* ── Document Selector ── */}
      <div className="compare-selector card">
        <div className="selector-row">
          <div className="selector-col">
            <label>Document A</label>
            <select
              value={docA}
              onChange={(e) => setDocA(e.target.value)}
              disabled={loading}
            >
              <option value="">Select document…</option>
              {documents.map((d) => (
                <option key={d.document_id} value={d.document_id}>
                  {d.filename} ({d.document_type || 'unknown'})
                </option>
              ))}
            </select>
          </div>

          <div className="selector-vs">
            <GitCompare size={20} />
            <span>VS</span>
          </div>

          <div className="selector-col">
            <label>Document B</label>
            <select
              value={docB}
              onChange={(e) => setDocB(e.target.value)}
              disabled={loading}
            >
              <option value="">Select document…</option>
              {documents.filter((d) => d.document_id !== docA).map((d) => (
                <option key={d.document_id} value={d.document_id}>
                  {d.filename} ({d.document_type || 'unknown'})
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          className="compare-btn"
          onClick={handleCompare}
          disabled={!docA || !docB || docA === docB || comparing}
        >
          {comparing ? (
            <><Loader2 size={16} className="spin" /> Comparing…</>
          ) : (
            <><GitCompare size={16} /> Compare Documents</>
          )}
        </button>

        {error && <p className="compare-error">{error}</p>}
      </div>

      {/* ── Results ── */}
      {result && (
        <div className="compare-results animate-fade-in">
          {/* Summary Bar */}
          <div className="compare-summary card">
            <div className="summary-grid">
              <div className="summary-item">
                <span className="summary-label">Similarity</span>
                <span className={`summary-value sim-${getSimilarityColor(result.similarity_score)}`}>
                  {(result.similarity_score * 100).toFixed(1)}%
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Type Match</span>
                <span className={`summary-value ${result.type_match ? 'match' : 'mismatch'}`}>
                  {result.type_match ? (
                    <><CheckCircle2 size={14} /> Match</>
                  ) : (
                    <><XCircle size={14} /> Different</>
                  )}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Doc A Type</span>
                <span className="summary-value type">{result.type_a || 'Unknown'}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Doc B Type</span>
                <span className="summary-value type">{result.type_b || 'Unknown'}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Validation A</span>
                <span className="summary-value">{result.validation_a || 'N/A'}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Validation B</span>
                <span className="summary-value">{result.validation_b || 'N/A'}</span>
              </div>
            </div>
            {result.summary && (
              <p className="compare-summary-text">{result.summary}</p>
            )}
          </div>

          {/* Field Diffs Table */}
          <div className="compare-fields card">
            <h3>
              <FileText size={18} />
              Field-by-Field Comparison
            </h3>
            <div className="fields-table-wrap">
              <table className="fields-table">
                <thead>
                  <tr>
                    <th>Field</th>
                    <th>
                      <span className="th-doc">A</span>
                      {result.filename_a}
                    </th>
                    <th>
                      <span className="th-doc">B</span>
                      {result.filename_b}
                    </th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {result.field_diffs.map((diff, idx) => (
                    <tr key={idx} className={diff.match ? 'row-match' : 'row-diff'}>
                      <td className="field-name">{diff.field_name}</td>
                      <td className="field-val">{diff.value_a || '—'}</td>
                      <td className="field-val">{diff.value_b || '—'}</td>
                      <td className="field-status">
                        {diff.match ? (
                          <span className="status-match">
                            <CheckCircle2 size={14} /> Match
                          </span>
                        ) : (
                          <span className="status-diff">
                            <MinusCircle size={14} /> {diff.notes || 'Differs'}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                  {result.field_diffs.length === 0 && (
                    <tr>
                      <td colSpan={4} className="no-fields">
                        No extracted fields to compare.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
