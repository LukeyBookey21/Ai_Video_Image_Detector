import React, { useState, useEffect } from 'react'
import Header from './components/Header'
import Upload from './components/Upload'
import ResultCard from './components/ResultCard'
import DetailedStats from './components/DetailedStats'
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
            Upload an image or video to analyze with our 9+ signal forensic pipeline.
            Combines ML models, frequency, noise, texture, SRM, color space, face, and metadata analysis.
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
          <div className="mt-6 space-y-4">
            <ResultCard result={result} />

            {/* Explanation */}
            {result.explanation && (
              <div className={`px-5 py-4 rounded-xl border text-sm leading-relaxed ${
                result.verdict === 'AI-Generated'
                  ? 'bg-red-500/5 border-red-500/30 text-red-300'
                  : 'bg-green-500/5 border-green-500/30 text-green-300'
              }`}>
                <p className="font-medium text-xs uppercase tracking-wider mb-2 opacity-70">
                  {result.verdict === 'AI-Generated' ? 'Why AI was detected' : 'Why this looks authentic'}
                </p>
                <p>{result.explanation}</p>
              </div>
            )}

            {/* Detailed Stats */}
            <DetailedStats result={result} />
          </div>
        )}

        {/* History */}
        <History history={history} onClear={clearHistory} />

        {/* Info */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
            <h4 className="text-sm font-medium text-indigo-400 mb-2">Frequency & Noise</h4>
            <p className="text-xs text-gray-500">
              DCT + FFT spectral analysis, SRM noise fingerprinting, and multi-scale noise consistency. Detects artifacts invisible to the human eye.
            </p>
          </div>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
            <h4 className="text-sm font-medium text-indigo-400 mb-2">Color & Face</h4>
            <p className="text-xs text-gray-500">
              LAB/YCbCr color space forensics, face symmetry, skin texture, and boundary artifact detection for deepfakes.
            </p>
          </div>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
            <h4 className="text-sm font-medium text-indigo-400 mb-2">Video & Temporal</h4>
            <p className="text-xs text-gray-500">
              Optical flow, physiological signal (rPPG), cross-frame identity consistency, and background-foreground coherence analysis.
            </p>
          </div>
        </div>
      </main>

      <footer className="text-center py-6 text-xs text-gray-600 border-t border-gray-900">
        AI Detector v2.0 — 9+ Signal Ensemble Detection Pipeline
      </footer>
    </div>
  )
}
