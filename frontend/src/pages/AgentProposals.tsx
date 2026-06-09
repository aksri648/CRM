import { Button } from '@/components/ui/button'
import { Sparkles, CheckCircle, XCircle } from 'lucide-react'

const proposals = [
  {
    id: 'P-001',
    title: 'Summer Sneaker Campaign',
    audience: '1,245 Customers',
    channel: 'WhatsApp',
    predictedCTR: '18%',
    predictedRevenue: '₹45,000',
    reasoning: 'Sneaker engagement increased 22% this week. Summer collection launch with 45 new SKUs.',
    confidence: 87,
    status: 'pending',
    createdAt: '2026-06-10',
  },
  {
    id: 'P-002',
    title: 'Cold Brew Coffee Promotion',
    audience: '3,210 Customers',
    channel: 'SMS + Email',
    predictedCTR: '15%',
    predictedRevenue: '₹32,000',
    reasoning: 'Cold brew searches up 40% in last 7 days. Temperature rising trend detected.',
    confidence: 82,
    status: 'pending',
    createdAt: '2026-06-09',
  },
  {
    id: 'P-003',
    title: 'Festival Season - Dormant Reactivation',
    audience: '2,847 Customers',
    channel: 'WhatsApp',
    predictedCTR: '21%',
    predictedRevenue: '₹75,000',
    reasoning: 'Festival season approaching. Historical data shows 3.2x higher conversion during this period.',
    confidence: 91,
    status: 'approved',
    createdAt: '2026-06-08',
  },
  {
    id: 'P-004',
    title: 'Cart Recovery - Weekend Flash',
    audience: '876 Customers',
    channel: 'RCS',
    predictedCTR: '24%',
    predictedRevenue: '₹28,000',
    reasoning: 'Cart abandonment at 68%. Weekend flash sales historically recover 12% of abandoned carts.',
    confidence: 78,
    status: 'rejected',
    createdAt: '2026-06-07',
  },
]

export function AgentProposals() {
  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Agent Proposals</h1>
          <p className="xeno-header-subtitle">AI-generated campaign proposals awaiting your review</p>
        </div>
        <div className="xeno-header-actions">
          <Button variant="outline" size="sm"><Sparkles size={14} /> Trigger Scan</Button>
        </div>
      </div>

      {proposals.map((p, i) => (
        <div key={i} className="xeno-proposal-card">
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
              <Button size="sm" style={{ background: '#14b8a6' }}><CheckCircle size={14} /> Approve</Button>
              <Button size="sm" variant="outline"><XCircle size={14} /> Reject</Button>
              <Button size="sm" variant="outline">Edit</Button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
