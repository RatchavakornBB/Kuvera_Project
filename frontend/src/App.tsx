import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Dashboard } from './pages/Dashboard';
import { DealDetail } from './pages/DealDetail';
import { DocumentsContracts } from './pages/DocumentsContracts';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/deals/:id" element={<DealDetail />} />
          <Route path="/documents" element={<DocumentsContracts />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
