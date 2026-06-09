import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Sparkles, Plus, Loader2 } from 'lucide-react'
import { listSegments, createSegment, snapshotSegment, listOpportunities } from '@/lib/api'

export function Segments() {
  const [aiOpportunities, setAiOpportunities] = useState<any[]>([])
  const [segments, setSegments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [builderName, setBuilderName] = useState('')
  const [conditions, setConditions] = useState([{ field: 'Last Purchase', op: 'Greater than', value: '' }])

  useEffect(() => {
    async function fetch() {
      try {
        setLoading(true)
        const [oppRes, segRes] = await Promise.all([
          listOpportunities({ status: 'pending' }),
          listSegments(),
        ])
        setAiOpportunities(oppRes.opportunities || [])
        setSegments(segRes.segments || [])
      } catch (e: any) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [])

  const getSize = (item: any) => item.customer_count ?? item.size ?? 0

  if (loading) {
    return <div style={{ color: '#64748b', padding: 40, textAlign: 'center' }}><Loader2 size={24} className="animate-spin" style={{ margin: '0 auto 8px' }} /><div>Loading...</div></div>
  }

  if (error) {
    return <div style={{ color: '#ef4444', padding: 40, textAlign: 'center' }}>Error: {error}</div>
  }

  const handleUseOpportunity = async (id: string) => {
    try {
      await snapshotSegment(id)
      const segRes = await listSegments()
      setSegments(segRes.segments || [])
    } catch (e: any) {
      setError(e.message)
    }
  }

  const addCondition = () => setConditions([...conditions, { field: 'Last Purchase', op: 'Greater than', value: '' }])
  const removeCondition = (i: number) => setConditions(conditions.filter((_, idx) => idx !== i))
  const updateCondition = (i: number, key: string, val: string) => {
    const c = [...conditions]
    ;(c[i] as any)[key] = val
    setConditions(c)
  }

  const handleCreate = async () => {
    try {
      await createSegment({ name: builderName || 'Custom Segment', criteria: { logic: 'AND', conditions } })
      setBuilderName('')
      setConditions([{ field: 'Last Purchase', op: 'Greater than', value: '' }])
      const segRes = await listSegments()
      setSegments(segRes.segments || [])
    } catch (e: any) {
      setError(e.message)
    }
  }

  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Segments</h1>
          <p className="xeno-header-subtitle">Build and manage audience segments</p>
        </div>
        <div className="xeno-header-actions">
          <Button size="sm" style={{ background: '#14b8a6' }}><Sparkles size={14} /> AI Segment Builder</Button>
          <Button size="sm" variant="outline"><Plus size={14} /> Create Segment</Button>
        </div>
      </div>

      <Tabs defaultValue="ai" style={{ marginBottom: 24 }}>
        <TabsList>
          <TabsTrigger value="ai">AI-Suggested</TabsTrigger>
          <TabsTrigger value="manual">Manual Segments</TabsTrigger>
          <TabsTrigger value="builder">Segment Builder</TabsTrigger>
        </TabsList>

        <TabsContent value="ai">
          <div className="xeno-card">
            <div className="xeno-card-header">
              <h2 className="xeno-card-title">AI-Suggested Segments</h2>
              <Badge style={{ background: '#dcfce7', color: '#15803d' }}><Sparkles size={12} style={{ marginRight: 4 }} /> AI Powered</Badge>
            </div>
            <p style={{ color: '#64748b', marginBottom: 16, fontSize: 14 }}>
              Based on your customer data, our AI has identified these high-potential segments:
            </p>
            {aiOpportunities.length === 0 && <p style={{ color: '#94a3b8', fontSize: 14 }}>No AI-suggested segments available.</p>}
            {aiOpportunities.map((s, i) => (
              <div key={s.id || i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 0', borderBottom: i < aiOpportunities.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                <div>
                  <h4 style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>{s.name || s.segment_name}</h4>
                  <p style={{ fontSize: 13, color: '#64748b' }}>{s.description || s.desc}</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Badge variant="secondary" style={{ fontSize: 13, padding: '4px 12px' }}>{getSize(s)} customers</Badge>
                  <Button size="sm" variant="outline" onClick={() => handleUseOpportunity(s.id)}>Use</Button>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="manual">
          <div className="xeno-card">
            <div className="xeno-card-header">
              <h2 className="xeno-card-title">Your Segments</h2>
              <Button size="sm" variant="outline">View All</Button>
            </div>
            {segments.length === 0 && <p style={{ color: '#94a3b8', fontSize: 14 }}>No segments yet.</p>}
            {segments.map((s, i) => (
              <div key={s.id || i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 0', borderBottom: i < segments.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                <div>
                  <h4 style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>{s.name}</h4>
                  <p style={{ fontSize: 13, color: '#64748b' }}>{s.description}</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Badge variant="secondary" style={{ fontSize: 13, padding: '4px 12px' }}>{getSize(s)} customers</Badge>
                  <Button size="sm" variant="outline" onClick={() => snapshotSegment(s.id)}>Edit</Button>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="builder">
          <div className="xeno-card">
            <div className="xeno-card-header">
              <h2 className="xeno-card-title">Segment Builder</h2>
            </div>
            <div style={{ marginBottom: 16 }}>
              <input
                type="text"
                placeholder="Segment name"
                value={builderName}
                onChange={e => setBuilderName(e.target.value)}
                style={{ border: '1px solid #e2e8f0', padding: '8px 12px', borderRadius: 6, fontSize: 13, outline: 'none', width: '100%', boxSizing: 'border-box' }}
              />
            </div>
            <div className="xeno-condition-logic">
              <button className="xeno-filter-chip active">AND</button>
              <button className="xeno-filter-chip">OR</button>
            </div>
            <div className="xeno-segment-conditions">
              {conditions.map((c, i) => (
                <div key={i} className="xeno-condition-row">
                  <select
                    value={c.field}
                    onChange={e => updateCondition(i, 'field', e.target.value)}
                    className="xeno-filter-chip" style={{ background: 'white', border: '1px solid #e2e8f0', padding: '8px 12px', borderRadius: 6, fontSize: 13 }}
                  >
                    <option>Last Purchase</option>
                    <option>Total Spend</option>
                    <option>Order Count</option>
                    <option>Category</option>
                  </select>
                  <select
                    value={c.op}
                    onChange={e => updateCondition(i, 'op', e.target.value)}
                    className="xeno-filter-chip" style={{ background: 'white', border: '1px solid #e2e8f0', padding: '8px 12px', borderRadius: 6, fontSize: 13 }}
                  >
                    <option>Greater than</option>
                    <option>Less than</option>
                    <option>Equals</option>
                    <option>Between</option>
                  </select>
                  <input
                    type="text"
                    placeholder="Value"
                    value={c.value}
                    onChange={e => updateCondition(i, 'value', e.target.value)}
                    style={{ border: '1px solid #e2e8f0', padding: '8px 12px', borderRadius: 6, fontSize: 13, outline: 'none', width: 120 }}
                  />
                  <button onClick={() => removeCondition(i)} style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer', fontSize: 18 }}>×</button>
                </div>
              ))}
              <Button size="sm" variant="outline" style={{ marginTop: 8 }} onClick={addCondition}>+ Add Condition</Button>
            </div>
            <div className="xeno-segment-preview" style={{ marginTop: 20, padding: 16, background: '#f0fdfa', borderRadius: 8, border: '1px solid #ccfbf1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <strong style={{ fontSize: 14 }}>Segment Preview</strong>
                <Badge style={{ background: '#14b8a6', color: 'white' }}>~TBD customers</Badge>
              </div>
              <p style={{ fontSize: 13, color: '#475569' }}>Conditions: {conditions.map(c => `${c.field} ${c.op} ${c.value || '?'}`).join(', ') || 'None'}</p>
            </div>
            <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
              <Button onClick={handleCreate} style={{ background: '#14b8a6' }}>Create Segment</Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
