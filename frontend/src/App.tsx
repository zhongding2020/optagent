import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import WorkflowDetail from './pages/WorkflowDetail'
import Analysis from './pages/Analysis'
import Chat from './pages/Chat'
import KnowledgeBase from './pages/KnowledgeBase'

function Layout() {
  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/sessions/:id" element={<WorkflowDetail />} />
          <Route path="/sessions/:id/analysis" element={<Analysis />} />
          <Route path="/sessions/:id/chat" element={<Chat />} />
          <Route path="/kb" element={<KnowledgeBase />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
