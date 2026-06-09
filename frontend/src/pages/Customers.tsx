import { Search } from 'lucide-react'

const customers = [
  { initials: 'JD', name: 'John Doe', email: 'john.doe@email.com', ltv: '$456', orders: 12, lastOrder: '5d', status: 'active', bg: 'linear-gradient(135deg, #14b8a6, #0d9488)' },
  { initials: 'JS', name: 'Jane Smith', email: 'jane.smith@email.com', ltv: '$789', orders: 18, lastOrder: '2d', status: 'vip', bg: 'linear-gradient(135deg, #f093fb, #f5576c)' },
  { initials: 'RJ', name: 'Robert Johnson', email: 'robert.j@email.com', ltv: '$234', orders: 6, lastOrder: '45d', status: 'at_risk', bg: 'linear-gradient(135deg, #4facfe, #00f2fe)' },
  { initials: 'EW', name: 'Emily Wilson', email: 'emily.w@email.com', ltv: '$1,234', orders: 24, lastOrder: '1d', status: 'vip', bg: 'linear-gradient(135deg, #a8edea, #fed6e3)' },
  { initials: 'MB', name: 'Michael Brown', email: 'michael.b@email.com', ltv: '$567', orders: 9, lastOrder: '12d', status: 'active', bg: 'linear-gradient(135deg, #ffecd2, #fcb69f)' },
  { initials: 'SD', name: 'Sarah Davis', email: 'sarah.d@email.com', ltv: '$890', orders: 15, lastOrder: '8d', status: 'active', bg: 'linear-gradient(135deg, #89f7fe, #66a6ff)' },
  { initials: 'DM', name: 'David Martinez', email: 'david.m@email.com', ltv: '$345', orders: 7, lastOrder: '30d', status: 'at_risk', bg: 'linear-gradient(135deg, #fddb92, #d1fdff)' },
  { initials: 'AL', name: 'Ashley Lee', email: 'ashley.l@email.com', ltv: '$1,567', orders: 32, lastOrder: '3d', status: 'vip', bg: 'linear-gradient(135deg, #a1c4fd, #c2e9fb)' },
  { initials: 'KT', name: 'Kevin Taylor', email: 'kevin.t@email.com', ltv: '$678', orders: 14, lastOrder: '7d', status: 'active', bg: 'linear-gradient(135deg, #d4fc79, #96e6a1)' },
]

export function Customers() {
  return (
    <div>
      <div className="xeno-header">
        <div>
          <h1>Customers</h1>
          <p className="xeno-header-subtitle">12,486 total customers</p>
        </div>
      </div>

      <div className="xeno-search-bar">
        <div className="xeno-search-box">
          <Search size={16} />
          <input type="text" placeholder="Search by name, email, phone..." />
        </div>
        <div className="xeno-filter-chips">
          {['All', 'Active', 'VIP', 'At Risk', 'New'].map((f, i) => (
            <button key={i} className={`xeno-filter-chip ${i === 0 ? 'active' : ''}`}>{f}</button>
          ))}
        </div>
      </div>

      <div className="xeno-customer-grid">
        {customers.map((c, i) => (
          <div key={i} className="xeno-customer-card">
            <div className="xeno-customer-card-header">
              <div className="xeno-customer-avatar" style={{ background: c.bg }}>{c.initials}</div>
              <div className="xeno-customer-info">
                <h4>{c.name}</h4>
                <p>{c.email}</p>
              </div>
            </div>
            <div className="xeno-customer-stats">
              <div className="xeno-customer-stat">
                <div className="xeno-customer-stat-value">{c.ltv}</div>
                <div className="xeno-customer-stat-label">LTV</div>
              </div>
              <div className="xeno-customer-stat">
                <div className="xeno-customer-stat-value">{c.orders}</div>
                <div className="xeno-customer-stat-label">Orders</div>
              </div>
              <div className="xeno-customer-stat">
                <div className="xeno-customer-stat-value">{c.lastOrder}</div>
                <div className="xeno-customer-stat-label">Last Order</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
