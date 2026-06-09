import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Toaster } from '@/components/ui/toaster'

export function AppLayout() {
  return (
    <div className="xeno-layout">
      <Sidebar />
      <main className="xeno-main">
        <div className="xeno-page-content">
          <Outlet />
        </div>
      </main>
      <Toaster />
    </div>
  )
}
