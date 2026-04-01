import React, { useState, useEffect } from 'react'

export default function Header() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    fetch('/api/health')
      .then(r => r.json())
      .then(setHealth)
      .catch(() => setHealth(null))
  }, [])

  const mlActive = health?.ml_model_loaded
  const mode = health?.detection_mode

  return (
    <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center text-xl font-bold">
            AI
          </div>
          <div>
            <h1 className="text-lg sm:text-xl font-bold text-white">AI Detector</h1>
            <p className="text-xs text-gray-400">Image & Video Analysis</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {health ? (
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${
              mlActive
                ? 'bg-green-900/50 text-green-400 border-green-800'
                : 'bg-yellow-900/50 text-yellow-400 border-yellow-800'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${mlActive ? 'bg-green-400' : 'bg-yellow-400'}`}></span>
              {mlActive ? 'ML + Heuristic' : 'Heuristic Only'}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-red-900/50 text-red-400 border border-red-800">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
              Backend Offline
            </span>
          )}
        </div>
      </div>
      {health && !mlActive && (
        <div className="bg-yellow-900/20 border-t border-yellow-800/50 px-6 py-2 text-center text-xs text-yellow-400">
          Running in heuristic-only mode (lower accuracy). Run <code className="bg-yellow-900/50 px-1.5 py-0.5 rounded">python install_ml.py</code> in the backend folder for ML-powered detection (~94% accuracy).
        </div>
      )}
    </header>
  )
}
