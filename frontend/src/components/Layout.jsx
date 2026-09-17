import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  FileText,
  AlertTriangle,
  Copy,
  Search,
  MessageCircleQuestion,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import './Layout.css';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/upload', icon: Upload, label: 'Upload' },
  { to: '/documents', icon: FileText, label: 'Documents' },
  { to: '/anomalies', icon: AlertTriangle, label: 'Anomalies' },
  { to: '/duplicates', icon: Copy, label: 'Duplicates' },
  { to: '/search', icon: Search, label: 'Search' },
  { to: '/qa', icon: MessageCircleQuestion, label: 'Q&A' },
];

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`app-layout ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <Sparkles size={22} className="logo-icon" />
            {!collapsed && <span className="logo-text">Nexora</span>}
          </div>
          <button
            className="collapse-btn"
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active' : ''}`
              }
              title={collapsed ? label : undefined}
            >
              <Icon size={20} />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          {!collapsed && (
            <div className="sidebar-version">
              <span>v0.11.0</span>
            </div>
          )}
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
