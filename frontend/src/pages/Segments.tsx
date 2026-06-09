import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Sparkles, Plus } from 'lucide-react'

const aiSegments = [
  { name: 'High-Value At-Risk Customers', desc: 'Customers with high lifetime value who haven\'t purchased in the last 30 days', size: '342', type: 'ai' },
  { name: 'Potential Brand Advocates', desc: 'Frequent shoppers with high engagement rates and positive sentiment', size: '567', type: 'ai' },
  { name: 'Product Category - Footwear', desc: 'Customers who purchased footwear 3+ times and viewed footwear in the last 7 days', size: '891', type: 'ai' },
]

const manualSegments = [
  { name: 'VIP Customers', desc: 'Customers with lifetime value over ₹5,000 and at least 10 purchases', size: '1,234', type: 'manual' },
  { name: 'Cart Abandoners - Last 7 Days', desc: 'Customers who added items to cart but didn\'t complete purchase in the last 7 days', size: '456', type: 'manual' },
  { name: 'New Customers - First Purchase', desc: 'Customers who made their first purchase in the last 30 days', size: '789', type: 'manual' },
  { name: 'Seasonal Shoppers - Summer', desc: 'Customers who primarily shop during summer months based on historical data', size: '2,345', type: 'manual' },
]

export function Segments() {
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
            {aiSegments.map((s, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 0', borderBottom: i < aiSegments.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                <div>
                  <h4 style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>{s.name}</h4>
                  <p style={{ fontSize: 13, color: '#64748b' }}>{s.desc}</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Badge variant="secondary" style={{ fontSize: 13, padding: '4px 12px' }}>{s.size} customers</Badge>
                  <Button size="sm" variant="outline">Use</Button>
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
            {manualSegments.map((s, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 0', borderBottom: i < manualSegments.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                <div>
                  <h4 style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>{s.name}</h4>
                  <p style={{ fontSize: 13, color: '#64748b' }}>{s.desc}</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Badge variant="secondary" style={{ fontSize: 13, padding: '4px 12px' }}>{s.size} customers</Badge>
                  <Button size="sm" variant="outline">Edit</Button>
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
            <div className="xeno-condition-logic">
              <button className="xeno-filter-chip active">AND</button>
              <button className="xeno-filter-chip">OR</button>
            </div>
            <div className="xeno-segment-conditions">
              <div className="xeno-condition-row">
                <select className="xeno-filter-chip" style={{ background: 'white', border: '1px solid #e2e8f0', padding: '8px 12px', borderRadius: 6, fontSize: 13 }}>
                  <option>Last Purchase</option>
                  <option>Total Spend</option>
                  <option>Order Count</option>
                  <option>Category</option>
                </select>
                <select className="xeno-filter-chip" style={{ background: 'white', border: '1px solid #e2e8f0', padding: '8px 12px', borderRadius: 6, fontSize: 13 }}>
                  <option>Greater than</option>
                  <option>Less than</option>
                  <option>Equals</option>
                  <option>Between</option>
                </select>
                <input type="text" placeholder="Value" style={{ border: '1px solid #e2e8f0', padding: '8px 12px', borderRadius: 6, fontSize: 13, outline: 'none', width: 120 }} />
                <button style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer', fontSize: 18 }}>×</button>
              </div>
              <Button size="sm" variant="outline" style={{ marginTop: 8 }}>+ Add Condition</Button>
            </div>
            <div className="xeno-segment-preview" style={{ marginTop: 20, padding: 16, background: '#f0fdfa', borderRadius: 8, border: '1px solid #ccfbf1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <strong style={{ fontSize: 14 }}>Segment Preview</strong>
                <Badge style={{ background: '#14b8a6', color: 'white' }}>~1,245 customers</Badge>
              </div>
              <p style={{ fontSize: 13, color: '#475569' }}>Conditions: Last Purchase greater than 30 days ago</p>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
