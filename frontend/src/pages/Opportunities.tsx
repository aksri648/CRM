import { Button } from '@/components/ui/button'
import { TrendingUp, Sparkles } from 'lucide-react'

const opportunities = [
  {
    emoji: '🔥',
    title: 'High Value Customers At Risk',
    audience: '342 Customers',
    expectedRevenue: '₹75,000',
    reasoning: 'These customers have LTV > ₹5,000 but haven\'t purchased in 45+ days. Sneaker category engagement is up 22% this week.',
    type: 'at_risk',
  },
  {
    emoji: '👟',
    title: 'Sneaker Category Trending',
    audience: 'Past Sneaker Buyers',
    expectedCTR: '17%',
    expectedRevenue: '₹45,000',
    reasoning: 'Sneaker browsing increased 34% in the last 7 days. Summer collection launch is the perfect trigger.',
    type: 'trending',
  },
  {
    emoji: '🛒',
    title: 'Cart Abandonment Increasing',
    audience: 'Recent Cart Abandoners',
    expectedRevenue: '₹28,000',
    reasoning: 'Cart abandonment rate increased to 68% this week. 1,245 customers with items in cart for 24+ hours.',
    type: 'cart',
  },
  {
    emoji: '💎',
    title: 'Loyalty Members Not Redeeming',
    audience: '1,876 Members',
    expectedRevenue: '₹52,000',
    reasoning: '3,456 loyalty points are expiring in 15 days. Only 12% of members have redeemed this quarter.',
    type: 'loyalty',
  },
  {
    emoji: '📱',
    title: 'App Inactive Users',
    audience: '2,134 Users',
    expectedRevenue: '₹35,000',
    reasoning: 'Users who installed the app but haven\'t opened it in 30+ days. Push notification re-engagement recommended.',
    type: 'reengagement',
  },
]

export function Opportunities() {
  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Opportunities</h1>
          <p className="xeno-header-subtitle">AI-discovered marketing opportunities for your business</p>
        </div>
        <div className="xeno-header-actions">
          <Button variant="outline" size="sm"><Sparkles size={14} /> Scan for Opportunities</Button>
        </div>
      </div>

      {opportunities.map((opp, i) => (
        <div key={i} className="xeno-opportunity-card">
          <div className="xeno-opportunity-emoji">{opp.emoji}</div>
          <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: '#0f172a' }}>{opp.title}</h3>
          <div style={{ display: 'flex', gap: 24, marginBottom: 16, flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: 12, color: '#64748b' }}>Audience</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#0f172a' }}>{opp.audience}</div>
            </div>
            {opp.expectedCTR && (
              <div>
                <div style={{ fontSize: 12, color: '#64748b' }}>Expected CTR</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#0f172a' }}>{opp.expectedCTR}</div>
              </div>
            )}
            <div>
              <div style={{ fontSize: 12, color: '#64748b' }}>Expected Revenue</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#16a34a' }}>{opp.expectedRevenue}</div>
            </div>
          </div>
          <div style={{ padding: 12, background: '#f8fafc', borderRadius: 8, marginBottom: 16 }}>
            <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
              <TrendingUp size={12} color="#14b8a6" /> AI Reasoning
            </div>
            <div style={{ fontSize: 13, color: '#475569', lineHeight: 1.5 }}>{opp.reasoning}</div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <Button size="sm" style={{ background: '#14b8a6' }}>Generate Campaign</Button>
            <Button size="sm" variant="outline">Review Proposal</Button>
            <Button size="sm" variant="outline">Dismiss</Button>
          </div>
        </div>
      ))}
    </div>
  )
}
