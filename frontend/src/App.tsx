import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Dashboard } from './pages/Dashboard';
import { DealDetail } from './pages/DealDetail';
import { DocumentsContracts } from './pages/DocumentsContracts';
import { AgentHub } from './pages/AgentHub';
import { AdminGovernance } from './pages/AdminGovernance';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/deals/:id" element={<DealDetail />} />
          <Route path="/documents" element={<DocumentsContracts />} />
          <Route path="/agent-hub" element={<AgentHub />} />
          <Route path="/admin" element={<AdminGovernance />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
