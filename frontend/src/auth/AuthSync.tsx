import { useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { useAppStore } from '@/store'

export function AuthSync() {
  const { isSignedIn, getToken } = useAuth()
  const setToken = useAppStore((s) => s.setToken)

  useEffect(() => {
    if (isSignedIn) {
      getToken().then((t) => { if (t) setToken(t) })
    } else {
      setToken(null)
    }
  }, [isSignedIn, getToken, setToken])

  return null
}
