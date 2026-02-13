import { Routes, Route, Navigate } from 'react-router-dom'

// Pages — to be implemented by L9 worker
// import Home from './pages/Home'
// import Scan from './pages/Scan'
// import Send from './pages/Send'
// import History from './pages/History'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Routes>
        <Route path="/" element={<PlaceholderHome />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

function PlaceholderHome() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">SOMS Wallet</h1>
        <p className="text-gray-400">Mobile wallet app — scaffold ready</p>
      </div>
    </div>
  )
}
