import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import DocumentsPage from './pages/DocumentsPage';
import DocumentDetailPage from './pages/DocumentDetailPage';
import AnomaliesPage from './pages/AnomaliesPage';
import DuplicatesPage from './pages/DuplicatesPage';
import SearchPage from './pages/SearchPage';
import QAPage from './pages/QAPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="documents/:id" element={<DocumentDetailPage />} />
          <Route path="anomalies" element={<AnomaliesPage />} />
          <Route path="duplicates" element={<DuplicatesPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="qa" element={<QAPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}