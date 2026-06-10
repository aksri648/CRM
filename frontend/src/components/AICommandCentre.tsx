import { useState, useEffect, useRef } from 'react'
import { X, Send, Bot, Loader2, Activity, Cpu, Bell } from 'lucide-react'
import { getPipelineStatus, listProposals, commandCentreQuery } from '@/lib/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export function AICommandCentre({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello, I am the Xeno AI Command Centre. I can help you monitor system activity, generate campaigns, discover opportunities, or answer questions about your CRM. How can I assist you?',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [pipelineStatus, setPipelineStatus] = useState<any>(null)
  const [proposals, setProposals] = useState<any[]>([])
  const [statusLoading, setStatusLoading] = useState(true)
  const chatEnd = useRef<HTMLDivElement>(null)

  const fetchStatus = async () => {
    setStatusLoading(true)
    try {
      const [ps, pr] = await Promise.all([
        getPipelineStatus().catch(() => null),
        listProposals().catch(() => []),
      ])
      setPipelineStatus(ps)
      setProposals(pr)
    } catch { /* ignore */ }
    setStatusLoading(false)
  }

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 15000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || sending) return
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setSending(true)

    try {
      const result = await commandCentreQuery(userMsg.content)
      setMessages((m) => [...m, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: result.response || 'I could not process that query.',
        timestamp: new Date(),
      }])
    } catch {
      setMessages((m) => [...m, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      }])
    }
    setSending(false)
  }

  const activeRuns = proposals.filter((p) => p.status === 'running' || p.status === 'pending')

  return (
    <div className="xeno-cc-overlay">
      <div className="xeno-cc-backdrop" onClick={onClose} />
      <div className="xeno-cc-panel">
        <div className="xeno-cc-header">
          <div className="xeno-cc-header-left">
            <div className="xeno-cc-header-icon">
              <Bot size={20} />
            </div>
            <div>
              <div className="xeno-cc-title">AI Command Centre</div>
              <div className="xeno-cc-subtitle">System overview & assistant</div>
            </div>
          </div>
          <button className="xeno-cc-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="xeno-cc-status">
          <div className="xeno-cc-status-header">
            <Activity size={14} />
            <span>System Status</span>
            {statusLoading && <Loader2 size={12} className="animate-spin" style={{ marginLeft: 'auto' }} />}
          </div>
          {!statusLoading && (
            <div className="xeno-cc-status-grid">
              <div className="xeno-cc-stat">
                <Cpu size={14} />
                <div>
                  <div className="xeno-cc-stat-label">Worker</div>
                  <div className="xeno-cc-stat-value">{pipelineStatus?.worker_status || 'unknown'}</div>
                </div>
              </div>
              <div className="xeno-cc-stat">
                <Activity size={14} />
                <div>
                  <div className="xeno-cc-stat-label">Queue</div>
                  <div className="xeno-cc-stat-value">{pipelineStatus?.queue_depth ?? '—'}</div>
                </div>
              </div>
              <div className="xeno-cc-stat">
                <Bell size={14} />
                <div>
                  <div className="xeno-cc-stat-label">Active Runs</div>
                  <div className="xeno-cc-stat-value">{activeRuns.length}</div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="xeno-cc-chat">
          {messages.map((msg) => (
            <div key={msg.id} className={`xeno-cc-message ${msg.role === 'user' ? 'xeno-cc-message-user' : 'xeno-cc-message-assistant'}`}>
              <div className="xeno-cc-message-content">{msg.content}</div>
              <div className="xeno-cc-message-time">{msg.timestamp.toLocaleTimeString()}</div>
            </div>
          ))}
          {sending && (
            <div className="xeno-cc-message xeno-cc-message-assistant">
              <div className="xeno-cc-message-content" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Loader2 size={14} className="animate-spin" /> Thinking...
              </div>
            </div>
          )}
          <div ref={chatEnd} />
        </div>

        <div className="xeno-cc-input-bar">
          <input
            className="xeno-cc-input"
            placeholder="Ask about system status, campaigns, or customers..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={sending}
          />
          <button className="xeno-cc-send" onClick={handleSend} disabled={!input.trim() || sending}>
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
