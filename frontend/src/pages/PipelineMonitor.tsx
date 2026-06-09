import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'

const pipelineStages = [
  { label: 'Campaign', value: '4 Active', icon: '🚀' },
  { label: 'Queue', value: '12 Pending', icon: '📤' },
  { label: 'Worker', value: '3 Processing', icon: '⚙️' },
  { label: 'Sent', value: '45,678', icon: '📨' },
  { label: 'Delivered', value: '44,170', icon: '✅' },
  { label: 'Opened', value: '27,562', icon: '👁️' },
  { label: 'Clicked', value: '8,832', icon: '🖱️' },
  { label: 'Converted', value: '1,855', icon: '💰' },
]

const events = [
  { time: '10:32:15 AM', event: 'Campaign Dispatched', detail: 'Summer Sale → WhatsApp Queue', type: 'info' },
  { time: '10:32:18 AM', event: 'Worker Picked', detail: 'worker-03 processing message batch', type: 'success' },
  { time: '10:32:22 AM', event: 'Message Sent', detail: '5,432 messages dispatched', type: 'success' },
  { time: '10:32:45 AM', event: 'Delivery Receipt', detail: '5,201 delivered (95.7%)', type: 'success' },
  { time: '10:33:12 AM', event: 'Open Event', detail: '247 opens recorded', type: 'warning' },
  { time: '10:33:30 AM', event: 'Click Event', detail: '89 clicks recorded', type: 'warning' },
  { time: '10:34:02 AM', event: 'Conversion', detail: '12 conversions recorded', type: 'purple' },
  { time: '10:34:15 AM', event: 'Failed Messages', detail: '23 messages failed - retry queued', type: 'error' },
]

export function PipelineMonitor() {
  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Pipeline Monitor</h1>
          <p className="xeno-header-subtitle">Real-time communication lifecycle visualization</p>
        </div>
        <div className="xeno-header-actions">
          <Button variant="outline" size="sm"><RefreshCw size={14} /> Refresh</Button>
        </div>
      </div>

      <div className="xeno-card">
        <div className="xeno-pipeline">
          {pipelineStages.map((stage, i) => (
            <>
              <div key={i} className="xeno-pipeline-stage">
                <div className="xeno-pipeline-icon" style={{
                  background: i === 7 ? '#dcfce7' : i >= 5 ? '#fef9c3' : i >= 3 ? '#dbeafe' : '#f1f5f9',
                  color: i === 7 ? '#15803d' : i >= 5 ? '#a16207' : i >= 3 ? '#1d4ed8' : '#475569'
                }}>
                  <span style={{ fontSize: 20 }}>{stage.icon}</span>
                </div>
                <div className="xeno-pipeline-label">{stage.label}</div>
                <div className="xeno-pipeline-value">{stage.value}</div>
              </div>
              {i < pipelineStages.length - 1 && <div className="xeno-pipeline-arrow" />}
            </>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div className="xeno-card">
          <div className="xeno-card-header">
            <h2 className="xeno-card-title">Event Timeline</h2>
          </div>
          <div className="xeno-timeline">
            {events.map((evt, i) => (
              <div key={i} className="xeno-timeline-item">
                <div className="xeno-timeline-date">{evt.time}</div>
                <div className="xeno-timeline-content">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong style={{ fontSize: 14 }}>{evt.event}</strong>
                      <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>{evt.detail}</div>
                    </div>
                    <span className={`xeno-badge xeno-badge-${evt.type === 'error' ? 'danger' : evt.type === 'success' ? 'success' : evt.type === 'purple' ? 'purple' : 'warning'}`}>
                      {evt.type === 'error' ? 'Failed' : evt.type === 'success' ? 'OK' : evt.type === 'purple' ? 'Conversion' : 'Event'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="xeno-card">
          <div className="xeno-card-header">
            <h2 className="xeno-card-title">Queue Depth</h2>
          </div>
          <div style={{ padding: 20, textAlign: 'center' }}>
            <div style={{ fontSize: 48, fontWeight: 700, color: '#14b8a6', marginBottom: 8 }}>12</div>
            <div style={{ fontSize: 14, color: '#64748b', marginBottom: 24 }}>Messages in Queue</div>
            <div style={{ display: 'flex', gap: 12 }}>
              {[
                { label: 'Processing', value: '3', color: '#3b82f6' },
                { label: 'Pending', value: '7', color: '#f59e0b' },
                { label: 'Retry', value: '2', color: '#ef4444' },
              ].map((q, i) => (
                <div key={i} style={{ flex: 1, padding: 16, background: '#f8fafc', borderRadius: 8 }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: q.color }}>{q.value}</div>
                  <div style={{ fontSize: 12, color: '#64748b' }}>{q.label}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ padding: 20, borderTop: '1px solid #f1f5f9', marginTop: 16 }}>
            <div className="xeno-card-header" style={{ marginBottom: 12 }}>
              <h2 className="xeno-card-title">Retry Stats</h2>
            </div>
            <div style={{ display: 'flex', gap: 16 }}>
              {[
                { label: 'Attempt 1', value: '98.2%', color: '#16a34a' },
                { label: 'Attempt 2', value: '1.5%', color: '#f59e0b' },
                { label: 'Attempt 3', value: '0.3%', color: '#ef4444' },
              ].map((r, i) => (
                <div key={i} style={{ flex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: r.color }}>{r.value}</div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>{r.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
