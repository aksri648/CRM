import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Sparkles, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { listProposals, listApprovals, respondToApproval, discoverOpportunities } from '@/lib/api'

type Proposal = {
  id: string
  title: string
  audience: string
  channel: string
  predictedCTR: string
  predictedRevenue: string
  reasoning: string
  confidence: number
  status: 'pending' | 'approved' | 'rejected'
  createdAt: string
}

function mapProposal(raw: any, approval?: any): Proposal {
  const status = approval?.status || raw?.status || 'pending'
  return {
    id: raw?.id || raw?.proposalId || raw?._id || '',
    title: raw?.title || raw?.campaignName || raw?.name || 'Untitled',
    audience: raw?.audience || raw?.targetAudience || raw?.segment || `${raw?.audienceSize || 0} Customers`,
    channel: raw?.channel || raw?.channels || raw?.platform || 'Unknown',
    predictedCTR: raw?.predictedCTR || raw?.ctr || raw?.estimatedCTR || `${raw?.ctrPercent || 0}%`,
    predictedRevenue: raw?.predictedRevenue || raw?.revenue || raw?.estimatedRevenue || `₹${raw?.revenueAmount || 0}`,
    reasoning: raw?.reasoning || raw?.aiReasoning || raw?.rationale || raw?.description || '',
    confidence: raw?.confidence ?? raw?.confidenceScore ?? raw?.score ?? 0,
    status: status === 'approved' ? 'approved' : status === 'rejected' ? 'rejected' : 'pending',
    createdAt: raw?.createdAt || raw?.created || raw?.date || raw?.generatedAt || '',
  }
}

export function AgentProposals() {
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  async function fetchData() {
    try {
      setLoading(true)
      setError(null)
      const [rawProposals, approvals] = await Promise.all([
        listProposals(),
        listApprovals(),
      ])
      const approvalMap = new Map<string, any>()
      for (const a of approvals || []) {
        const key = a?.proposalId || a?.id || a?._id
        if (key) approvalMap.set(key, a)
      }
      const merged = (rawProposals || []).map((p: any) => {
        const key = p?.id || p?.proposalId || p?._id
        return mapProposal(p, key ? approvalMap.get(key) : undefined)
      })
      setProposals(merged)
    } catch {
      setError('Failed to load proposals.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  async function handleScan() {
    try {
      setScanning(true)
      await discoverOpportunities()
      await fetchData()
    } catch {
      setError('Scan failed. Please try again.')
    } finally {
      setScanning(false)
    }
  }

  async function handleAction(id: string, action: string) {
    try {
      setActionLoading(`${id}-${action}`)
      await respondToApproval(id, action)
      await fetchData()
    } catch {
      setError('Action failed. Please try again.')
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 320 }}>
        <Loader2 size={32} className="animate-spin" color="#14b8a6" />
      </div>
    )
  }

  if (error && proposals.length === 0) {
    return (
      <div>
        <div className="xeno-header">
          <div>
            <h1>Agent Proposals</h1>
            <p className="xeno-header-subtitle">AI-generated campaign proposals awaiting your review</p>
          </div>
        </div>
        <div style={{ textAlign: 'center', padding: 48, color: '#ef4444' }}>{error}</div>
      </div>
    )
  }

  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Agent Proposals</h1>
          <p className="xeno-header-subtitle">AI-generated campaign proposals awaiting your review</p>
        </div>
        <div className="xeno-header-actions">
          <Button variant="outline" size="sm" onClick={handleScan} disabled={scanning}>
            {scanning ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {scanning ? 'Scanning...' : 'Trigger Scan'}
          </Button>
        </div>
      </div>

      {error && (
        <div style={{ textAlign: 'center', padding: 16, color: '#ef4444', marginBottom: 16 }}>{error}</div>
      )}

      {proposals.length === 0 && !loading && (
        <div style={{ textAlign: 'center', padding: 48, color: '#64748b' }}>No proposals found.</div>
      )}

      {proposals.map((p, i) => (
        <div key={p.id || i} className="xeno-proposal-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <h3 style={{ fontSize: 18, fontWeight: 600 }}>{p.title}</h3>
                <span className="xeno-badge xeno-badge-gray" style={{ fontSize: 10 }}>{p.id}</span>
              </div>
              <p style={{ fontSize: 13, color: '#64748b' }}>Created: {p.createdAt}</p>
            </div>
            <span className={`xeno-badge ${p.status === 'approved' ? 'xeno-badge-success' : p.status === 'rejected' ? 'xeno-badge-danger' : 'xeno-badge-warning'}`}>
              {p.status === 'approved' ? 'Approved' : p.status === 'rejected' ? 'Rejected' : 'Pending'}
            </span>
          </div>

          <div style={{ display: 'flex', gap: 24, marginBottom: 16, flexWrap: 'wrap' }}>
            {[
              { label: 'Audience', value: p.audience },
              { label: 'Channel', value: p.channel },
              { label: 'Predicted CTR', value: p.predictedCTR },
              { label: 'Predicted Revenue', value: p.predictedRevenue, highlight: true },
              { label: 'Confidence', value: `${p.confidence}%`, highlight: true },
            ].map((m, j) => (
              <div key={j}>
                <div style={{ fontSize: 12, color: '#64748b' }}>{m.label}</div>
                <div style={{ fontSize: 15, fontWeight: 600, color: m.highlight ? (j === 4 ? '#14b8a6' : '#16a34a') : '#0f172a' }}>{m.value}</div>
              </div>
            ))}
          </div>

          <div style={{ padding: 12, background: '#f8fafc', borderRadius: 8, marginBottom: 16 }}>
            <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
              <Sparkles size={12} color="#14b8a6" /> AI Reasoning
            </div>
            <div style={{ fontSize: 13, color: '#475569', lineHeight: 1.5 }}>{p.reasoning}</div>
          </div>

          {p.status === 'pending' && (
            <div style={{ display: 'flex', gap: 10 }}>
              <Button
                size="sm"
                style={{ background: '#14b8a6' }}
                onClick={() => handleAction(p.id, 'approved')}
                disabled={actionLoading === `${p.id}-approved`}
              >
                {actionLoading === `${p.id}-approved` ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
                Approve
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleAction(p.id, 'rejected')}
                disabled={actionLoading === `${p.id}-rejected`}
              >
                {actionLoading === `${p.id}-rejected` ? <Loader2 size={14} className="animate-spin" /> : <XCircle size={14} />}
                Reject
              </Button>
              <Button size="sm" variant="outline">Edit</Button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
