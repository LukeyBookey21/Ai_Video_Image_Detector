import React, { useState, useRef, useCallback } from 'react'

const ACCEPTED_TYPES = [
  'image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff',
  'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 'video/webm',
]

export default function Upload({ onResult, onError, isLoading, setIsLoading }) {
  const [dragActive, setDragActive] = useState(false)
  const [preview, setPreview] = useState(null)
  const [fileName, setFileName] = useState('')
  const fileInputRef = useRef(null)

  const handleFile = useCallback(async (file) => {
    if (!file) return

    if (!ACCEPTED_TYPES.includes(file.type)) {
      onError(`Unsupported file type: ${file.type}`)
      return
    }

    if (file.size > 100 * 1024 * 1024) {
      onError('File too large. Maximum size is 100MB.')
      return
    }

    setFileName(file.name)

    // Generate preview
    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file)
      setPreview({ type: 'image', url })
    } else if (file.type.startsWith('video/')) {
      const url = URL.createObjectURL(file)
      setPreview({ type: 'video', url })
    }

    // Upload and analyze
    setIsLoading(true)
    onError(null)
    onResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 120000) // 2 min timeout

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
          detail = err.detail || detail
        } catch {}
        throw new Error(detail)
      }

      const result = await response.json()
      onResult(result)
    } catch (err) {
      if (err.name === 'AbortError') {
        onError('Analysis timed out. Try a smaller file or shorter video.')
      } else if (err.message === 'Failed to fetch') {
        onError('Cannot connect to backend. Make sure the backend is running on localhost:8000')
      } else {
        onError(err.message || 'Failed to analyze file.')
      }
    } finally {
      setIsLoading(false)
    }
  }, [onResult, onError, setIsLoading])

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

  const reset = () => {
    setPreview(null)
    setFileName('')
    onResult(null)
    onError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div className="space-y-4">
      {/* Upload zone */}
      <div
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200 ${
          dragActive
            ? 'drop-zone-active border-indigo-500 bg-indigo-500/10'
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
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-lg text-gray-300">Analyzing {fileName}...</p>
            <p className="text-sm text-gray-500">Running ensemble detection (ViT + Frequency Analysis)</p>
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
                Drop an image or video here, or <span className="text-indigo-400 font-medium">browse</span>
              </p>
              <p className="text-sm text-gray-500 mt-1">
                JPEG, PNG, WebP, MP4, AVI, MOV, WebM — up to 100MB
              </p>
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
    </div>
  )
}
