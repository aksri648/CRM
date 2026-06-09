import { useState, useEffect } from 'react'
import { listOpportunities, discoverOpportunities } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { TrendingUp, Sparkles, Loader2 } from 'lucide-react'

const TYPE_EMOJI: Record<string, string> = {
  at_risk: '🔥',
  trending: '👟',
  cart: '🛒',
  loyalty: '💎',
  reengagement: '📱',
}

function getEmoji(opp: any) {
  return TYPE_EMOJI[opp.type] || opp.emoji || '💡'
}

function getTitle(opp: any) {
  return opp.title || opp.name || 'Opportunity'
}

function getAudience(opp: any) {
  return opp.audience || opp.target_audience || opp.segment_name || '—'
}

function getMetricRow(opp: any) {
  const ctr = opp.predicted_outcome?.expected_ctr || opp.expectedCTR || null
  const revenue = opp.expected_revenue || opp.expectedRevenue || null
  const confidence = opp.confidence_score || opp.predicted_outcome?.confidence || null

  return { ctr, revenue, confidence }
}

function getReasoning(opp: any) {
  return opp.reasoning || opp.supporting_data || 'No reasoning available.'
}

function formatRevenue(val: any) {
  if (!val) return null
  if (typeof val === 'string') return val
  if (typeof val === 'number') {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val)
  }
  return String(val)
}

export function Opportunities() {
  const [opportunities, setOpportunities] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function fetchOpportunities() {
    setLoading(true)
    setError(null)
    try {
      const res = await listOpportunities()
      setOpportunities(res.opportunities || [])
    } catch {
      setError('Failed to load opportunities.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchOpportunities() }, [])

  async function handleScan() {
    setScanning(true)
    try {
      await discoverOpportunities()
      await fetchOpportunities()
    } catch {
      setError('Scan failed. Please try again.')
    } finally {
      setScanning(false)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
        <Loader2 className="animate-spin" size={32} />
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
        <p style={{ color: '#ef4444' }}>{error}</p>
      </div>
    )
  }

  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Opportunities</h1>
          <p className="xeno-header-subtitle">AI-discovered marketing opportunities for your business</p>
        </div>
        <div className="xeno-header-actions">
          <Button variant="outline" size="sm" onClick={handleScan} disabled={scanning}>
            {scanning ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {scanning ? ' Scanning…' : ' Scan for Opportunities'}
          </Button>
        </div>
      </div>

      {opportunities.map((opp, i) => {
        const { ctr, revenue, confidence } = getMetricRow(opp)
        const rev = formatRevenue(revenue)
        return (
          <div key={opp.id || i} className="xeno-opportunity-card">
            <div className="xeno-opportunity-emoji">{getEmoji(opp)}</div>
            <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: '#0f172a' }}>{getTitle(opp)}</h3>
            <div style={{ display: 'flex', gap: 24, marginBottom: 16, flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: 12, color: '#64748b' }}>Audience</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#0f172a' }}>{getAudience(opp)}</div>
              </div>
              {ctr && (
                <div>
                  <div style={{ fontSize: 12, color: '#64748b' }}>Expected CTR</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#0f172a' }}>{ctr}</div>
                </div>
              )}
              {rev && (
                <div>
                  <div style={{ fontSize: 12, color: '#64748b' }}>Expected Revenue</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#16a34a' }}>{rev}</div>
                </div>
              )}
              {!rev && confidence && (
                <div>
                  <div style={{ fontSize: 12, color: '#64748b' }}>Confidence Score</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#0f172a' }}>{(confidence * 100).toFixed(0)}%</div>
                </div>
              )}
            </div>
            <div style={{ padding: 12, background: '#f8fafc', borderRadius: 8, marginBottom: 16 }}>
              <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                <TrendingUp size={12} color="#14b8a6" /> AI Reasoning
              </div>
              <div style={{ fontSize: 13, color: '#475569', lineHeight: 1.5 }}>{getReasoning(opp)}</div>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <Button size="sm" style={{ background: '#14b8a6' }} onClick={() => alert('Campaign generation started')}>Generate Campaign</Button>
              <Button size="sm" variant="outline" onClick={() => alert('Review proposal clicked')}>Review Proposal</Button>
              <Button size="sm" variant="outline" onClick={() => setOpportunities(prev => prev.filter((_, idx) => idx !== i))}>Dismiss</Button>
            </div>
          </div>
        )
      })}
    </div>
  )
}
