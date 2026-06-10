import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '@/store'
import { Loader2, Eye, EyeOff, UserPlus, LogIn } from 'lucide-react'

const API_BASE = 'https://xeno-api-worker.akshrivastav648.workers.dev/api/v1'

export function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState('')
  const navigate = useNavigate()
  const setToken = useAppStore((s) => s.setToken)

  const switchMode = (newMode: 'login' | 'register') => {
    setMode(newMode)
    setError('')
    setSuccess('')
  }

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || 'Invalid credentials.')
      }
      const data = await res.json()
      setToken(data.access_token)
      navigate('/')
    } catch (e: any) {
      setError(e.message || 'Login failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!username.trim() || !password.trim()) {
      setError('Please fill in all fields.')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || 'Registration failed.')
      }
      setSuccess('Account created successfully! You can now sign in.')
      switchMode('login')
      setPassword('')
      setConfirmPassword('')
    } catch (e: any) {
      setError(e.message || 'Registration failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="xeno-login-page">
      <div className="xeno-login-card">
        <div className="xeno-login-header">
          <div className="xeno-login-logo">
            <div className="xeno-login-logo-icon">X</div>
            Xeno AI
          </div>
          <p className="xeno-login-tagline">Campaign Intelligence Platform</p>
        </div>

        <div className="xeno-login-tabs">
          <button
            className={`xeno-login-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => switchMode('login')}
          >
            <LogIn size={16} /> Sign In
          </button>
          <button
            className={`xeno-login-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => switchMode('register')}
          >
            <UserPlus size={16} /> Create Account
          </button>
        </div>

        <form
          className="xeno-login-form"
          onSubmit={(e) => {
            e.preventDefault()
            mode === 'login' ? handleLogin() : handleRegister()
          }}
        >
          <div className="xeno-login-field">
            <label>Username</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              autoFocus
              autoComplete="username"
            />
          </div>

          <div className="xeno-login-field">
            <label>Password</label>
            <div className="xeno-login-password-wrap">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
              <button
                type="button"
                className="xeno-login-password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {mode === 'register' && (
            <div className="xeno-login-field">
              <label>Confirm Password</label>
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm your password"
                autoComplete="new-password"
              />
            </div>
          )}

          {error && <div className="xeno-login-error">{error}</div>}
          {success && <div className="xeno-login-success">{success}</div>}

          <button className="xeno-login-submit" type="submit" disabled={loading}>
            {loading ? (
              <><Loader2 size={16} className="animate-spin" /> Processing...</>
            ) : mode === 'login' ? (
              <><LogIn size={16} /> Sign In</>
            ) : (
              <><UserPlus size={16} /> Create Account</>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
