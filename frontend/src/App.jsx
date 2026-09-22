import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import HomeLayout from './components/HomeLayout';
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import DocumentsPage from './pages/DocumentsPage';
import DocumentDetailPage from './pages/DocumentDetailPage';
import AnomaliesPage from './pages/AnomaliesPage';
import DuplicatesPage from './pages/DuplicatesPage';
import SearchPage from './pages/SearchPage';
import QAPage from './pages/QAPage';
import ComparePage from './pages/ComparePage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Home uses navbar-only layout */}
        <Route element={<HomeLayout />}>
          <Route path="/" element={<HomePage />} />
        </Route>

        {/* All other pages use sidebar layout */}
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/documents/:id" element={<DocumentDetailPage />} />
          <Route path="/anomalies" element={<AnomaliesPage />} />
          <Route path="/duplicates" element={<DuplicatesPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/qa" element={<QAPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}