import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Sparkles, TrendingUp, TrendingDown } from 'lucide-react'

const channelData = [
  { channel: 'WhatsApp', sent: '15,432', delivery: '98.2%', openRate: '78.5%', clickRate: '34.2%', conversion: '5.8%' },
  { channel: 'Email', sent: '12,345', delivery: '95.6%', openRate: '52.3%', clickRate: '18.7%', conversion: '3.2%' },
  { channel: 'SMS', sent: '10,567', delivery: '97.8%', openRate: '85.2%', clickRate: '42.1%', conversion: '4.5%' },
  { channel: 'RCS', sent: '7,334', delivery: '94.5%', openRate: '72.8%', clickRate: '28.9%', conversion: '4.1%' },
]

const topCampaigns = [
  { name: 'Loyalty Rewards Reminder', channel: 'sms', openRate: '85.2%', clickRate: '27.9%', conversion: '4.2%', revenue: '$12,345' },
  { name: 'Summer Sale Announcement', channel: 'whatsapp', openRate: '78.5%', clickRate: '22.7%', conversion: '4.5%', revenue: '$23,456' },
  { name: 'Flash Sale - 50% Off', channel: 'rcs', openRate: '72.8%', clickRate: '28.9%', conversion: '4.1%', revenue: '$18,901' },
  { name: 'New Collection Launch', channel: 'email', openRate: '52.3%', clickRate: '11.3%', conversion: '1.8%', revenue: '$8,765' },
]

export function Analytics() {
  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Analytics</h1>
          <p className="xeno-header-subtitle">Campaign performance and engagement metrics</p>
        </div>
      </div>

      <div className="xeno-stats-grid">
        {[
          { title: 'Total Messages', value: '45,678', change: '+15.3%', positive: true },
          { title: 'Avg Delivery Rate', value: '96.7%', change: '+1.2%', positive: true },
          { title: 'Avg Open Rate', value: '62.4%', change: '-2.1%', positive: false },
          { title: 'Avg Conversion Rate', value: '4.2%', change: '+0.8%', positive: true },
        ].map((s, i) => (
          <div key={i} className="xeno-stat-card">
            <div className="xeno-stat-title" style={{ marginBottom: 8, color: '#64748b' }}>{s.title}</div>
            <div className="xeno-stat-value">{s.value}</div>
            <div className={`xeno-stat-change ${s.positive ? 'positive' : 'negative'}`}>
              {s.positive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {s.change}
            </div>
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
                  {['Channel', 'Sent', 'Delivery Rate', 'Open Rate', 'Click Rate', 'Conversion'].map((h, i) => (
                    <th key={i} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b', fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.5px', borderBottom: '1px solid #f1f5f9' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {channelData.map((c, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '12px 16px' }}>
                      <span className={`xeno-channel-tag xeno-channel-${c.channel === 'WhatsApp' ? 'whatsapp' : c.channel.toLowerCase()}`}>{c.channel}</span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>{c.sent}</td>
                    <td style={{ padding: '12px 16px' }}>{c.delivery}</td>
                    <td style={{ padding: '12px 16px' }}>{c.openRate}</td>
                    <td style={{ padding: '12px 16px' }}>{c.clickRate}</td>
                    <td style={{ padding: '12px 16px' }}>{c.conversion}</td>
                  </tr>
                ))}
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
                  {['Campaign', 'Channel', 'Open Rate', 'Click Rate', 'Conversion', 'Revenue'].map((h, i) => (
                    <th key={i} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b', fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.5px', borderBottom: '1px solid #f1f5f9' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {topCampaigns.map((c, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 500 }}>{c.name}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span className={`xeno-channel-tag xeno-channel-${c.channel}`}>{c.channel === 'whatsapp' ? 'WhatsApp' : c.channel === 'sms' ? 'SMS' : c.channel === 'email' ? 'Email' : 'RCS'}</span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>{c.openRate}</td>
                    <td style={{ padding: '12px 16px' }}>{c.clickRate}</td>
                    <td style={{ padding: '12px 16px' }}>{c.conversion}</td>
                    <td style={{ padding: '12px 16px', fontWeight: 600 }}>{c.revenue}</td>
                  </tr>
                ))}
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
              {[
                { label: 'Total Sent', value: '45,678', pct: '100%', color: '#3b82f6', width: '100%' },
                { label: 'Delivered', value: '44,170', pct: '96.7%', color: '#16a34a', width: '85%' },
                { label: 'Opened', value: '27,562', pct: '62.4%', color: '#7c3aed', width: '65%' },
                { label: 'Clicked', value: '8,832', pct: '20.0%', color: '#f59e0b', width: '40%' },
                { label: 'Converted', value: '1,855', pct: '4.2%', color: '#14b8a6', width: '25%' },
              ].map((stage, i) => (
                <div key={i} className="xeno-funnel-stage" style={{ width: stage.width, background: stage.color }}>
                  <div className="xeno-funnel-label">
                    <span>{stage.label}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                    <span>{stage.value}</span>
                    <span style={{ opacity: 0.8, fontSize: 12 }}>{stage.pct}</span>
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
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {[
            { title: 'WhatsApp Dominance', text: 'WhatsApp continues to outperform other channels with 78.5% open rates. Consider shifting 30% of email budget to WhatsApp for higher ROI.', color: '#14b8a6' },
            { title: 'SMS Re-engagement Power', text: 'SMS shows 85.2% open rates for re-engagement campaigns. Cart abandonment recovery via SMS converts 2.5x better than email.', color: '#f59e0b' },
            { title: 'Timing Optimization', text: 'Campaigns sent between 10-11 AM see 23% higher engagement. Weekend campaigns have 15% lower CTR than weekday sends.', color: '#7c3aed' },
          ].map((insight, i) => (
            <div key={i} style={{ padding: 16, background: '#f8fafc', borderRadius: 8, border: `1px solid ${insight.color}20`, borderLeft: `3px solid ${insight.color}` }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: insight.color, marginBottom: 6 }}>{insight.title}</div>
              <div style={{ fontSize: 13, color: '#475569', lineHeight: 1.5 }}>{insight.text}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
