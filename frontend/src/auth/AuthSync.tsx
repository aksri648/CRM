import { useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { useAppStore } from '@/store'

export function AuthSync() {
  const { isSignedIn, getToken } = useAuth()
  const setToken = useAppStore((s) => s.setToken)

  useEffect(() => {
    let cancelled = false
    if (isSignedIn) {
      getToken().then((t) => { if (!cancelled && t) setToken(t) })
    }
    return () => { cancelled = true }
  }, [isSignedIn, getToken, setToken])

  return null
}
