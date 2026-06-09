import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import { listCampaigns } from '@/lib/api'

function fmt(n: number | null | undefined): string {
  if (n === null || n === undefined) return '\u2014'
  return n.toLocaleString()
}

function fmtCurrency(n: number | null | undefined): string {
  if (n === null || n === undefined) return '\u2014'
  return '$' + n.toLocaleString()
}

const channelLabels: Record<string, string> = {
  whatsapp: 'WhatsApp',
  email: 'Email',
  sms: 'SMS',
  rcs: 'RCS',
}

const statusBadgeMap: Record<string, string> = {
  launched: 'success',
  sending: 'info',
  draft: 'gray',
  paused: 'warning',
  completed: 'success',
  failed: 'error',
}

const statusLabelMap: Record<string, string> = {
  launched: 'Delivered',
  sending: 'Sending',
  draft: 'Draft',
  paused: 'Paused',
  completed: 'Completed',
  failed: 'Failed',
}

export function Campaigns() {
  const [campaigns, setCampaigns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    listCampaigns()
      .then((res) => setCampaigns(res.campaigns))
      .catch((err) => setError(err?.message || 'Failed to load campaigns'))
      .finally(() => setLoading(false))
  }, [])

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

      {loading && <p style={{ textAlign: 'center', color: '#64748b', padding: 40 }}>Loading campaigns...</p>}
      {error && <p style={{ textAlign: 'center', color: '#dc2626', padding: 40 }}>{error}</p>}

      {!loading && !error && campaigns.length === 0 && (
        <p style={{ textAlign: 'center', color: '#64748b', padding: 40 }}>No campaigns found.</p>
      )}

      {!loading && !error && campaigns.map((c, i) => (
        <div key={c.id ?? i} className="xeno-card" style={{ cursor: 'pointer' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{c.name}</h3>
              <div style={{ display: 'flex', gap: 20, fontSize: 13, color: '#64748b' }}>
                <span>Channel: <span className={`xeno-channel-tag xeno-channel-${c.channel}`}>
                  {channelLabels[c.channel] ?? c.channel}
                </span></span>
                <span>Segment: {c.segment_name}</span>
              </div>
            </div>
            <span className={`xeno-badge xeno-badge-${statusBadgeMap[c.status] ?? 'gray'}`}>
              {statusLabelMap[c.status] ?? c.status}
            </span>
          </div>
          <div style={{ display: 'flex', gap: 24, paddingTop: 16, borderTop: '1px solid #f1f5f9' }}>
            {[
              { label: 'Sent', value: fmt(c.sent_count) },
              { label: 'Delivered', value: fmt(c.delivered_count) },
              { label: 'Opened', value: fmt(c.open_count) },
              { label: 'Clicked', value: fmt(c.click_count) },
              { label: 'Converted', value: fmt(c.conversion_count) },
              { label: 'Revenue', value: fmtCurrency(c.revenue), highlight: true },
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
