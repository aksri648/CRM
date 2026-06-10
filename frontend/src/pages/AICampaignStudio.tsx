import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { generateCampaign, listSegments } from '@/lib/api'
import {
  Send, Sparkles, Users, Target, BarChart3, Wallet,
  CheckCircle, Pencil, Play, MessageSquare, Loader2, AlertCircle
} from 'lucide-react'

const fallbackSuggestions = [
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
  const [campaignData, setCampaignData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [suggestionChips, setSuggestionChips] = useState<string[]>(fallbackSuggestions)

  useEffect(() => {
    listSegments(1, 10).then(res => {
      if (res.segments?.length) {
        const uniqueNames = [...new Set(res.segments.map((s: any) => s.name).filter(Boolean))]
        if (uniqueNames.length) setSuggestionChips(uniqueNames.slice(0, 5))
      }
    }).catch(() => {})
  }, [])

  const handleSend = async (goal?: string) => {
    const text = (goal || input).trim()
    if (!text) return
    setMessages([...messages, { role: 'user', content: text }])
    setInput('')
    setGenerated(true)
    setLoading(true)
    setError(null)
    setCampaignData(null)
    try {
      const data = await generateCampaign(text)
      setCampaignData(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to generate campaign. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const sd = campaignData?.supporting_data || {}
  const audienceSize = sd.audienceSize || sd.audience_size || sd.segment_size || '—'
  const audience = sd.audience || sd.segment || sd.target_audience || '—'
  const channel = sd.channel || sd.channels || sd.preferred_channel || '—'
  const openRate = sd.predictedOpenRate || sd.open_rate || sd.predicted_open_rate || '—'
  const ctr = sd.predictedCTR || sd.ctr || sd.predicted_ctr || '—'
  const revenue = sd.predictedRevenue || sd.revenue || sd.predicted_revenue || '—'
  const variants = sd.messageVariants || sd.variants || sd.message_variants || []

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
                  {suggestionChips.map((s, i) => (
                    <button
                      key={i}
                      className="xeno-suggestion-chip"
                      onClick={() => handleSend(s)}
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

            {loading && (
              <div className="xeno-message assistant">
                <div className="xeno-message-bubble" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Loader2 size={20} className="animate-spin" color="#14b8a6" />
                  <span>Xeno AI is crafting your campaign...</span>
                </div>
              </div>
            )}

            {error && (
              <div className="xeno-message assistant">
                <div className="xeno-message-bubble" style={{ border: '1px solid #fecaca', background: '#fef2f2' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <AlertCircle size={18} color="#ef4444" />
                    <strong style={{ color: '#dc2626' }}>Error</strong>
                  </div>
                  <p style={{ fontSize: 13, color: '#991b1b' }}>{error}</p>
                </div>
              </div>
            )}

            {campaignData && !loading && (
              <div className="xeno-message assistant">
                <div className="xeno-message-bubble" style={{ maxWidth: '100%' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <Sparkles size={18} color="#14b8a6" />
                    <strong style={{ fontSize: 16 }}>AI Campaign Proposal</strong>
                    {campaignData.confidence_score != null && (
                      <span style={{ marginLeft: 'auto', fontSize: 12, color: '#64748b', background: '#f1f5f9', padding: '2px 8px', borderRadius: 12 }}>
                        Confidence: {(campaignData.confidence_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
                    {[
                      { label: 'Audience', value: audience, icon: Users, color: '#3b82f6' },
                      { label: 'Audience Size', value: typeof audienceSize === 'number' ? audienceSize.toLocaleString() : audienceSize, icon: Target, color: '#16a34a' },
                      { label: 'Channel', value: channel, icon: MessageSquare, color: '#7c3aed' },
                      { label: 'Predicted Open Rate', value: openRate, icon: BarChart3, color: '#f59e0b' },
                      { label: 'Predicted CTR', value: ctr, icon: BarChart3, color: '#f59e0b' },
                      { label: 'Predicted Revenue', value: revenue, icon: Wallet, color: '#16a34a' },
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

                  {variants.length > 0 && (
                    <div style={{ marginBottom: 20 }}>
                      <strong style={{ fontSize: 14, color: '#0f172a' }}>Message Variants</strong>
                      <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                        {variants.map((v: any, i: number) => (
                          <div key={i} style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: 12, background: '#f8fafc' }}>
                            <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8, fontWeight: 600 }}>{v.variant || v.name || `Variant ${i + 1}`}</div>
                            <div style={{ fontSize: 13, lineHeight: 1.5, marginBottom: 8 }}>{v.message || v.text || v.content || ''}</div>
                            {(v.channel || v.type) && (
                              <span className={`xeno-channel-tag xeno-channel-${(v.channel || v.type).toLowerCase()}`}>
                                {v.channel || v.type}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {campaignData.reasoning && (
                    <div style={{ padding: 16, background: '#f0fdfa', borderRadius: 8, marginBottom: 20, border: '1px solid #ccfbf1' }}>
                      <strong style={{ fontSize: 14, color: '#0f172a' }}>AI Reasoning</strong>
                      <p style={{ fontSize: 13, color: '#475569', marginTop: 8, lineHeight: 1.6 }}>{campaignData.reasoning}</p>
                    </div>
                  )}

                  {campaignData.predicted_outcome && (
                    <div style={{ padding: 16, background: '#fffbeb', borderRadius: 8, marginBottom: 20, border: '1px solid #fde68a' }}>
                      <strong style={{ fontSize: 14, color: '#0f172a' }}>Predicted Outcome</strong>
                      <p style={{ fontSize: 13, color: '#475569', marginTop: 8, lineHeight: 1.6 }}>{campaignData.predicted_outcome}</p>
                    </div>
                  )}

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
              disabled={loading}
            />
            <Button
              style={{ background: '#14b8a6', borderRadius: '50%', width: 44, height: 44, padding: 0 }}
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
