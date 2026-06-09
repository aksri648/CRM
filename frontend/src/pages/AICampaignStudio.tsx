import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Send, Sparkles, Users, Target, BarChart3, Wallet,
  CheckCircle, Pencil, Play, MessageSquare
} from 'lucide-react'

const suggestions = [
  'Increase repeat purchases',
  'Reactivate churned customers',
  'Promote summer collection',
  'Improve loyalty engagement',
  'Bring back customers who haven\'t purchased in 60 days',
]

export function AICampaignStudio() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([])
  const [generated, setGenerated] = useState(false)

  const handleSend = () => {
    if (!input.trim()) return
    setMessages([...messages, { role: 'user', content: input }])
    setGenerated(true)
    setInput('')
  }

  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>AI Campaign Studio</h1>
          <p className="xeno-header-subtitle">Describe your marketing goal and let AI build the campaign</p>
        </div>
      </div>

      <div className="xeno-studio-container">
        <div className="xeno-studio-chat">
          <div className="xeno-studio-messages">
            {!generated ? (
              <div className="xeno-studio-welcome">
                <div style={{ fontSize: 48, marginBottom: 16 }}><Sparkles size={48} style={{ color: '#14b8a6', margin: '0 auto' }} /></div>
                <h2>What marketing goal would you like to achieve?</h2>
                <p>Describe your objective and Xeno AI will generate a complete campaign strategy including audience, channels, messaging, and A/B tests.</p>
                <div className="xeno-suggestion-chips">
                  {suggestions.map((s, i) => (
                    <button
                      key={i}
                      className="xeno-suggestion-chip"
                      onClick={() => { setMessages([{ role: 'user', content: s }]); setGenerated(true) }}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, i) => (
                <div key={i} className={`xeno-message ${msg.role}`}>
                  <div className="xeno-message-bubble">{msg.content}</div>
                </div>
              ))
            )}

            {generated && (
              <div className="xeno-message assistant">
                <div className="xeno-message-bubble" style={{ maxWidth: '100%' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <Sparkles size={18} color="#14b8a6" />
                    <strong style={{ fontSize: 16 }}>AI Campaign Proposal</strong>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
                    {[
                      { label: 'Audience', value: 'High-Value Lapsed Buyers', icon: Users, color: '#3b82f6' },
                      { label: 'Audience Size', value: '2,847 customers', icon: Target, color: '#16a34a' },
                      { label: 'Channel', value: 'WhatsApp + SMS', icon: MessageSquare, color: '#7c3aed' },
                      { label: 'Predicted Open Rate', value: '72.5%', icon: BarChart3, color: '#f59e0b' },
                      { label: 'Predicted CTR', value: '18.3%', icon: BarChart3, color: '#f59e0b' },
                      { label: 'Predicted Revenue', value: '₹2,45,000', icon: Wallet, color: '#16a34a' },
                    ].map((item, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px', background: '#f8fafc', borderRadius: 8 }}>
                        <div style={{ width: 36, height: 36, borderRadius: 8, background: `${item.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <item.icon size={16} color={item.color} />
                        </div>
                        <div>
                          <div style={{ fontSize: 12, color: '#64748b' }}>{item.label}</div>
                          <div style={{ fontSize: 14, fontWeight: 600 }}>{item.value}</div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div style={{ marginBottom: 20 }}>
                    <strong style={{ fontSize: 14, color: '#0f172a' }}>Message Variants</strong>
                    <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                      {[
                        { variant: 'A - Discount', msg: 'Hey {name}! We miss you. Here\'s 20% off your next order. Use code COMEBACK20', type: 'whatsapp' },
                        { variant: 'B - Urgency', msg: '⏰ Your cart misses you! 24hr flash sale - 25% off everything. Shop now!', type: 'sms' },
                      ].map((v, i) => (
                        <div key={i} style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: 12, background: '#f8fafc' }}>
                          <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8, fontWeight: 600 }}>{v.variant}</div>
                          <div style={{ fontSize: 13, lineHeight: 1.5, marginBottom: 8 }}>{v.msg}</div>
                          <span className={`xeno-channel-tag xeno-channel-${v.type}`}>
                            {v.type === 'whatsapp' ? 'WhatsApp' : 'SMS'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div style={{ padding: 16, background: '#f0fdfa', borderRadius: 8, marginBottom: 20, border: '1px solid #ccfbf1' }}>
                    <strong style={{ fontSize: 14, color: '#0f172a' }}>AI Reasoning</strong>
                    <p style={{ fontSize: 13, color: '#475569', marginTop: 8, lineHeight: 1.6 }}>
                      These 2,847 customers have LTV {'>'} ₹2,000 but haven't purchased in 30-90 days. 
                      Historical data shows WhatsApp re-engagement campaigns achieve 72.5% open rates 
                      with this segment. Discount-based offers convert at 4.2% vs 2.8% for emotional appeals. 
                      Recommended send time: Tuesday 10:30 AM.
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: 10 }}>
                    <Button style={{ background: '#14b8a6' }}><CheckCircle size={14} /> Approve</Button>
                    <Button variant="outline"><Pencil size={14} /> Edit</Button>
                    <Button variant="outline"><Play size={14} /> Launch</Button>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="xeno-studio-input">
            <input
              placeholder="Describe your marketing goal..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />
            <Button style={{ background: '#14b8a6', borderRadius: '50%', width: 44, height: 44, padding: 0 }} onClick={handleSend}>
              <Send size={18} />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
