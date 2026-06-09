import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { Dashboard } from '@/pages/Dashboard'
import { AICampaignStudio } from '@/pages/AICampaignStudio'
import { Opportunities } from '@/pages/Opportunities'
import { Customers } from '@/pages/Customers'
import { Segments } from '@/pages/Segments'
import { Campaigns } from '@/pages/Campaigns'
import { ABTests } from '@/pages/ABTests'
import { Analytics } from '@/pages/Analytics'
import { PipelineMonitor } from '@/pages/PipelineMonitor'
import { AgentProposals } from '@/pages/AgentProposals'
import { Settings } from '@/pages/Settings'
import './app.css'

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/ai-studio" element={<AICampaignStudio />} />
        <Route path="/opportunities" element={<Opportunities />} />
        <Route path="/customers" element={<Customers />} />
        <Route path="/segments" element={<Segments />} />
        <Route path="/campaigns" element={<Campaigns />} />
        <Route path="/ab-tests" element={<ABTests />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/pipeline" element={<PipelineMonitor />} />
        <Route path="/proposals" element={<AgentProposals />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
