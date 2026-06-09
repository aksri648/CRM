import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ClerkProvider } from '@clerk/clerk-react'
import './index.css'
import App from './App'

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || ''
const queryClient = new QueryClient()

function Root() {
  if (!CLERK_KEY) {
    return (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App clerkReady={false} />
        </BrowserRouter>
      </QueryClientProvider>
    )
  }
  return (
    <ClerkProvider publishableKey={CLERK_KEY} afterSignOutUrl="/login">
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
