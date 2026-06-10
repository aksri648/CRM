import { StrictMode, useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ClerkProvider } from '@clerk/clerk-react'
import './index.css'
import App from './App'

const API_URL = import.meta.env.VITE_API_URL || 'https://xeno-api-worker.akshrivastav648.workers.dev'
const queryClient = new QueryClient()

function Root() {
  const [clerkKey, setClerkKey] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const envKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
    if (envKey) {
      setClerkKey(envKey)
      setLoading(false)
      return
    }
    fetch(`${API_URL}/api/v1/config`)
      .then((r) => r.json())
      .then((data) => setClerkKey(data.clerkPublishableKey || ''))
      .catch(() => setClerkKey(''))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#0f172a', color: '#64748b' }}>
        Loading...
      </div>
    )
  }

  if (!clerkKey) {
    return (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App clerkReady={false} />
        </BrowserRouter>
      </QueryClientProvider>
    )
  }

  return (
    <ClerkProvider publishableKey={clerkKey} afterSignOutUrl="/login">
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App clerkReady />
        </BrowserRouter>
      </QueryClientProvider>
    </ClerkProvider>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
)
