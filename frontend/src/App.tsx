import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Today } from './pages/Today';
import { Dashboard } from './pages/Dashboard';
import { ChatPage } from './pages/ChatPage';
import { DealDetail } from './pages/DealDetail';
import { DocumentsContracts } from './pages/DocumentsContracts';
import { DailyDigest } from './pages/DailyDigest';
import { AgentHub } from './pages/AgentHub';
import { AdminGovernance } from './pages/AdminGovernance';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/today" element={<Today />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/deals/:id" element={<DealDetail />} />
          <Route path="/documents" element={<DocumentsContracts />} />
          <Route path="/daily-digest" element={<DailyDigest />} />
          <Route path="/agent-hub" element={<AgentHub />} />
          <Route path="/admin" element={<AdminGovernance />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
