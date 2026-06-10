import { useAppStore } from "@/store"

declare const __API_URL__: string

const BASE = `${__API_URL__}/api/v1`

function authHeaders(): Record<string, string> {
  const t = useAppStore.getState().token
  return t ? { Authorization: `Bearer ${t}` } : {}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...options.headers },
  })
  if (res.status === 401) {
    // Stale or missing token — drop session and bounce to login.
    useAppStore.getState().logout()
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login"
    }
    throw new Error("Session expired")
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export async function login(username: string): Promise<{ access_token: string; role: string }> {
  const res = await request<{ access_token: string; role: string }>("/auth/login", {
    method: "POST", body: JSON.stringify({ username, password: "" }),
  })
  useAppStore.getState().setToken(res.access_token)
  return res
}

export async function getDashboardStats(): Promise<{
  total_customers: number; active_campaigns: number; total_sent: number;
  total_revenue: number; avg_open_rate: number; avg_ctr: number;
  avg_conversion_rate: number; channel_breakdown: any[]; recent_campaigns: any[]
}> {
  return request("/dashboard/stats")
}

export async function listCustomers(params?: {
  page?: number; page_size?: number; search?: string;
  lifecycle_stage?: string; sort_by?: string; sort_desc?: boolean
}): Promise<{ customers: any[]; total: number; page: number; page_size: number }> {
  const q = new URLSearchParams()
  if (params?.page) q.set("page", String(params.page))
  if (params?.page_size) q.set("page_size", String(params.page_size))
  if (params?.search) q.set("search", params.search)
  if (params?.lifecycle_stage) q.set("lifecycle_stage", params.lifecycle_stage)
  if (params?.sort_by) q.set("sort_by", params.sort_by)
  if (params?.sort_desc !== undefined) q.set("sort_desc", String(params.sort_desc))
  const s = q.toString()
  return request(`/customers${s ? `?${s}` : ""}`)
}

export async function getCustomer(id: string): Promise<any> {
  return request(`/customers/${id}`)
}

export async function getCustomerOrders(id: string, page = 1, pageSize = 20): Promise<any> {
  return request(`/customers/${id}/orders?page=${page}&page_size=${pageSize}`)
}

export async function getLifecycleDistribution(): Promise<any> {
  return request("/customers/lifecycle/distribution")
}

export async function listSegments(page = 1, pageSize = 20): Promise<{ segments: any[]; total: number; page: number; page_size: number }> {
  return request(`/segments?page=${page}&page_size=${pageSize}`)
}

export async function createSegment(data: { name: string; description?: string; criteria?: any }): Promise<any> {
  return request("/segments", { method: "POST", body: JSON.stringify(data) })
}

export async function snapshotSegment(id: string): Promise<any> {
  return request(`/segments/${id}/snapshot`, { method: "POST" })
}

export async function listCampaigns(params?: {
  page?: number; page_size?: number; status?: string; channel?: string
}): Promise<{ campaigns: any[]; total: number; page: number; page_size: number }> {
  const q = new URLSearchParams()
  if (params?.page) q.set("page", String(params.page))
  if (params?.page_size) q.set("page_size", String(params.page_size))
  if (params?.status) q.set("status", params.status)
  if (params?.channel) q.set("channel", params.channel)
  const s = q.toString()
  return request(`/campaigns${s ? `?${s}` : ""}`)
}

export async function getCampaign(id: string): Promise<any> {
  return request(`/campaigns/${id}`)
}

export async function createCampaign(data: any): Promise<any> {
  return request("/campaigns", { method: "POST", body: JSON.stringify(data) })
}

export async function launchCampaign(id: string): Promise<any> {
  return request(`/campaigns/${id}/launch`, { method: "POST" })
}

export async function getCampaignPerformance(id: string): Promise<any> {
  return request(`/campaigns/${id}/performance`)
}

export async function getChannelAnalytics(channel?: string): Promise<any[]> {
  return request(`/analytics/channels${channel ? `?channel=${channel}` : ""}`)
}

export async function generateCampaign(goal: string): Promise<any> {
  return request("/agents/generate-campaign", { method: "POST", body: JSON.stringify({ goal }) })
}

export async function discoverOpportunities(): Promise<any> {
  return request("/agents/discover-opportunities", { method: "POST" })
}

export async function listOpportunities(params?: {
  status?: string; page?: number; page_size?: number
}): Promise<{ opportunities: any[]; total: number; page: number; page_size: number }> {
  const q = new URLSearchParams()
  if (params?.status) q.set("status", params.status)
  if (params?.page) q.set("page", String(params.page))
  if (params?.page_size) q.set("page_size", String(params.page_size))
  const s = q.toString()
  return request(`/opportunities${s ? `?${s}` : ""}`)
}

export async function listApprovals(params?: {
  status?: string; page?: number; page_size?: number
}): Promise<any> {
  const q = new URLSearchParams()
  if (params?.status) q.set("status", params.status)
  if (params?.page) q.set("page", String(params.page))
  if (params?.page_size) q.set("page_size", String(params.page_size))
  const s = q.toString()
  return request(`/approvals${s ? `?${s}` : ""}`)
}

export async function respondToApproval(id: string, action: string): Promise<any> {
  return request(`/approvals/${id}/respond`, { method: "POST", body: JSON.stringify({ action }) })
}

export async function getPipelineStatus(): Promise<any> {
  return request("/pipeline/status")
}

export async function listProposals(): Promise<any[]> {
  return request("/proposals")
}

export async function triggerScheduler(jobType: string): Promise<any> {
  return request(`/scheduler/trigger/${jobType}`, { method: "POST" })
}

export async function listABTests(params?: {
  page?: number; page_size?: number; status?: string
}): Promise<{ ab_tests: any[]; total: number; page: number; page_size: number }> {
  const q = new URLSearchParams()
  if (params?.page) q.set("page", String(params.page))
  if (params?.page_size) q.set("page_size", String(params.page_size))
  if (params?.status) q.set("status", params.status)
  const s = q.toString()
  return request(`/ab-tests${s ? `?${s}` : ""}`)
}

export async function getABTest(id: string): Promise<any> {
  return request(`/ab-tests/${id}`)
}

export async function createABTest(data: {
  name: string; campaign_id: string; hypothesis?: string;
  audience_split?: any; success_metric?: string; min_confidence?: number
}): Promise<any> {
  return request("/ab-tests", { method: "POST", body: JSON.stringify(data) })
}

export async function commandCentreQuery(query: string): Promise<{
  response: string; reasoning?: string; confidence_score?: number;
  supporting_data?: any; predicted_outcome?: any; agent_trace?: any[]
}> {
  return request("/agents/command-centre", { method: "POST", body: JSON.stringify({ query }) })
}

export interface CommandCentreMessage {
  role: "user" | "assistant"
  text: string
  ts: number
}

export async function getCommandCentreHistory(): Promise<{ history: CommandCentreMessage[] }> {
  return request("/command-centre/history")
}

export async function commandCentreChat(
  query: string,
  conversation_history?: { role: "user" | "assistant"; text: string; ts: number }[]
): Promise<{
  response: string; reasoning?: string; confidence_score?: number;
  supporting_data?: any; predicted_outcome?: any; agent_trace?: any[]
}> {
  return request("/command-centre/chat", {
    method: "POST",
    body: JSON.stringify({ query, conversation_history: conversation_history || [] }),
  })
}

export async function clearCommandCentreHistory(): Promise<{ status: string }> {
  return request("/command-centre/history", { method: "DELETE" })
}

export async function listProducts(params?: {
  page?: number; page_size?: number; category?: string
}): Promise<{ products: any[]; total: number; page: number; page_size: number }> {
  const q = new URLSearchParams()
  if (params?.page) q.set("page", String(params.page))
  if (params?.page_size) q.set("page_size", String(params.page_size))
  if (params?.category) q.set("category", params.category)
  const s = q.toString()
  return request(`/products${s ? `?${s}` : ""}`)
}
