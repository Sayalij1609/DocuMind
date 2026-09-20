import { useState, useEffect, useRef } from 'react';
import { NavLink, Outlet, useLocation, Link } from 'react-router-dom';
import {
  Home,
  LayoutDashboard,
  Upload,
  FileText,
  AlertTriangle,
  Copy,
  Search,
  MessageCircleQuestion,
  FileCheck2,
  Menu,
  X,
  ArrowRight,
} from 'lucide-react';
import './HomeLayout.css';

const navItems = [
  { to: '/', icon: Home, label: 'Home' },
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/upload', icon: Upload, label: 'Upload' },
  { to: '/documents', icon: FileText, label: 'Documents' },
  { to: '/anomalies', icon: AlertTriangle, label: 'Anomalies' },
  { to: '/duplicates', icon: Copy, label: 'Duplicates' },
  { to: '/search', icon: Search, label: 'Search' },
  { to: '/qa', icon: MessageCircleQuestion, label: 'Q&A' },
];

export default function HomeLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navRef = useRef(null);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    function handleClick(e) {
      if (mobileOpen && navRef.current && !navRef.current.contains(e.target)) {
        setMobileOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [mobileOpen]);

  return (
    <div className="home-layout">
      {/* Top Navbar */}
      <header className="home-navbar" ref={navRef}>
        <div className="home-navbar-inner">
          {/* Logo */}
          <NavLink to="/" className="home-navbar-brand">
            <span className="home-navbar-logo-mark">
              <FileCheck2 size={20} />
            </span>
            <span className="home-navbar-logo-text">Documind</span>
          </NavLink>

          {/* Desktop nav links */}
          <nav className="home-navbar-links">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `home-navbar-link ${isActive ? 'active' : ''}`
                }
              >
                <Icon size={16} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          {/* Mobile hamburger */}
          <button
            className="home-navbar-toggle"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle navigation"
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

        {/* Mobile dropdown */}
        {mobileOpen && (
          <nav className="home-navbar-mobile">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `home-navbar-mobile-link ${isActive ? 'active' : ''}`
                }
              >
                <Icon size={18} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>
        )}
      </header>

      {/* Main Content */}
      <main className="home-main-content">
        <Outlet />
      </main>

      {/* Modern High-Resolution Footer */}
      <footer className="home-footer">
        <div className="home-footer-inner">
          <div className="home-footer-grid">
            {/* Brand Column */}
            <div className="footer-col footer-col-brand">
              <Link to="/" className="footer-brand">
                <span className="footer-logo-mark">
                  <FileCheck2 size={20} />
                </span>
                <span className="footer-logo-text">Documind</span>
              </Link>
              <p className="footer-desc">
                Intelligent Document Processing & Understanding Pipeline. Empowering teams with automated classification, structured extraction, anomaly detection, and deep semantic search.
              </p>
              <div className="footer-status-pill">
                <span className="footer-status-dot"></span>
                <span>System Operational · ML Pipeline Active</span>
              </div>
            </div>

            {/* Navigation Column */}
            <div className="footer-col">
              <h4 className="footer-col-title">Platform</h4>
              <ul className="footer-links">
                <li><Link to="/dashboard">Live Dashboard</Link></li>
                <li><Link to="/upload">Upload Document</Link></li>
                <li><Link to="/documents">Document Repository</Link></li>
                <li><Link to="/search">Deep Search</Link></li>
              </ul>
            </div>

            {/* Intelligence Column */}
            <div className="footer-col">
              <h4 className="footer-col-title">Intelligence</h4>
              <ul className="footer-links">
                <li><Link to="/anomalies">Anomaly Detection</Link></li>
                <li><Link to="/duplicates">Duplicate Clusters</Link></li>
                <li><Link to="/qa">Document Q&A</Link></li>
                <li><Link to="/dashboard">Validation Rules</Link></li>
              </ul>
            </div>

            {/* Architecture Column */}
            <div className="footer-col">
              <h4 className="footer-col-title">Engine Stack</h4>
              <ul className="footer-tech-list">
                <li><span className="tech-tag">FastAPI</span> High-speed Python API</li>
                <li><span className="tech-tag">React 19</span> Modern Vite frontend</li>
                <li><span className="tech-tag">PyMuPDF</span> Native PDF parsing</li>
                <li><span className="tech-tag">Tesseract</span> Optical Character Rec.</li>
                <li><span className="tech-tag">Sentence-BERT</span> Vector Embeddings</li>
              </ul>
            </div>
          </div>

          <div className="home-footer-bottom">
            <p className="footer-copy">
              © {new Date().getFullYear()} Documind. All rights reserved. Enterprise-grade document automation.
            </p>
            <div className="footer-actions">
              <Link to="/upload" className="footer-cta-btn">
                <span>Start Ingesting</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
