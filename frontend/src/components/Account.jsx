/* Account — saved results page for authenticated users */
import React, { useState, useEffect } from 'react'
import { getAuthToken, getAuthHeaders } from './AccountButton'

export default function Account() {
  const [user, setUser] = useState(null)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const token = getAuthToken()
    if (!token) {
      setError('Please log in to view your saved results.')
      setLoading(false)
      return
    }
    Promise.all([
      fetch('/api/auth/me', { headers: getAuthHeaders() }).then(r => r.ok ? r.json() : null),
      fetch('/api/user/results', { headers: getAuthHeaders() }).then(r => r.ok ? r.json() : null),
    ]).then(([u, r]) => {
      setUser(u)
      setResults(r?.results || [])
    }).catch(() => setError('Failed to load account data.'))
      .finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id) => {
    const res = await fetch(`/api/user/results/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    })
    if (res.ok) {
      setResults(prev => prev.filter(r => r.id !== id))
    }
  }

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <p className="text-gray-500">Loading...</p>
    </div>
  )

  if (error) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center">
        <p className="text-gray-400 mb-4">{error}</p>
        <a href="/" className="text-sm text-indigo-400 hover:text-indigo-300">Back to detector</a>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-2xl mx-auto px-6 py-12">
        <a href="/" className="text-sm text-indigo-400 hover:text-indigo-300 mb-6 block">Back to detector</a>
        <h1 className="text-2xl font-bold text-white mb-2">Your saved results</h1>
        {user && <p className="text-sm text-gray-500 mb-8">{user.email}</p>}

        {results.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-2">No saved results yet.</p>
            <p className="text-xs text-gray-600">Analyse an image and click "Save to account" to keep it here.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {results.map((r) => (
              <div key={r.id} className="flex items-center justify-between px-4 py-3 bg-gray-900/50 border border-gray-800 rounded-xl">
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    r.verdict === 'AI-Generated' ? 'bg-red-500' : 'bg-green-500'
                  }`} />
                  <div className="min-w-0">
                    <p className="text-sm text-gray-300 truncate">{r.filename || 'Unknown'}</p>
                    <p className="text-xs text-gray-600">{new Date(r.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    r.verdict === 'AI-Generated' ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'
                  }`}>
                    {r.verdict === 'AI-Generated' ? 'AI' : 'Real'}
                  </span>
                  <span className="text-xs text-gray-500 font-mono">{r.ai_probability}%</span>
                  <button
                    onClick={() => handleDelete(r.id)}
                    className="text-xs text-gray-600 hover:text-red-400 transition-colors"
                    title="Delete"
                  >
                    x
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
