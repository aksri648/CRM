import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'

export function Settings() {
  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Settings</h1>
          <p className="xeno-header-subtitle">Configure your platform preferences</p>
        </div>
      </div>

      <div className="xeno-card">
        <div className="xeno-card-header">
          <h2 className="xeno-card-title">General</h2>
        </div>
        <div style={{ display: 'grid', gap: 20 }}>
          <div>
            <Label>Platform Name</Label>
            <Input defaultValue="Xeno AI Campaign Studio" style={{ marginTop: 4, maxWidth: 400 }} />
          </div>
          <div>
            <Label>Default Timezone</Label>
            <select className="xeno-filter-chip" style={{ background: 'white', border: '1px solid #e2e8f0', padding: '10px 14px', borderRadius: 8, fontSize: 14, marginTop: 4, maxWidth: 400, width: '100%' }}>
              <option>Asia/Kolkata (IST, UTC +5:30)</option>
              <option>America/New_York (EST, UTC -5:00)</option>
              <option>Europe/London (GMT, UTC +0:00)</option>
            </select>
          </div>
          <div>
            <Label>Default Currency</Label>
            <select className="xeno-filter-chip" style={{ background: 'white', border: '1px solid #e2e8f0', padding: '10px 14px', borderRadius: 8, fontSize: 14, marginTop: 4, maxWidth: 400, width: '100%' }}>
              <option>INR (₹)</option>
              <option>USD ($)</option>
              <option>EUR (€)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="xeno-card">
        <div className="xeno-card-header">
          <h2 className="xeno-card-title">Notifications</h2>
        </div>
        <div style={{ display: 'grid', gap: 16 }}>
          {[
            { label: 'Telegram Bot Notifications', desc: 'Receive proposal alerts via Telegram' },
            { label: 'Campaign Completion Alerts', desc: 'Notify when campaigns finish sending' },
            { label: 'AI Opportunity Alerts', desc: 'Get notified when new opportunities are discovered' },
            { label: 'Weekly Digest Email', desc: 'Receive a weekly performance summary' },
          ].map((n, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: i < 3 ? '1px solid #f1f5f9' : 'none' }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 500 }}>{n.label}</div>
                <div style={{ fontSize: 12, color: '#64748b' }}>{n.desc}</div>
              </div>
              <Switch defaultChecked={i < 3} />
            </div>
          ))}
        </div>
      </div>

      <div className="xeno-card">
        <div className="xeno-card-header">
          <h2 className="xeno-card-title">AI Configuration</h2>
        </div>
        <div style={{ display: 'grid', gap: 20 }}>
          <div>
            <Label>AI Model</Label>
            <select className="xeno-filter-chip" style={{ background: 'white', border: '1px solid #e2e8f0', padding: '10px 14px', borderRadius: 8, fontSize: 14, marginTop: 4, maxWidth: 400, width: '100%' }}>
              <option>GPT-5 (Default)</option>
              <option>GPT-4 Turbo</option>
              <option>Claude 4</option>
            </select>
          </div>
          <div>
            <Label>Autonomous Scanning Schedule</Label>
            <select className="xeno-filter-chip" style={{ background: 'white', border: '1px solid #e2e8f0', padding: '10px 14px', borderRadius: 8, fontSize: 14, marginTop: 4, maxWidth: 400, width: '100%' }}>
              <option>Daily at 6:00 AM</option>
              <option>Every 12 hours</option>
              <option>Weekly on Monday</option>
              <option>Manual only</option>
            </select>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0' }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 500 }}>Auto-approve Low Risk Proposals</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>Auto-approve proposals with confidence score {'>'} 95%</div>
            </div>
            <Switch />
          </div>
        </div>
      </div>

      <div className="xeno-card">
        <div className="xeno-card-header">
          <h2 className="xeno-card-title">Telegram Bot</h2>
        </div>
        <div style={{ display: 'grid', gap: 20 }}>
          <div>
            <Label>Bot Token</Label>
            <Input type="password" defaultValue="••••••••••••••••" style={{ marginTop: 4, maxWidth: 400 }} />
          </div>
          <div>
            <Label>Chat ID</Label>
            <Input defaultValue="-1001234567890" style={{ marginTop: 4, maxWidth: 400 }} />
          </div>
          <div>
            <Button size="sm" variant="outline">Test Connection</Button>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
        <Button variant="outline">Cancel</Button>
        <Button style={{ background: '#14b8a6' }}>Save Changes</Button>
      </div>
    </div>
  )
}
