import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Users, Megaphone, Send, DollarSign,
  TrendingUp, TrendingDown, Sparkles, Clock, Lightbulb,
  CloudUpload, Layers, Rocket, BarChart3, ArrowRight
} from 'lucide-react'
import { getDashboardStats, listCampaigns } from '@/lib/api'

export function Dashboard() {
  const navigate = useNavigate()
  const [data, setData] = useState<any>(null)
  const [campaigns, setCampaigns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const [stats, camps] = await Promise.all([
          getDashboardStats(),
          listCampaigns({ page_size: 5 }),
        ])
        setData(stats)
        setCampaigns(stats.recent_campaigns?.length ? stats.recent_campaigns : camps.campaigns || [])
      } catch (e: any) {
        setError(e.message || 'Failed to load dashboard')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error}</div>
  if (!data) return <div>No dashboard data available.</div>

  const stats = [
    { title: 'Total Customers', value: (data.total_customers ?? 0).toLocaleString(), change: '+12.5%', icon: Users, color: '#3b82f6', bg: '#eff6ff', positive: true },
    { title: 'Active Campaigns', value: String(data.active_campaigns ?? 0), change: '+2 this week', icon: Megaphone, color: '#16a34a', bg: '#f0fdf4', positive: true },
    { title: 'Messages Sent', value: (data.total_sent ?? 0).toLocaleString(), change: '+12.3%', icon: Send, color: '#7c3aed', bg: '#faf5ff', positive: true },
    { title: 'Revenue Attributed', value: `$${(data.total_revenue ?? 0).toLocaleString()}`, change: '+5.4%', icon: DollarSign, color: '#f59e0b', bg: '#fffbeb', positive: true },
  ]

  const { avg_open_rate = 0, avg_ctr = 0, avg_conversion_rate = 0 } = data

  const insights = [
    {
      type: 'opportunity', icon: Lightbulb, color: '#14b8a6', title: 'Engagement',
      text: avg_open_rate > 25
        ? `Open rate of ${avg_open_rate}% is strong. Segment engaged users for premium campaigns to maximize ROI.`
        : `Open rate is ${avg_open_rate}%. A/B test subject lines and send times to improve engagement.`,
    },
    {
      type: 'timing', icon: Clock, color: '#f59e0b', title: 'Click Performance',
      text: avg_ctr > 10
        ? `CTR of ${avg_ctr}% shows content resonates well. Expand successful creatives to broader audiences.`
        : `CTR is ${avg_ctr}%. Personalize CTAs and offers to boost click-through rates.`,
    },
    {
      type: 'suggestion', icon: Sparkles, color: '#7c3aed', title: 'Conversion',
      text: avg_conversion_rate > 5
        ? `Conversion rate of ${avg_conversion_rate}% is above average. Double down on your top-performing channels.`
        : `Conversion rate at ${avg_conversion_rate}%. Refine targeting and landing pages for better results.`,
    },
  ]

  const channelLabel: Record<string, string> = { whatsapp: 'WhatsApp', sms: 'SMS', email: 'Email', rcs: 'RCS' }

  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Dashboard</h1>
          <p className="xeno-header-subtitle">Overview of your campaign engagement performance</p>
        </div>
        <div className="xeno-header-actions">
          <Button variant="outline" size="sm" onClick={() => navigate('/customers')}><CloudUpload size={14} /> Import</Button>
          <Button size="sm" onClick={() => navigate('/campaigns')}><Rocket size={14} /> New Campaign</Button>
        </div>
      </div>

      <div className="xeno-quick-actions">
        {[
          { icon: CloudUpload, label: 'Import Data', desc: 'Upload customers & orders', color: '#3b82f6', bg: '#eff6ff' },
          { icon: Layers, label: 'Build Segment', desc: 'Create audience segments', color: '#7c3aed', bg: '#faf5ff' },
          { icon: Rocket, label: 'Launch Campaign', desc: 'Send personalized messages', color: '#16a34a', bg: '#f0fdf4' },
          { icon: BarChart3, label: 'View Insights', desc: 'Analyze performance', color: '#f59e0b', bg: '#fffbeb' },
        ].map((item, i) => {
          const paths: Record<string, string> = {
            'Import Data': '/customers',
            'Build Segment': '/segments',
            'Launch Campaign': '/campaigns',
            'View Insights': '/analytics',
          }
          return (
          <div key={i} className="xeno-quick-action" onClick={() => navigate(paths[item.label])} style={{ cursor: 'pointer' }}>
            <div className="xeno-quick-action-icon" style={{ background: item.bg, color: item.color }}>
              <item.icon size={20} />
            </div>
            <div className="xeno-quick-action-label">{item.label}</div>
            <div className="xeno-quick-action-desc">{item.desc}</div>
          </div>
          )
        })}
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
            {campaigns.map((c: any, i: number) => (
              <tr key={c.id || i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '12px 16px', fontWeight: 500 }}>{c.name}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span className={`xeno-channel-tag xeno-channel-${c.channel || 'email'}`}>
                    {channelLabel[c.channel] || c.channel || 'Email'}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', color: '#475569' }}>{c.approval_status || '—'}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span className={`xeno-badge xeno-badge-${c.status === 'sent' || c.status === 'completed' ? 'success' : c.status === 'sending' ? 'info' : c.status === 'draft' ? 'warning' : 'purple'}`}>
                    {c.status ? c.status.charAt(0).toUpperCase() + c.status.slice(1) : '—'}
                  </span>
                </td>
                <td style={{ padding: '12px 16px' }}>{c.created_at ? new Date(c.created_at).toLocaleDateString() : '—'}</td>
                <td style={{ padding: '12px 16px' }}>{c.open_rate != null ? `${c.open_rate}%` : '—'}</td>
                <td style={{ padding: '12px 16px' }}>{c.click_rate != null ? `${c.click_rate}%` : '—'}</td>
                <td style={{ padding: '12px 16px', fontWeight: 600 }}>{c.revenue != null ? `$${c.revenue}` : '—'}</td>
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
