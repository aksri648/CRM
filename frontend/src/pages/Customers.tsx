import { useState, useEffect } from 'react'
import { Search } from 'lucide-react'
import { listCustomers } from '@/lib/api'

const CHIP_KEYS = ['All', 'Active', 'VIP', 'At Risk', 'New']

const STAGE_PARAM: Record<string, string | undefined> = {
  All: undefined,
  Active: 'active',
  VIP: 'vip',
  'At Risk': 'at_risk',
  New: 'new',
}

const GRADIENTS = [
  'linear-gradient(135deg, #14b8a6, #0d9488)',
  'linear-gradient(135deg, #f093fb, #f5576c)',
  'linear-gradient(135deg, #4facfe, #00f2fe)',
  'linear-gradient(135deg, #a8edea, #fed6e3)',
  'linear-gradient(135deg, #ffecd2, #fcb69f)',
  'linear-gradient(135deg, #89f7fe, #66a6ff)',
  'linear-gradient(135deg, #fddb92, #d1fdff)',
  'linear-gradient(135deg, #a1c4fd, #c2e9fb)',
  'linear-gradient(135deg, #d4fc79, #96e6a1)',
]

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function pickGradient(name: string): string {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return GRADIENTS[Math.abs(hash) % GRADIENTS.length]
}

function formatCurrency(val: number): string {
  return '$' + val.toLocaleString('en-US')
}

function displayDays(days: number): string {
  if (days === 0) return 'Today'
  if (days === 1) return '1d'
  if (days < 30) return `${days}d`
  const months = Math.floor(days / 30)
  if (months === 1) return '1mo'
  if (months < 12) return `${months}mo`
  return `${Math.floor(months / 12)}y`
}

function relativeDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  const t = new Date(dateStr).getTime()
  if (isNaN(t)) return '—'
  const diff = Date.now() - t
  const days = Math.floor(diff / 86400000)
  if (days === 0) return 'Today'
  if (days === 1) return '1d'
  if (days < 30) return `${days}d`
  const months = Math.floor(days / 30)
  if (months === 1) return '1mo'
  if (months < 12) return `${months}mo`
  return `${Math.floor(months / 12)}y`
}

export function Customers() {
  const [customers, setCustomers] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [activeChip, setActiveChip] = useState('All')

  const fetchData = async (opts: { search?: string; lifecycle_stage?: string }) => {
    setLoading(true)
    setError('')
    try {
      const data = await listCustomers({
        search: opts.search || undefined,
        lifecycle_stage: opts.lifecycle_stage || undefined,
      })
      setCustomers(Array.isArray(data?.customers) ? data.customers : [])
      setTotal(typeof data?.total === 'number' ? data.total : 0)
    } catch (e: any) {
      setError(e.message || 'Failed to load customers')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchData({ search, lifecycle_stage: STAGE_PARAM[activeChip] })
    }, 300)
    return () => clearTimeout(timer)
  }, [search, activeChip])

  const handleChipClick = (chip: string) => {
    setActiveChip(chip)
    setSearch('')
  }

  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Customers</h1>
          <p className="xeno-header-subtitle">{total.toLocaleString()} total customers</p>
        </div>
      </div>

      <div className="xeno-search-bar">
        <div className="xeno-search-box">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search by name, email, phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="xeno-filter-chips">
          {CHIP_KEYS.map((f) => (
            <button
              key={f}
              className={`xeno-filter-chip ${f === activeChip ? 'active' : ''}`}
              onClick={() => handleChipClick(f)}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="xeno-loading">Loading customers...</div>}
      {error && <div className="xeno-error">{error}</div>}
      {!loading && !error && (
        <div className="xeno-customer-grid">
          {customers.map((c) => {
            const customerName = c.name || `${c.first_name || ''} ${c.last_name || ''}`.trim() || 'Unknown'
            const ltv = c.ltv ?? c.total_spent ?? 0
            const orders = c.order_count ?? c.orders ?? c.total_orders ?? 0
            const lastOrder = c.last_order_date ? relativeDate(c.last_order_date) : (c.days_since_last_order != null ? displayDays(c.days_since_last_order) : '—')
            return (
            <div key={c.id} className="xeno-customer-card">
              <div className="xeno-customer-card-header">
                <div
                  className="xeno-customer-avatar"
                  style={
                    c.avatar
                      ? { background: `url(${c.avatar})`, backgroundSize: 'cover' }
                      : { background: pickGradient(customerName) }
                  }
                >
                  {!c.avatar && getInitials(customerName)}
                </div>
                <div className="xeno-customer-info">
                  <h4>{customerName}</h4>
                  <p>{c.email}</p>
                </div>
              </div>
              <div className="xeno-customer-stats">
                <div className="xeno-customer-stat">
                  <div className="xeno-customer-stat-value">{formatCurrency(ltv)}</div>
                  <div className="xeno-customer-stat-label">LTV</div>
                </div>
                <div className="xeno-customer-stat">
                  <div className="xeno-customer-stat-value">{orders}</div>
                  <div className="xeno-customer-stat-label">Orders</div>
                </div>
                <div className="xeno-customer-stat">
                  <div className="xeno-customer-stat-value">{lastOrder}</div>
                  <div className="xeno-customer-stat-label">Last Order</div>
                </div>
              </div>
            </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
