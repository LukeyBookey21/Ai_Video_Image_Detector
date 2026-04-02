/* BatchUpload — upload and analyse multiple files at once */
import React, { useState, useRef } from 'react'

const ACCEPTED_TYPES = [
  'image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff',
  'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 'video/webm',
]

function VerdictBadge({ verdict }) {
  if (!verdict) return null
  const isAI = verdict === 'AI-Generated'
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
      isAI ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'
    }`}>
      {isAI ? 'AI' : 'Real'}
    </span>
  )
}

export default function BatchUpload({ onError }) {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [fileCount, setFileCount] = useState(0)
  const inputRef = useRef(null)

  const handleFiles = async (files) => {
    const fileList = Array.from(files).filter(f => ACCEPTED_TYPES.includes(f.type)).slice(0, 10)
    if (fileList.length === 0) {
      onError && onError('No supported files selected. Please choose images or videos.')
      return
    }

    setFileCount(fileList.length)
    setLoading(true)
    setResults([])
    onError && onError(null)

    const formData = new FormData()
    fileList.forEach(f => formData.append('files', f))

    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 300000) // 5 min for batch

      const response = await fetch('/api/detect/batch', {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })
      clearTimeout(timeout)

      if (!response.ok) {
        let detail = 'Batch analysis failed'
        try {
          const err = await response.json()
          detail = err.detail?.error || err.detail || err.error || detail
        } catch {}
        throw new Error(detail)
      }

      const data = await response.json()
      setResults(data.results || [])
    } catch (err) {
      if (err.name === 'AbortError') {
        onError && onError('Batch analysis timed out.')
      } else if (err.message === 'Failed to fetch') {
        onError && onError("We're having trouble connecting. Please try again in a moment.")
      } else {
        onError && onError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          loading ? 'opacity-60 pointer-events-none border-gray-800' : 'border-gray-700 hover:border-gray-500 bg-gray-900/50'
        }`}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          multiple
          accept={ACCEPTED_TYPES.join(',')}
          onChange={(e) => e.target.files?.length && handleFiles(e.target.files)}
        />
        {loading ? (
          <div className="space-y-3">
            <div className="w-12 h-12 mx-auto border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-gray-300">Analysing {fileCount} files...</p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-base text-gray-200">Select multiple files to check at once</p>
            <p className="text-xs text-gray-500">Up to 10 files, 50 MB each</p>
          </div>
        )}
      </div>

      {results.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Results ({results.length} files)</p>
          {results.map((r, i) => (
            <div key={i} className="flex items-center justify-between px-4 py-3 bg-gray-900/50 border border-gray-800 rounded-xl text-sm">
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <span className="text-gray-300 truncate">{r.filename || 'Unknown'}</span>
              </div>
              {r.error ? (
                <span className="text-xs text-red-400 ml-2">{r.error}</span>
              ) : (
                <div className="flex items-center gap-3 flex-shrink-0 ml-2">
                  <VerdictBadge verdict={r.verdict} />
                  <span className="text-xs text-gray-500 font-mono">{r.ai_probability}%</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
