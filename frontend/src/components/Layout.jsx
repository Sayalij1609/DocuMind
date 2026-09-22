import { useState } from 'react';
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
  ChevronLeft,
  ChevronRight,
  FileCheck2,
  ArrowLeft,
  GitCompare,
} from 'lucide-react';
import './Layout.css';

const navGroups = [
  {
    label: 'Overview',
    items: [
      { to: '/', icon: Home, label: 'Home' },
      { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    ],
  },
  {
    label: 'Workspace',
    items: [
      { to: '/upload', icon: Upload, label: 'Upload' },
      { to: '/documents', icon: FileText, label: 'Documents' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { to: '/anomalies', icon: AlertTriangle, label: 'Anomalies' },
      { to: '/duplicates', icon: Copy, label: 'Duplicates' },
      { to: '/compare', icon: GitCompare, label: 'Compare' },
      { to: '/search', icon: Search, label: 'Search' },
      { to: '/qa', icon: MessageCircleQuestion, label: 'Q&A' },
    ],
  },
];

const routeLabels = {
  '/dashboard': 'Dashboard Overview',
  '/upload': 'Upload Document',
  '/documents': 'Document Repository',
  '/anomalies': 'Anomaly Detection',
  '/duplicates': 'Duplicate Analysis',
  '/compare': 'Document Comparison',
  '/search': 'Deep Search',
  '/qa': 'Document Q&A',
};

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const getSectionTitle = () => {
    if (routeLabels[location.pathname]) return routeLabels[location.pathname];
    if (location.pathname.startsWith('/documents/')) return 'Document Details';
    return 'Workspace';
  };

  return (
    <div className={`app-layout ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <aside className="sidebar">
        <div className="sidebar-header">
          <Link to="/" className="logo">
            <span className="logo-mark">
              <FileCheck2 size={18} />
            </span>
            {!collapsed && <span className="logo-text">Documind</span>}
          </Link>
          <button
            className="collapse-btn"
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        <nav className="sidebar-nav">
          {navGroups.map((group) => (
            <div className="nav-section" key={group.label}>
              {!collapsed && <div className="nav-section-label">{group.label}</div>}
              {group.items.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `nav-item ${isActive ? 'active' : ''}`
                  }
                  title={collapsed ? label : undefined}
                >
                  <Icon size={19} />
                  {!collapsed && <span>{label}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          {!collapsed && (
            <div className="sidebar-version">
              <span>Documind v0.11.0</span>
            </div>
          )}
        </div>
      </aside>

      <main className="main-content">
        {/* Top Header with prominent "Back to Home" option for every section */}
        <header className="app-topbar">
          <div className="topbar-left">
            <Link to="/" className="back-to-home-btn" id="back-to-home-btn" title="Return to Documind Home Page">
              <ArrowLeft size={16} />
              <Home size={15} />
              <span>Back to Home</span>
            </Link>
            <div className="topbar-divider"></div>
            <div className="topbar-breadcrumb">
              <span className="breadcrumb-root">Documind</span>
              <span className="breadcrumb-sep">/</span>
              <span className="breadcrumb-page">{getSectionTitle()}</span>
            </div>
          </div>

          <div className="topbar-right">
            <div className="topbar-status-pill">
              <span className="status-indicator-dot"></span>
              <span>Pipeline Active</span>
            </div>
          </div>
        </header>

        <div className="page-content-wrapper">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
