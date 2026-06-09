import { useState } from 'react'
import { useAuth, SignIn } from '@clerk/clerk-react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAppStore } from '@/store'

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || ''

function ClerkLogin() {
  const { isSignedIn, isLoaded } = useAuth()

  if (!isLoaded) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#0f172a', color: '#94a3b8' }}>
        Loading...
      </div>
    )
  }

  if (isSignedIn) {
    return <Navigate to="/" replace />
  }

  return <LoginShell><SignIn routing="hash" /></LoginShell>
}

function DevLogin() {
  const [username, setUsername] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const setToken = useAppStore((s) => s.setToken)

  const handleLogin = async () => {
    if (!username.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await fetch('https://xeno-api-worker.akshrivastav648.workers.dev/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password: '' }),
      })
      if (!res.ok) throw new Error('Login failed')
      const data = await res.json()
      setToken(data.access_token)
      navigate('/')
    } catch (e: any) {
      setError(e.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <LoginShell>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
          placeholder="Username"
          style={{
            padding: '12px 16px', borderRadius: 8, border: '1px solid #334155',
            background: '#0f172a', color: 'white', fontSize: 14, outline: 'none',
          }}
        />
        {error && <div style={{ color: '#ef4444', fontSize: 13 }}>{error}</div>}
        <button
          onClick={handleLogin}
          disabled={loading}
          style={{
            padding: '12px', borderRadius: 8, border: 'none',
            background: loading ? '#0d9488' : '#14b8a6', color: 'white',
            fontSize: 14, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </div>
    </LoginShell>
  )
}

function LoginShell({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      minHeight: '100vh', background: '#0f172a',
    }}>
      <div style={{
        background: '#1e293b', borderRadius: 16, padding: 40,
        width: '100%', maxWidth: 440, border: '1px solid #334155',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 36, fontWeight: 700, color: '#14b8a6', marginBottom: 4 }}>
            Xeno AI
          </div>
          <div style={{ color: '#64748b', fontSize: 14 }}>
            Campaign Intelligence Platform
          </div>
        </div>
        {children}
      </div>
    </div>
  )
}

export function LoginPage() {
  return CLERK_KEY ? <ClerkLogin /> : <DevLogin />
}
