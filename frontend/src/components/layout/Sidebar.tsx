import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useClerk } from '@clerk/clerk-react'
import { useAppStore } from '@/store'
import {
  LayoutDashboard, Wand2, Lightbulb, Users, Layers, Megaphone,
  FlaskConical, BarChart3, GitCompare, Bot, Settings, LogOut, Brain,
} from 'lucide-react'
import { AICommandCentre } from '@/components/AICommandCentre'

const clerkEnabled = !!import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

function ClerkLogoutButton({ zustandLogout }: { zustandLogout: () => void }) {
  const { signOut } = useClerk()
  return (
    <button
      className="xeno-sidebar-logout"
      title="Sign out"
      onClick={async () => {
        try {
          await signOut()
        } finally {
          zustandLogout()
        }
      }}
    >
      <LogOut size={16} />
    </button>
  )
}

const navItems = [
  { section: 'Main' },
  { label: 'Dashboard', icon: LayoutDashboard, path: '/', badge: null as string | null },
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
  { label: 'AI Command Centre', icon: Brain, path: '#ai-cc', badge: 'Live' },
  { label: 'Settings', icon: Settings, path: '/settings', badge: null },
]

export function Sidebar() {
  const [showCC, setShowCC] = useState(false)
  const token = useAppStore((s) => s.token)
  const logout = useAppStore((s) => s.logout)

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
          ) : item.path === '#ai-cc' ? (
            <button
              key={item.path}
              className="xeno-nav-item"
              onClick={() => setShowCC(true)}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
              {item.badge && (
                <span className="xeno-nav-badge">{item.badge}</span>
              )}
            </button>
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
      <div className="xeno-sidebar-footer">
        <div className="xeno-sidebar-user">
          <div className="xeno-sidebar-avatar">A</div>
          <div className="xeno-sidebar-user-info">
            <div className="xeno-sidebar-user-name">Admin</div>
            <div className="xeno-sidebar-user-role">Admin</div>
          </div>
        </div>
        {token && (
          clerkEnabled ? (
            <ClerkLogoutButton zustandLogout={logout} />
          ) : (
            <button className="xeno-sidebar-logout" title="Sign out" onClick={logout}>
              <LogOut size={16} />
            </button>
          )
        )}
      </div>
      {showCC && <AICommandCentre onClose={() => setShowCC(false)} />}
    </div>
  )
}
