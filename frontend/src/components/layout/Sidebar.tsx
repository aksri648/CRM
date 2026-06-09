import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Wand2,
  Lightbulb,
  Users,
  Layers,
  Megaphone,
  FlaskConical,
  BarChart3,
  GitCompare,
  Bot,
  Settings,
} from 'lucide-react'

const navItems = [
  { section: 'Main' },
  { label: 'Dashboard', icon: LayoutDashboard, path: '/', badge: null },
  { label: 'AI Campaign Studio', icon: Wand2, path: '/ai-studio', badge: 'New' },
  { label: 'Opportunities', icon: Lightbulb, path: '/opportunities', badge: '5' },
  { label: 'Agent Proposals', icon: Bot, path: '/proposals', badge: '3' },

  { section: 'Audience' },
  { label: 'Customers', icon: Users, path: '/customers', badge: null },
  { label: 'Segments', icon: Layers, path: '/segments', badge: null },

  { section: 'Engage' },
  { label: 'Campaigns', icon: Megaphone, path: '/campaigns', badge: null },
  { label: 'A/B Tests', icon: FlaskConical, path: '/ab-tests', badge: null },

  { section: 'Analyze' },
  { label: 'Analytics', icon: BarChart3, path: '/analytics', badge: null },
  { label: 'Pipeline Monitor', icon: GitCompare, path: '/pipeline', badge: null },

  { section: 'System' },
  { label: 'Settings', icon: Settings, path: '/settings', badge: null },
]

export function Sidebar() {
  return (
    <div className="xeno-sidebar">
      <div className="xeno-logo">
        <div className="xeno-logo-icon">X</div>
        Xeno AI
      </div>
      <nav className="xeno-nav-menu">
        {navItems.map((item, i) =>
          'section' in item ? (
            <div key={i} className="xeno-nav-section">{item.section}</div>
          ) : (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `xeno-nav-item ${isActive ? 'active' : ''}`
              }
            >
              <item.icon size={18} />
              <span>{item.label}</span>
              {item.badge && (
                <span className="xeno-nav-badge">{item.badge}</span>
              )}
            </NavLink>
          )
        )}
      </nav>
    </div>
  )
}
