import React, { useState, useEffect } from 'react'
import Header from './components/Header'
import Upload from './components/Upload'
import ResultCard from './components/ResultCard'
import History from './components/History'
import FAQ from './components/FAQ'
import Waitlist from './components/Waitlist'

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
      const confidence = res.confidence || 0
      const isAI = res.verdict === 'AI-Generated'
      let phrase
      if (confidence >= 85) phrase = isAI ? "We're very confident this is AI-generated" : "We're very confident this is authentic"
      else if (confidence >= 65) phrase = isAI ? "We're fairly confident this is AI-generated" : "We're fairly confident this is authentic"
      else if (confidence >= 40) phrase = "We have some concerns about this content"
      else phrase = "We're not certain \u2014 treat with caution"

      setHistory(prev => [
        {
          id: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2),
          filename: res.filename,
          verdict: res.verdict,
          confidence: res.confidence,
          confidencePhrase: phrase,
          explanation: res.explanation || '',
          ai_probability: res.ai_probability,
          file_type: res.file_type,
          timestamp: new Date().toISOString(),
        },
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
          <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-white mb-3">
            Is this image or video real?
          </h2>
          <p className="text-gray-400 max-w-lg mx-auto">
            Upload a photo or video and we'll check if it was created by AI.
            It only takes a few seconds.
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

        {/* FAQ */}
        <FAQ />

        {/* History */}
        <History history={history} onClear={clearHistory} onSelect={(item) => {
          setResult({
            verdict: item.verdict,
            confidence: item.confidence,
            ai_probability: item.ai_probability,
            explanation: item.explanation,
            filename: item.filename,
            file_type: item.file_type,
            detection_mode: 'history',
          })
        }} />

        {/* How it works */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
            <h4 className="text-sm font-medium text-indigo-400 mb-2">We check for hidden patterns</h4>
            <p className="text-xs text-gray-500">
              AI-generated images leave invisible fingerprints in their pixels. We scan for unnatural patterns that the human eye can't see.
            </p>
          </div>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
            <h4 className="text-sm font-medium text-indigo-400 mb-2">We look at faces closely</h4>
            <p className="text-xs text-gray-500">
              AI often struggles with faces — subtle asymmetry, unnatural skin texture, and odd boundaries around hair and ears can give it away.
            </p>
          </div>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
            <h4 className="text-sm font-medium text-indigo-400 mb-2">We analyse video frame by frame</h4>
            <p className="text-xs text-gray-500">
              Deepfake videos can flicker or show inconsistencies between frames. We check every frame individually and how they flow together.
            </p>
          </div>
        </div>

        {/* Waitlist */}
        <Waitlist />
      </main>

      <footer className="text-center py-6 text-xs text-gray-600 border-t border-gray-900">
        AI Detector v2.0 — No detection tool is perfect. Always use your own judgement.
      </footer>
    </div>
  )
}
