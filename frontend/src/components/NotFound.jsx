/* NotFound — friendly 404 page */
import React from 'react'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-6">
      <div className="text-center max-w-md">
        <p className="text-6xl font-bold text-gray-800 mb-4">404</p>
        <h1 className="text-xl font-bold text-white mb-2">Page not found</h1>
        <p className="text-sm text-gray-500 mb-6">The page you're looking for doesn't exist.</p>
        <a
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-500/20 border border-indigo-500/30 rounded-xl text-sm text-indigo-300 hover:bg-indigo-500/30 transition-colors"
        >
          Go to AI Detector
        </a>
      </div>
    </div>
  )
}
