/* Waitlist — email capture for feature notifications */
import React, { useState } from 'react'

export default function Waitlist() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState(null) // 'added' | 'already_registered' | 'error'
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email.trim()) return

    setLoading(true)
    setStatus(null)
    setErrorMsg('')

    try {
      const res = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      })

      if (res.status === 422) {
        setErrorMsg('Please enter a valid email address.')
        setStatus('error')
      } else if (res.ok) {
        const data = await res.json()
        setStatus(data.status)
        if (data.status === 'added') setEmail('')
      } else {
        setErrorMsg('Something went wrong. Please try again.')
        setStatus('error')
      }
    } catch {
      setErrorMsg("We're having trouble connecting. Please try again.")
      setStatus('error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mt-10 bg-gray-900/30 border border-gray-800 rounded-xl p-6">
      <h3 className="text-sm font-medium text-gray-300 mb-1">Get notified about new features</h3>
      <p className="text-xs text-gray-600 mb-4">We'll email you when we add new detection capabilities.</p>

      {status === 'added' ? (
        <p className="text-sm text-green-400">You're on the list!</p>
      ) : status === 'already_registered' ? (
        <p className="text-sm text-indigo-400">You're already signed up.</p>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={loading || !email.trim()}
            className="px-4 py-2 bg-indigo-500/20 border border-indigo-500/30 rounded-lg text-sm text-indigo-300 hover:bg-indigo-500/30 disabled:opacity-50 transition-colors whitespace-nowrap"
          >
            {loading ? '...' : 'Join waitlist'}
          </button>
        </form>
      )}

      {status === 'error' && (
        <p className="text-xs text-red-400 mt-2">{errorMsg}</p>
      )}
    </div>
  )
}
