import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'

const campaigns = [
  { name: 'Summer Sale Announcement', channel: 'whatsapp', segment: 'High Value', status: 'success', label: 'Delivered', sent: '5,432', delivered: '5,201', opened: '3,876', clicked: '1,234', converted: '247', revenue: '$23,456' },
  { name: 'New Collection Launch', channel: 'email', segment: 'All Customers', status: 'purple', label: 'Opened', sent: '8,765', delivered: '8,234', opened: '4,321', clicked: '987', converted: '156', revenue: '$8,765' },
  { name: 'Loyalty Rewards Reminder', channel: 'sms', segment: 'Loyalty Members', status: 'warning', label: 'Clicked', sent: '2,345', delivered: '2,198', opened: '1,876', clicked: '654', converted: '98', revenue: '$12,345' },
  { name: 'Flash Sale - 50% Off', channel: 'rcs', segment: 'Recent Purchasers', status: 'info', label: 'Sending', sent: '3,456', delivered: '—', opened: '—', clicked: '—', converted: '—', revenue: '—' },
  { name: 'Weekend Special Offer', channel: 'whatsapp', segment: 'Frequent Shoppers', status: 'gray', label: 'Draft', sent: '—', delivered: '—', opened: '—', clicked: '—', converted: '—', revenue: '—' },
]

export function Campaigns() {
  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Campaigns</h1>
          <p className="xeno-header-subtitle">Manage and monitor your marketing campaigns</p>
        </div>
        <div className="xeno-header-actions">
          <Button size="sm"><Plus size={14} /> Create Campaign</Button>
        </div>
      </div>

      {campaigns.map((c, i) => (
        <div key={i} className="xeno-card" style={{ cursor: 'pointer' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{c.name}</h3>
              <div style={{ display: 'flex', gap: 20, fontSize: 13, color: '#64748b' }}>
                <span>Channel: <span className={`xeno-channel-tag xeno-channel-${c.channel}`}>
                  {c.channel === 'whatsapp' ? 'WhatsApp' : c.channel === 'sms' ? 'SMS' : c.channel === 'email' ? 'Email' : 'RCS'}
                </span></span>
                <span>Segment: {c.segment}</span>
              </div>
            </div>
            <span className={`xeno-badge xeno-badge-${c.status}`}>{c.label}</span>
          </div>
          <div style={{ display: 'flex', gap: 24, paddingTop: 16, borderTop: '1px solid #f1f5f9' }}>
            {[
              { label: 'Sent', value: c.sent },
              { label: 'Delivered', value: c.delivered },
              { label: 'Opened', value: c.opened },
              { label: 'Clicked', value: c.clicked },
              { label: 'Converted', value: c.converted },
              { label: 'Revenue', value: c.revenue, highlight: true },
            ].map((m, j) => (
              <div key={j} style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ fontSize: 18, fontWeight: 700, color: m.highlight ? '#16a34a' : '#0f172a' }}>{m.value}</div>
                <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{m.label}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
