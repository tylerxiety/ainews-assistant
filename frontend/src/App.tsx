import { BrowserRouter, Routes, Route } from 'react-router-dom'
import IssueList from './components/IssueList'
import Player from './components/Player'
import Settings from './components/Settings'
import InstallPrompt from './components/InstallPrompt'
import ErrorBoundary from './components/ErrorBoundary'
import { LanguageProvider } from './i18n'
import './App.css'

function App() {
  return (
    <LanguageProvider>
      <BrowserRouter>
        <div className="app">
          <ErrorBoundary>
            <InstallPrompt />
            <Routes>
              <Route path="/" element={<IssueList />} />
              <Route path="/player/:issueId" element={<Player />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </ErrorBoundary>
        </div>
      </BrowserRouter>
    </LanguageProvider>
  )
}

export default App
