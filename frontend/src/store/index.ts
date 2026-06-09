import { create } from 'zustand'

export interface Customer {
  id: string
  name: string
  email: string
  phone: string
  ltv: number
  orders: number
  lastOrder: string
  status: 'active' | 'inactive' | 'vip' | 'at_risk' | 'new'
  preferredChannel: string
  churnRisk: number
  avatar: string
}

export interface Campaign {
  id: string
  name: string
  channel: 'whatsapp' | 'sms' | 'email' | 'rcs'
  segment: string
  status: 'draft' | 'sending' | 'sent' | 'delivered' | 'opened' | 'clicked' | 'converted' | 'failed'
  sent: number
  delivered: number
  opened: number
  clicked: number
  converted: number
  revenue: number
  openRate: number
  clickRate: number
  conversionRate: number
  createdAt: string
}

export interface Opportunity {
  id: string
  title: string
  description: string
  audience: number
  expectedRevenue: number
  expectedCTR: number
  reasoning: string
  type: 'at_risk' | 'trending' | 'cart_abandonment' | 'reengagement' | 'upsell'
  status: 'pending' | 'generated' | 'approved' | 'rejected'
}

export interface Segment {
  id: string
  name: string
  description: string
  size: number
  type: 'ai' | 'manual'
}

export interface AIProposal {
  id: string
  title: string
  description: string
  audience: number
  channel: string
  predictedOpenRate: number
  predictedCTR: number
  predictedRevenue: number
  reasoning: string
  confidenceScore: number
  status: 'pending' | 'approved' | 'rejected'
  createdAt: string
  variants: {
    name: string
    message: string
    type: string
  }[]
}

interface AppState {
  sidebarOpen: boolean
  currentPage: string
  toggleSidebar: () => void
  setCurrentPage: (page: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  currentPage: 'dashboard',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setCurrentPage: (page) => set({ currentPage: page }),
}))
