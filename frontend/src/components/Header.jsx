/* Header — app branding and backend status indicator */
import React, { useState, useEffect } from 'react'

export default function Header() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    const check = () => {
      fetch('/api/health')
        .then(r => r.ok ? r.json() : null)
        .then(setHealth)
        .catch(() => setHealth(null))
    }
    check()
    const interval = setInterval(check, 30000)
    return () => clearInterval(interval)
  }, [])

  const mlActive = health?.models_loaded

  return (
    <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
        <a href="/" className="flex items-center gap-3 no-underline">
          <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center text-xl font-bold text-white">
            AI
          </div>
          <div>
            <h1 className="text-lg sm:text-xl font-bold text-white">AI Detector</h1>
            <p className="text-xs text-gray-400 hidden sm:block">Image & Video Analysis</p>
          </div>
        </a>
        <div className="flex items-center gap-2">
          {health ? (
            <span className={`inline-flex items-center gap-1.5 px-2 sm:px-3 py-1 rounded-full text-xs font-medium border ${
              mlActive
                ? 'bg-green-900/50 text-green-400 border-green-800'
                : 'bg-yellow-900/50 text-yellow-400 border-yellow-800'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${mlActive ? 'bg-green-400' : 'bg-yellow-400'}`}></span>
              <span className="hidden sm:inline">{mlActive ? 'ML + Heuristic' : 'Heuristic Only'}</span>
              <span className="sm:hidden">Online</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2 sm:px-3 py-1 rounded-full text-xs font-medium bg-red-900/50 text-red-400 border border-red-800">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse"></span>
              Offline
            </span>
          )}
        </div>
      </div>
      {health && !mlActive && (
        <div className="bg-yellow-900/20 border-t border-yellow-800/50 px-4 sm:px-6 py-2 text-center text-xs text-yellow-400">
          <span className="hidden sm:inline">Running in heuristic-only mode. Run </span>
          <code className="bg-yellow-900/50 px-1.5 py-0.5 rounded">python install_ml.py</code>
          <span className="hidden sm:inline"> for ML-powered detection.</span>
        </div>
      )}
    </header>
  )
}
