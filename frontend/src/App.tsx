import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import WorkflowDetail from './pages/WorkflowDetail'
import Analysis from './pages/Analysis'
import Chat from './pages/Chat'
import KnowledgeBase from './pages/KnowledgeBase'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/sessions/:id" element={<WorkflowDetail />} />
        <Route path="/sessions/:id/analysis" element={<Analysis />} />
        <Route path="/sessions/:id/chat" element={<Chat />} />
        <Route path="/kb" element={<KnowledgeBase />} />
      </Routes>
    </BrowserRouter>
  )
}
