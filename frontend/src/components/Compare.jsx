/* Compare — upload two images and compare their forensic profiles */
import React, { useState, useRef } from 'react'

const ACCEPTED = 'image/jpeg,image/png,image/webp,image/bmp,image/tiff'

export default function Compare() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [file1, setFile1] = useState(null)
  const [file2, setFile2] = useState(null)
  const ref1 = useRef(null)
  const ref2 = useRef(null)

  const handleCompare = async () => {
    if (!file1 || !file2) return
    setLoading(true)
    setError(null)
    setResult(null)

    const form = new FormData()
    form.append('file1', file1)
    form.append('file2', file2)

    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 120000)
      const res = await fetch('/api/compare', { method: 'POST', body: form, signal: controller.signal })
      clearTimeout(timeout)

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail?.error || err.detail || 'Comparison failed')
      }
      setResult(await res.json())
    } catch (e) {
      setError(e.name === 'AbortError' ? 'Comparison timed out.' : e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <a href="/" className="text-sm text-indigo-400 hover:text-indigo-300 mb-6 block">Back to detector</a>
        <h1 className="text-2xl font-bold text-white mb-2">Compare two images</h1>
        <p className="text-sm text-gray-500 mb-8">Upload two images to compare their forensic profiles side by side.</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div
            onClick={() => ref1.current?.click()}
            className="border-2 border-dashed border-gray-700 hover:border-gray-500 rounded-xl p-6 text-center cursor-pointer transition-colors"
          >
            <input ref={ref1} type="file" className="hidden" accept={ACCEPTED} onChange={(e) => setFile1(e.target.files?.[0] || null)} />
            <p className="text-sm text-gray-300">{file1 ? file1.name : 'Choose image 1'}</p>
            <p className="text-xs text-gray-600 mt-1">Click to select</p>
          </div>
          <div
            onClick={() => ref2.current?.click()}
            className="border-2 border-dashed border-gray-700 hover:border-gray-500 rounded-xl p-6 text-center cursor-pointer transition-colors"
          >
            <input ref={ref2} type="file" className="hidden" accept={ACCEPTED} onChange={(e) => setFile2(e.target.files?.[0] || null)} />
            <p className="text-sm text-gray-300">{file2 ? file2.name : 'Choose image 2'}</p>
            <p className="text-xs text-gray-600 mt-1">Click to select</p>
          </div>
        </div>

        <button
          onClick={handleCompare}
          disabled={!file1 || !file2 || loading}
          className="w-full py-3 bg-indigo-500 hover:bg-indigo-600 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl font-medium text-sm transition-colors"
        >
          {loading ? 'Comparing...' : 'Compare images'}
        </button>

        {error && (
          <p className="mt-4 text-sm text-red-400">{error}</p>
        )}

        {result && (
          <div className="mt-6 space-y-4 animate-fade-in-up">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className={`p-4 rounded-xl border ${
                result.image1.verdict === 'AI-Generated' ? 'border-red-500/30 bg-red-500/5' : 'border-green-500/30 bg-green-500/5'
              }`}>
                <p className="text-xs text-gray-500 mb-1">Image 1</p>
                <p className="text-sm text-gray-300 truncate mb-2">{result.image1.filename}</p>
                <p className={`text-lg font-bold ${
                  result.image1.verdict === 'AI-Generated' ? 'text-red-400' : 'text-green-400'
                }`}>{result.image1.verdict}</p>
                <p className="text-xs text-gray-500 mt-1">{result.image1.ai_probability}% AI probability</p>
              </div>
              <div className={`p-4 rounded-xl border ${
                result.image2.verdict === 'AI-Generated' ? 'border-red-500/30 bg-red-500/5' : 'border-green-500/30 bg-green-500/5'
              }`}>
                <p className="text-xs text-gray-500 mb-1">Image 2</p>
                <p className="text-sm text-gray-300 truncate mb-2">{result.image2.filename}</p>
                <p className={`text-lg font-bold ${
                  result.image2.verdict === 'AI-Generated' ? 'text-red-400' : 'text-green-400'
                }`}>{result.image2.verdict}</p>
                <p className="text-xs text-gray-500 mt-1">{result.image2.ai_probability}% AI probability</p>
              </div>
            </div>
            <div className="p-4 bg-gray-900/50 border border-gray-800 rounded-xl">
              <p className="text-sm text-gray-300">{result.comparison.summary}</p>
              <p className="text-xs text-gray-600 mt-2">Score difference: {result.comparison.score_difference} percentage points</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
