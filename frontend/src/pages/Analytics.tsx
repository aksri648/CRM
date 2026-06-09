import { useState, useEffect } from 'react'
import { getChannelAnalytics, getDashboardStats } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Sparkles, TrendingUp, TrendingDown, Loader2 } from 'lucide-react'

interface DashboardStats {
  total_customers: number
  active_campaigns: number
  total_sent: number
  total_revenue: number
  avg_open_rate: number
  avg_ctr: number
  avg_conversion_rate: number
  channel_breakdown: any[]
  recent_campaigns: any[]
}

function formatNum(n: number): string {
  return n.toLocaleString()
}

function formatPct(n: number): string {
  return `${(n * 100).toFixed(1)}%`
}

function channelTagClass(ch: string): string {
  const m: Record<string, string> = { whatsapp: 'whatsapp', sms: 'sms', email: 'email', rcs: 'rcs' }
  return m[ch.toLowerCase()] || 'email'
}

function channelLabel(ch: string): string {
  const m: Record<string, string> = { whatsapp: 'WhatsApp', sms: 'SMS', email: 'Email', rcs: 'RCS' }
  return m[ch.toLowerCase()] || ch
}

export function Analytics() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [channelData, setChannelData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      getDashboardStats(),
      getChannelAnalytics(),
    ])
      .then(([s, c]) => {
        setStats(s as DashboardStats)
        setChannelData(Array.isArray(c) ? c : [])
      })
      .catch((err) => {
        setError(err.message || 'Failed to load analytics')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin" size={32} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="xeno-card" style={{ padding: 24, color: '#dc2626' }}>
        Failed to load analytics: {error}
      </div>
    )
  }

  const totalSent = stats?.total_sent ?? 0
  const avgOpenRate = stats?.avg_open_rate ?? 0
  const avgCtr = stats?.avg_ctr ?? 0
  const avgConversionRate = stats?.avg_conversion_rate ?? 0

  let deliveryRate = 0
  const breakdown = stats?.channel_breakdown ?? []
  if (breakdown.length > 0) {
    const totalDelivered = breakdown.reduce(
      (sum: number, ch: any) => sum + (ch.delivered ?? ch.sent ?? 0),
      0,
    )
    const totalSentAcross = breakdown.reduce(
      (sum: number, ch: any) => sum + (ch.sent ?? 0),
      0,
    )
    deliveryRate =
      totalSentAcross > 0 ? totalDelivered / totalSentAcross : 0
  }

  const statCards = [
    {
      title: 'Total Messages',
      value: formatNum(totalSent),
      change: null as string | null,
      positive: true,
    },
    {
      title: 'Avg Delivery Rate',
      value: deliveryRate > 0 ? formatPct(deliveryRate) : '—',
      change: null,
      positive: true,
    },
    {
      title: 'Avg Open Rate',
      value: formatPct(avgOpenRate),
      change: null,
      positive: true,
    },
    {
      title: 'Avg Conversion Rate',
      value: formatPct(avgConversionRate),
      change: null,
      positive: true,
    },
  ]

  const mappedChannels = channelData.map((c: any) => ({
    channel: c.channel ?? 'Unknown',
    sent: c.sent != null ? formatNum(c.sent) : '—',
    delivery: c.delivery_rate != null ? formatPct(c.delivery_rate) : '—',
    openRate: c.open_rate != null ? formatPct(c.open_rate) : '—',
    clickRate: c.click_rate != null ? formatPct(c.click_rate) : '—',
    conversion: c.conversion_rate != null ? formatPct(c.conversion_rate) : '—',
  }))

  const campaigns = stats?.recent_campaigns ?? []
  const mappedCampaigns = campaigns.map((c: any) => ({
    name: c.name ?? c.campaign_name ?? 'Untitled',
    channel: (c.channel ?? 'email').toLowerCase(),
    openRate: c.open_rate != null ? formatPct(c.open_rate) : '—',
    clickRate: c.click_rate != null ? formatPct(c.click_rate) : '—',
    conversion: c.conversion_rate != null ? formatPct(c.conversion_rate) : '—',
    revenue: c.revenue != null ? `$${formatNum(c.revenue)}` : '—',
  }))

  const funnelStages = [
    {
      label: 'Total Sent',
      value: formatNum(totalSent),
      pct: '100%',
      color: '#3b82f6',
      width: '100%',
    },
    {
      label: 'Delivered',
      value: formatNum(Math.round(totalSent * deliveryRate)),
      pct: formatPct(deliveryRate),
      color: '#16a34a',
      width: '85%',
    },
    {
      label: 'Opened',
      value: formatNum(Math.round(totalSent * avgOpenRate)),
      pct: formatPct(avgOpenRate),
      color: '#7c3aed',
      width: '65%',
    },
    {
      label: 'Clicked',
      value: formatNum(Math.round(totalSent * avgCtr)),
      pct: formatPct(avgCtr),
      color: '#f59e0b',
      width: '40%',
    },
    {
      label: 'Converted',
      value: formatNum(Math.round(totalSent * avgConversionRate)),
      pct: formatPct(avgConversionRate),
      color: '#14b8a6',
      width: '25%',
    },
  ]

  const thStyle: React.CSSProperties = {
    padding: '12px 16px',
    textAlign: 'left',
    fontWeight: 600,
    color: '#64748b',
    fontSize: 12,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    borderBottom: '1px solid #f1f5f9',
  }

  const tdStyle: React.CSSProperties = {
    padding: '12px 16px',
  }

  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Analytics</h1>
          <p className="xeno-header-subtitle">
            Campaign performance and engagement metrics
          </p>
        </div>
      </div>

      <div className="xeno-stats-grid">
        {statCards.map((s, i) => (
          <div key={i} className="xeno-stat-card">
            <div
              className="xeno-stat-title"
              style={{ marginBottom: 8, color: '#64748b' }}
            >
              {s.title}
            </div>
            <div className="xeno-stat-value">{s.value}</div>
            {s.change && (
              <div
                className={`xeno-stat-change ${s.positive ? 'positive' : 'negative'}`}
              >
                {s.positive ? (
                  <TrendingUp size={12} />
                ) : (
                  <TrendingDown size={12} />
                )}
                {s.change}
              </div>
            )}
          </div>
        ))}
      </div>

      <Tabs defaultValue="channels" style={{ marginBottom: 24 }}>
        <TabsList>
          <TabsTrigger value="channels">Channel Performance</TabsTrigger>
          <TabsTrigger value="campaigns">Top Campaigns</TabsTrigger>
          <TabsTrigger value="funnel">Campaign Funnel</TabsTrigger>
        </TabsList>

        <TabsContent value="channels">
          <div className="xeno-card">
            <div className="xeno-card-header">
              <h2 className="xeno-card-title">Performance by Channel</h2>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {[
                    'Channel',
                    'Sent',
                    'Delivery Rate',
                    'Open Rate',
                    'Click Rate',
                    'Conversion',
                  ].map((h, i) => (
                    <th key={i} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {mappedChannels.map((c, i) => (
                  <tr
                    key={i}
                    style={{ borderBottom: '1px solid #f1f5f9' }}
                  >
                    <td style={tdStyle}>
                      <span
                        className={`xeno-channel-tag xeno-channel-${channelTagClass(c.channel)}`}
                      >
                        {c.channel}
                      </span>
                    </td>
                    <td style={tdStyle}>{c.sent}</td>
                    <td style={tdStyle}>{c.delivery}</td>
                    <td style={tdStyle}>{c.openRate}</td>
                    <td style={tdStyle}>{c.clickRate}</td>
                    <td style={tdStyle}>{c.conversion}</td>
                  </tr>
                ))}
                {mappedChannels.length === 0 && (
                  <tr>
                    <td
                      colSpan={6}
                      style={{
                        ...tdStyle,
                        textAlign: 'center',
                        color: '#94a3b8',
                      }}
                    >
                      No channel data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </TabsContent>

        <TabsContent value="campaigns">
          <div className="xeno-card">
            <div className="xeno-card-header">
              <h2 className="xeno-card-title">Top Performing Campaigns</h2>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {[
                    'Campaign',
                    'Channel',
                    'Open Rate',
                    'Click Rate',
                    'Conversion',
                    'Revenue',
                  ].map((h, i) => (
                    <th key={i} style={thStyle}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {mappedCampaigns.map((c, i) => (
                  <tr
                    key={i}
                    style={{ borderBottom: '1px solid #f1f5f9' }}
                  >
                    <td style={{ ...tdStyle, fontWeight: 500 }}>
                      {c.name}
                    </td>
                    <td style={tdStyle}>
                      <span
                        className={`xeno-channel-tag xeno-channel-${channelTagClass(c.channel)}`}
                      >
                        {channelLabel(c.channel)}
                      </span>
                    </td>
                    <td style={tdStyle}>{c.openRate}</td>
                    <td style={tdStyle}>{c.clickRate}</td>
                    <td style={tdStyle}>{c.conversion}</td>
                    <td style={{ ...tdStyle, fontWeight: 600 }}>
                      {c.revenue}
                    </td>
                  </tr>
                ))}
                {mappedCampaigns.length === 0 && (
                  <tr>
                    <td
                      colSpan={6}
                      style={{
                        ...tdStyle,
                        textAlign: 'center',
                        color: '#94a3b8',
                      }}
                    >
                      No campaign data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </TabsContent>

        <TabsContent value="funnel">
          <div className="xeno-card">
            <div className="xeno-card-header">
              <h2 className="xeno-card-title">Campaign Funnel</h2>
            </div>
            <div className="xeno-funnel">
              {funnelStages.map((stage, i) => (
                <div
                  key={i}
                  className="xeno-funnel-stage"
                  style={{
                    width: stage.width,
                    background: stage.color,
                  }}
                >
                  <div className="xeno-funnel-label">
                    <span>{stage.label}</span>
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      gap: 16,
                      alignItems: 'center',
                    }}
                  >
                    <span>{stage.value}</span>
                    <span style={{ opacity: 0.8, fontSize: 12 }}>
                      {stage.pct}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>

      <div className="xeno-card">
        <div className="xeno-card-header">
          <h2 className="xeno-card-title">AI Insights</h2>
          <Badge style={{ background: '#dcfce7', color: '#15803d' }}>
            <Sparkles size={12} style={{ marginRight: 4 }} /> AI Generated
          </Badge>
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 16,
          }}
        >
          {[
            {
              title: 'Channel Performance',
              text: `${
                mappedChannels.length > 0
                  ? mappedChannels[0].channel
                  : 'Primary'
              } leads with ${mappedChannels.length > 0 ? mappedChannels[0].openRate : 'N/A'} open rate. Consider optimizing underperforming channels for better ROI.`,
              color: '#14b8a6',
            },
            {
              title: 'Engagement Trends',
              text: `Overall open rate is ${formatPct(avgOpenRate)} with a ${formatPct(avgConversionRate)} conversion rate. ${
                avgConversionRate > 0.05
                  ? 'Strong conversion performance indicates effective targeting.'
                  : 'Consider A/B testing messaging to improve conversion.'
              }`,
              color: '#f59e0b',
            },
            {
              title: 'Revenue Impact',
              text: `Total of ${formatNum(totalSent)} messages sent across all channels. ${
                (stats?.total_revenue ?? 0) > 0
                  ? `Revenue tracked at $${formatNum(stats!.total_revenue)}.`
                  : 'Enable revenue tracking to measure campaign ROI.'
              }`,
              color: '#7c3aed',
            },
          ].map((insight, i) => (
            <div
              key={i}
              style={{
                padding: 16,
                background: '#f8fafc',
                borderRadius: 8,
                border: `1px solid ${insight.color}20`,
                borderLeft: `3px solid ${insight.color}`,
              }}
            >
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: insight.color,
                  marginBottom: 6,
                }}
              >
                {insight.title}
              </div>
              <div
                style={{
                  fontSize: 13,
                  color: '#475569',
                  lineHeight: 1.5,
                }}
              >
                {insight.text}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
