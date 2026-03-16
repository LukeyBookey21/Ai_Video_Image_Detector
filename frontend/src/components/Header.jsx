import React from 'react'

export default function Header() {
  return (
    <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center text-xl font-bold">
            AI
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">AI Detector</h1>
            <p className="text-xs text-gray-400">Image & Video Analysis</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-900/50 text-green-400 border border-green-800">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400"></span>
            Ensemble ML
          </span>
        </div>
      </div>
    </header>
  )
}
