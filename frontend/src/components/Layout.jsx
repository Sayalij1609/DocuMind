import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
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
      { to: '/search', icon: Search, label: 'Search' },
      { to: '/qa', icon: MessageCircleQuestion, label: 'Q&A' },
    ],
  },
];

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`app-layout ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-mark">
              <FileCheck2 size={18} />
            </span>
            {!collapsed && <span className="logo-text">Documind</span>}
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
