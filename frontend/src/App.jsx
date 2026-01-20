import { BrowserRouter, Routes, Route } from 'react-router-dom'
import IssueList from './components/IssueList'
import Player from './components/Player'
import Settings from './components/Settings'
import InstallPrompt from './components/InstallPrompt'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <InstallPrompt />
        <Routes>
          <Route path="/" element={<IssueList />} />
          <Route path="/player/:issueId" element={<Player />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
