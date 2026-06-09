// TODO: Replace mock data with real A/B test API endpoints once they exist on the backend

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Sparkles, Trophy, Loader2 } from 'lucide-react'

const mockAbTests = [
  {
    name: 'Summer Sale Offer Test',
    status: 'Completed',
    winner: 'A - Discount',
    variants: [
      { label: 'A - Discount', message: 'Hey {name}! ☀️ Summer sale is here! Get 20% off on all summer essentials. Use code SUMMER20. Shop now!', openRate: '72.5%', ctr: '22.3%', conversion: '4.8%', revenue: '$12,345', winner: true },
      { label: 'B - Urgency', message: '⏰ LAST CALL! Summer sale ends in 24 hours! 25% off everything. Don\'t miss out → [link]', openRate: '68.2%', ctr: '18.7%', conversion: '3.9%', revenue: '$9,876', winner: false },
    ],
  },
  {
    name: 'Re-engagement Channel Test',
    status: 'Running',
    winner: null,
    variants: [
      { label: 'A - WhatsApp', message: 'Hey {name}, we miss you! Here\'s a special 15% off just for you. Use code MISSYOU15.', openRate: '78.3%', ctr: '24.1%', conversion: '—', revenue: '—', winner: false },
      { label: 'B - SMS', message: 'We missed you! 15% off your next order. Code: MISSYOU15. Valid for 7 days.', openRate: '82.1%', ctr: '28.5%', conversion: '—', revenue: '—', winner: false },
    ],
  },
  {
    name: 'Loyalty Points Reminder',
    status: 'Completed',
    winner: 'B - Emotional',
    variants: [
      { label: 'A - Transactional', message: 'You have 500 loyalty points expiring soon. Redeem them before June 30.', openRate: '45.2%', ctr: '12.3%', conversion: '2.1%', revenue: '$3,456', winner: false },
      { label: 'B - Emotional', message: 'Your points are waiting! 💎 500 loyalty points ready to be turned into something special. Don\'t let them expire!', openRate: '62.8%', ctr: '21.5%', conversion: '4.3%', revenue: '$7,890', winner: true },
    ],
  },
]

export function ABTests() {
  const [loading, setLoading] = useState(true)
  const [abTests] = useState(mockAbTests)

  useEffect(() => {
    setLoading(false)
  }, [])

  if (loading) {
    return (
      <div className="xeno-header">
        <div>
          <h1>A/B Tests</h1>
          <p className="xeno-header-subtitle">Design and analyze campaign experiments</p>
        </div>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: 60 }}>
          <Loader2 size={32} className="animate-spin" style={{ color: '#14b8a6' }} />
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>A/B Tests</h1>
          <p className="xeno-header-subtitle">Design and analyze campaign experiments</p>
        </div>
        <div className="xeno-header-actions">
          <Button size="sm" style={{ background: '#14b8a6' }}><Sparkles size={14} /> AI Generate Test</Button>
          <Button size="sm" variant="outline">Create Manual Test</Button>
        </div>
      </div>

      {abTests.map((test, i) => (
        <div key={i} className="xeno-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <h3 style={{ fontSize: 16, fontWeight: 600 }}>{test.name}</h3>
              {test.winner ? (
                <Badge style={{ background: '#dcfce7', color: '#15803d' }}>
                  <Trophy size={12} style={{ marginRight: 4 }} /> {test.winner}
                </Badge>
              ) : (
                <Badge style={{ background: '#dbeafe', color: '#1d4ed8' }}>Running</Badge>
              )}
            </div>
            <span className="xeno-badge xeno-badge-gray">{test.status}</span>
          </div>
          <div className="xeno-ab-variants">
            {test.variants.map((v, j) => (
              <div key={j} className={`xeno-ab-variant ${v.winner ? 'winner' : ''}`}>
                {v.winner && <div style={{ position: 'absolute', top: -10, right: 12, background: '#14b8a6', color: 'white', fontSize: 10, padding: '2px 8px', borderRadius: 10, fontWeight: 600 }}>WINNER</div>}
                <div className="xeno-ab-variant-label">{v.label}</div>
                <div className="xeno-ab-variant-message">{v.message}</div>
                <div className="xeno-ab-stats">
                  {[
                    { label: 'Open Rate', value: v.openRate },
                    { label: 'CTR', value: v.ctr },
                    { label: 'Conversion', value: v.conversion },
                    { label: 'Revenue', value: v.revenue },
                  ].map((stat, k) => (
                    <div key={k} className="xeno-ab-stat">
                      <div className="xeno-ab-stat-value">{stat.value}</div>
                      <div className="xeno-ab-stat-label">{stat.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
