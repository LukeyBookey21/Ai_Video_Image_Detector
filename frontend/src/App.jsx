import React, { useState, useEffect } from 'react'
import Header from './components/Header'
import Upload from './components/Upload'
import ResultCard from './components/ResultCard'
import History from './components/History'

const HISTORY_KEY = 'ai-detector-history'

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
  } catch {
    return []
  }
}

export default function App() {
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [history, setHistory] = useState(loadHistory)

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 20)))
  }, [history])

  const handleResult = (res) => {
    setResult(res)
    if (res) {
      setHistory(prev => [
        { filename: res.filename, verdict: res.verdict, ai_probability: res.ai_probability, file_type: res.file_type },
        ...prev.slice(0, 19),
      ])
    }
  }

  const clearHistory = () => {
    setHistory([])
    localStorage.removeItem(HISTORY_KEY)
  }

  return (
    <div className="min-h-screen bg-gray-950">
      <Header />

      <main className="max-w-3xl mx-auto px-6 py-10">
        {/* Hero */}
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-white mb-3">
            Detect AI-Generated Content
          </h2>
          <p className="text-gray-400 max-w-lg mx-auto">
            Upload an image or video to analyze it with our ensemble forensic pipeline.
            Combines frequency, statistical, and texture analysis for reliable detection.
          </p>
        </div>

        {/* Upload */}
        <Upload
          onResult={handleResult}
          onError={setError}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
        />

        {/* Error */}
        {error && (
          <div className="mt-6 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="mt-6">
            <ResultCard result={result} />
          </div>
        )}

        {/* History */}
        <History history={history} onClear={clearHistory} />

        {/* Info */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
            <h4 className="text-sm font-medium text-indigo-400 mb-2">Frequency Analysis</h4>
            <p className="text-xs text-gray-500">
              DCT + FFT spectral analysis detects artifacts in the frequency domain that are invisible to the human eye. AI images deviate from natural 1/f power law.
            </p>
          </div>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
            <h4 className="text-sm font-medium text-indigo-400 mb-2">Statistical Analysis</h4>
            <p className="text-xs text-gray-500">
              Analyzes noise patterns, pixel distributions, and color channel correlations. AI-generated content has distinct statistical fingerprints.
            </p>
          </div>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
            <h4 className="text-sm font-medium text-indigo-400 mb-2">Texture & Video</h4>
            <p className="text-xs text-gray-500">
              Detects unnatural smoothness and edge patterns. For video, extracts keyframes and analyzes each independently.
            </p>
          </div>
        </div>
      </main>

      <footer className="text-center py-6 text-xs text-gray-600 border-t border-gray-900">
        AI Detector v1.0 — Ensemble ML Detection Pipeline
      </footer>
    </div>
  )
}
