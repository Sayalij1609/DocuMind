import './DataTable.css';
import LoadingSpinner from './LoadingSpinner';
import EmptyState from './EmptyState';

export default function DataTable({ columns, data, loading, emptyMessage, onRowClick }) {
  if (loading) {
    return (
      <div className="table-loading">
        <LoadingSpinner />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return <EmptyState message={emptyMessage || 'No data found'} />;
  }

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} style={col.width ? { width: col.width } : undefined}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr
              key={row.document_id || row.id || index}
              className={onRowClick ? 'clickable' : ''}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((col) => (
                <td key={col.key}>
                  {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
