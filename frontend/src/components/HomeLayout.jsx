import { useState, useEffect, useRef } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
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

      <main className="home-main-content">
        <Outlet />
      </main>
    </div>
  );
}
