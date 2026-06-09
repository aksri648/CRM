import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Users, Megaphone, Send, DollarSign,
  TrendingUp, TrendingDown, Sparkles, Clock, Lightbulb,
  CloudUpload, Layers, Rocket, BarChart3, ArrowRight
} from 'lucide-react'

const stats = [
  { title: 'Total Customers', value: '12,486', change: '+5.2%', icon: Users, color: '#3b82f6', bg: '#eff6ff', positive: true },
  { title: 'Active Campaigns', value: '8', change: '+2 this week', icon: Megaphone, color: '#16a34a', bg: '#f0fdf4', positive: true },
  { title: 'Messages Sent (30d)', value: '34.5K', change: '+12.3%', icon: Send, color: '#7c3aed', bg: '#faf5ff', positive: true },
  { title: 'Revenue Attributed', value: '$63.5K', change: '-2.1%', icon: DollarSign, color: '#f59e0b', bg: '#fffbeb', positive: false },
]

const campaigns = [
  { name: 'Summer Sale Announcement', channel: 'whatsapp', segment: 'High Value', status: 'success', statusLabel: 'Delivered', sent: '5,432', openRate: '71.3%', clickRate: '22.7%', revenue: '$23,456' },
  { name: 'New Collection Launch', channel: 'email', segment: 'All Customers', status: 'purple', statusLabel: 'Opened', sent: '8,765', openRate: '49.3%', clickRate: '11.3%', revenue: '$8,765' },
  { name: 'Loyalty Rewards Reminder', channel: 'sms', segment: 'Loyalty Members', status: 'warning', statusLabel: 'Clicked', sent: '2,345', openRate: '80.0%', clickRate: '27.9%', revenue: '$12,345' },
  { name: 'Flash Sale - 50% Off', channel: 'rcs', segment: 'Recent Purchasers', status: 'info', statusLabel: 'Sending', sent: '3,456', openRate: '—', clickRate: '—', revenue: '—' },
]

const insights = [
  { type: 'opportunity', icon: Lightbulb, color: '#14b8a6', title: 'Opportunity', text: '342 high-value customers haven\'t purchased in 30 days. A re-engagement campaign could recover ~$15K.' },
  { type: 'timing', icon: Clock, color: '#f59e0b', title: 'Timing', text: 'WhatsApp campaigns sent between 10-11 AM show 23% higher open rates for your audience.' },
  { type: 'suggestion', icon: Sparkles, color: '#7c3aed', title: 'Suggestion', text: 'Cart abandoners respond 2.5x better to SMS with discount codes vs. generic reminders.' },
]

export function Dashboard() {
  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Dashboard</h1>
          <p className="xeno-header-subtitle">Overview of your campaign engagement performance</p>
        </div>
        <div className="xeno-header-actions">
          <Button variant="outline" size="sm"><CloudUpload size={14} /> Export</Button>
          <Button size="sm"><Rocket size={14} /> New Campaign</Button>
        </div>
      </div>

      <div className="xeno-quick-actions">
        {[
          { icon: CloudUpload, label: 'Import Data', desc: 'Upload customers & orders', color: '#3b82f6', bg: '#eff6ff' },
          { icon: Layers, label: 'Build Segment', desc: 'Create audience segments', color: '#7c3aed', bg: '#faf5ff' },
          { icon: Rocket, label: 'Launch Campaign', desc: 'Send personalized messages', color: '#16a34a', bg: '#f0fdf4' },
          { icon: BarChart3, label: 'View Insights', desc: 'Analyze performance', color: '#f59e0b', bg: '#fffbeb' },
        ].map((item, i) => (
          <div key={i} className="xeno-quick-action">
            <div className="xeno-quick-action-icon" style={{ background: item.bg, color: item.color }}>
              <item.icon size={20} />
            </div>
            <div className="xeno-quick-action-label">{item.label}</div>
            <div className="xeno-quick-action-desc">{item.desc}</div>
          </div>
        ))}
      </div>

      <div className="xeno-stats-grid">
        {stats.map((s, i) => (
          <div key={i} className="xeno-stat-card">
            <div className="xeno-stat-header">
              <span className="xeno-stat-title">{s.title}</span>
              <div className="xeno-stat-icon" style={{ background: s.bg, color: s.color }}>
                <s.icon size={16} />
              </div>
            </div>
            <div className="xeno-stat-value">{s.value}</div>
            <div className={`xeno-stat-change ${s.positive ? 'positive' : 'negative'}`}>
              {s.positive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {s.change}
            </div>
          </div>
        ))}
      </div>

      <div className="xeno-card">
        <div className="xeno-card-header">
          <h2 className="xeno-card-title">Recent Campaigns</h2>
          <Button variant="ghost" size="sm">View All <ArrowRight size={14} /></Button>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Campaign', 'Channel', 'Segment', 'Status', 'Sent', 'Open Rate', 'Click Rate', 'Revenue'].map((h, i) => (
                <th key={i} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b', fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.5px', borderBottom: '1px solid #f1f5f9' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {campaigns.map((c, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '12px 16px', fontWeight: 500 }}>{c.name}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span className={`xeno-channel-tag xeno-channel-${c.channel}`}>
                    {c.channel === 'whatsapp' ? 'WhatsApp' : c.channel === 'sms' ? 'SMS' : c.channel === 'email' ? 'Email' : 'RCS'}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', color: '#475569' }}>{c.segment}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span className={`xeno-badge xeno-badge-${c.status}`}>{c.statusLabel}</span>
                </td>
                <td style={{ padding: '12px 16px' }}>{c.sent}</td>
                <td style={{ padding: '12px 16px' }}>{c.openRate}</td>
                <td style={{ padding: '12px 16px' }}>{c.clickRate}</td>
                <td style={{ padding: '12px 16px', fontWeight: 600 }}>{c.revenue}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="xeno-card">
        <div className="xeno-card-header">
          <h2 className="xeno-card-title">AI Insights</h2>
          <Badge variant="secondary" style={{ background: '#dcfce7', color: '#15803d' }}>
            <Sparkles size={12} style={{ marginRight: 4 }} /> AI Generated
          </Badge>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {insights.map((insight, i) => (
            <div key={i} className={`xeno-insight xeno-insight-${insight.type}`}>
              <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                <insight.icon size={14} color={insight.color} />
                {insight.title}
              </div>
              <div style={{ fontSize: 14, fontWeight: 500, lineHeight: 1.5 }}>{insight.text}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
