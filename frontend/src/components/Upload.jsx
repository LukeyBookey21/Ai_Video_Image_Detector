/* Upload component — file upload and URL input tabs */
import React, { useState, useRef, useCallback } from 'react'
import ProgressIndicator from './ProgressIndicator'

const ACCEPTED_TYPES = [
  'image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff',
  'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 'video/webm',
]

const isTouchDevice = typeof window !== 'undefined' && ('ontouchstart' in window || navigator.maxTouchPoints > 0)

export default function Upload({ onResult, onError, isLoading, setIsLoading }) {
  const [tab, setTab] = useState('file')
  const [dragActive, setDragActive] = useState(false)
  const [preview, setPreview] = useState(null)
  const [fileName, setFileName] = useState('')
  const [url, setUrl] = useState('')
  const fileInputRef = useRef(null)

  const handleFile = useCallback(async (file) => {
    if (!file) return

    if (!ACCEPTED_TYPES.includes(file.type)) {
      onError('This file type isn\'t supported. Please upload a JPEG, PNG, WebP, MP4, MOV, AVI, or WebM file.')
      return
    }

    if (file.size > 50 * 1024 * 1024) {
      onError('This file is too large. The maximum size is 50 MB.')
      return
    }

    setFileName(file.name)

    if (file.type.startsWith('image/')) {
      setPreview({ type: 'image', url: URL.createObjectURL(file) })
    } else if (file.type.startsWith('video/')) {
      setPreview({ type: 'video', url: URL.createObjectURL(file) })
    }

    setIsLoading(true)
    onError(null)
    onResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 120000)

      const response = await fetch('/api/detect', {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })

      clearTimeout(timeout)

      if (!response.ok) {
        let detail = 'Detection failed'
        try {
          const err = await response.json()
          detail = err.detail?.error || err.detail || err.error || detail
        } catch {}
        throw new Error(detail)
      }

      const result = await response.json()
      onResult(result)
    } catch (err) {
      if (err.name === 'AbortError') {
        onError('This is taking longer than expected. Try a smaller file or shorter video.')
      } else if (err.message === 'Failed to fetch') {
        onError("We're having trouble connecting. Please try again in a moment.")
      } else {
        onError(err.message || 'Failed to analyze file.')
      }
    } finally {
      setIsLoading(false)
    }
  }, [onResult, onError, setIsLoading])

  const handleUrl = useCallback(async () => {
    const trimmed = url.trim()
    if (!trimmed) return

    try {
      const parsed = new URL(trimmed)
      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        onError('Please enter a URL starting with http:// or https://')
        return
      }
    } catch {
      onError('Please enter a valid URL.')
      return
    }

    setIsLoading(true)
    onError(null)
    onResult(null)
    setFileName(trimmed)

    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 120000)

      const response = await fetch('/api/detect-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: trimmed }),
        signal: controller.signal,
      })

      clearTimeout(timeout)

      if (!response.ok) {
        let detail = 'Detection failed'
        try {
          const err = await response.json()
          detail = err.detail?.error || err.detail || err.error || detail
        } catch {}
        throw new Error(detail)
      }

      const result = await response.json()
      onResult(result)
    } catch (err) {
      if (err.name === 'AbortError') {
        onError('This is taking longer than expected. The file may be too large.')
      } else if (err.message === 'Failed to fetch') {
        onError("We're having trouble connecting. Please try again in a moment.")
      } else {
        onError(err.message || 'Failed to analyze URL.')
      }
    } finally {
      setIsLoading(false)
    }
  }, [url, onResult, onError, setIsLoading])

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }, [handleFile])

  const handleInputChange = useCallback((e) => {
    if (e.target.files?.[0]) {
      handleFile(e.target.files[0])
    }
  }, [handleFile])

  // Support Ctrl+V paste from clipboard
  const handlePaste = useCallback((e) => {
    const items = e.clipboardData?.items
    if (!items) return
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        e.preventDefault()
        const file = item.getAsFile()
        if (file) handleFile(file)
        return
      }
    }
  }, [handleFile])

  // Listen for paste events globally
  React.useEffect(() => {
    document.addEventListener('paste', handlePaste)
    return () => document.removeEventListener('paste', handlePaste)
  }, [handlePaste])

  const reset = () => {
    setPreview(null)
    setFileName('')
    setUrl('')
    onResult(null)
    onError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div className="space-y-4">
      {/* Tab switcher */}
      <div className="flex rounded-xl bg-gray-900/50 border border-gray-800 p-1">
        <button
          onClick={() => setTab('file')}
          className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-colors ${
            tab === 'file' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'text-gray-500 hover:text-gray-300'
          }`}
        >
          Upload file
        </button>
        <button
          onClick={() => setTab('url')}
          className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-colors ${
            tab === 'url' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'text-gray-500 hover:text-gray-300'
          }`}
        >
          Paste a link
        </button>
      </div>

      {tab === 'file' ? (
        <>
          {/* File upload zone */}
          <div
            className={`relative border-2 border-dashed rounded-2xl p-8 md:p-12 text-center cursor-pointer transition-all duration-200 ${
              dragActive
                ? 'border-indigo-500 bg-indigo-500/10'
                : 'border-gray-700 hover:border-gray-500 bg-gray-900/50'
            } ${isLoading ? 'pointer-events-none opacity-60' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept={ACCEPTED_TYPES.join(',')}
              onChange={handleInputChange}
            />

            {isLoading ? (
              <div onClick={(e) => e.stopPropagation()}>
                <ProgressIndicator />
              </div>
            ) : (
              <div className="space-y-4">
                <div className="w-16 h-16 mx-auto bg-gray-800 rounded-2xl flex items-center justify-center">
                  <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <div>
                  <p className="text-lg text-gray-200">
                    {isTouchDevice
                      ? <>Tap to choose a file</>
                      : <>Drop an image or video here, or <span className="text-indigo-400 font-medium">browse</span></>
                    }
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    JPEG, PNG, WebP, MP4, AVI, MOV, WebM — up to 50 MB
                  </p>
                  {!isTouchDevice && (
                    <p className="text-xs text-gray-600 mt-1">
                      You can also paste an image with Ctrl+V
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Preview */}
          {preview && !isLoading && (
            <div className="relative rounded-xl overflow-hidden bg-gray-900 border border-gray-800">
              <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-800">
                <span className="text-sm text-gray-400 truncate">{fileName}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); reset() }}
                  className="text-xs text-gray-500 hover:text-white px-2 py-1 rounded hover:bg-gray-800 transition-colors"
                >
                  Clear
                </button>
              </div>
              <div className="max-h-64 overflow-hidden flex items-center justify-center bg-black">
                {preview.type === 'image' ? (
                  <img src={preview.url} alt="Preview" className="max-h-64 object-contain" />
                ) : (
                  <video src={preview.url} className="max-h-64" controls muted />
                )}
              </div>
            </div>
          )}
        </>
      ) : (
        /* URL input tab */
        <div className={`rounded-2xl border border-gray-700 bg-gray-900/50 p-6 md:p-8 ${isLoading ? 'opacity-60 pointer-events-none' : ''}`}>
          {isLoading ? (
            <ProgressIndicator />
          ) : (
            <div className="space-y-4">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleUrl()}
                placeholder="Paste an image or video URL..."
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm"
              />
              <button
                onClick={handleUrl}
                disabled={!url.trim()}
                className="w-full py-3 bg-indigo-500 hover:bg-indigo-600 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl font-medium text-sm transition-colors"
              >
                Check this link
              </button>
              <p className="text-xs text-gray-600 text-center">
                We'll download the file, check it, then delete it immediately.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
