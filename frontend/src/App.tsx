import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { ConfigurePage } from './pages/ConfigurePage';
import { LiveInterviewPage } from './pages/LiveInterviewPage';
import { ResultsPage } from './pages/ResultsPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';

function AppLayout({
  darkMode,
  setDarkMode,
  activeSessionId,
  setActiveSessionId,
}: {
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
  activeSessionId: string | null;
  setActiveSessionId: (val: string | null) => void;
}) {
  const location = useLocation();
  const isLanding = location.pathname === '/';

  return (
    <div className={`min-h-screen flex flex-col ${darkMode ? 'dark bg-navy-900 text-slate-100' : 'bg-slate-50 text-slate-900'}`}>
      <Navbar darkMode={darkMode} setDarkMode={setDarkMode} />

      <div className="flex-1 flex w-full">
        {!isLanding && <Sidebar activeSessionId={activeSessionId} />}

        <main className={`flex-1 overflow-y-auto ${isLanding ? 'w-full' : 'p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto'}`}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route
              path="/configure"
              element={<ConfigurePage onSessionCreated={(sid) => setActiveSessionId(sid)} />}
            />
            <Route path="/interview/:sessionId" element={<LiveInterviewPage />} />
            <Route path="/results/:sessionId" element={<ResultsPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/settings" element={<SettingsPage darkMode={darkMode} setDarkMode={setDarkMode} />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export function App() {
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const saved = localStorage.getItem('interviewiq_theme');
    return saved !== null ? saved === 'dark' : true;
  });

  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('interviewiq_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('interviewiq_theme', 'light');
    }
  }, [darkMode]);

  return (
    <BrowserRouter>
      <AppLayout
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        activeSessionId={activeSessionId}
        setActiveSessionId={setActiveSessionId}
      />
    </BrowserRouter>
  );
}

export default App;
