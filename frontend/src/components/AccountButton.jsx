/* AccountButton — login/account dropdown in header */
import React, { useState, useEffect, useRef } from 'react'

const TOKEN_KEY = 'ai-detector-token'
const USER_KEY = 'ai-detector-user'

export function getAuthToken() {
  try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
}

export function getAuthHeaders() {
  const token = getAuthToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export default function AccountButton() {
  const [user, setUser] = useState(null)
  const [showLogin, setShowLogin] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const menuRef = useRef(null)

  useEffect(() => {
    // Check for saved token
    const token = getAuthToken()
    if (token) {
      fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.ok ? r.json() : null)
        .then(u => { if (u) setUser(u) })
        .catch(() => {})
    }
  }, [])

  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setShowMenu(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleLogin = async (e) => {
    e.preventDefault()
    if (!email.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      })
      if (!res.ok) throw new Error('Login failed')
      const data = await res.json()
      try {
        localStorage.setItem(TOKEN_KEY, data.token)
        localStorage.setItem(USER_KEY, JSON.stringify({ email: data.email }))
      } catch {}
      setUser({ email: data.email })
      setShowLogin(false)
      setEmail('')
    } catch (e) {
      setError('Could not log in. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    try {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    } catch {}
    setUser(null)
    setShowMenu(false)
  }

  if (user) {
    return (
      <div className="relative" ref={menuRef}>
        <button
          onClick={() => setShowMenu(!showMenu)}
          className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-bold text-white"
          title={user.email}
        >
          {user.email[0].toUpperCase()}
        </button>
        {showMenu && (
          <div className="absolute right-0 top-10 w-56 bg-gray-900 border border-gray-800 rounded-xl shadow-lg py-2 z-50">
            <p className="px-4 py-1 text-xs text-gray-500 truncate">{user.email}</p>
            <a href="/account" className="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-800 transition-colors">
              Saved results
            </a>
            <button
              onClick={handleLogout}
              className="w-full text-left px-4 py-2 text-sm text-gray-400 hover:bg-gray-800 transition-colors"
            >
              Log out
            </button>
          </div>
        )}
      </div>
    )
  }

  if (showLogin) {
    return (
      <form onSubmit={handleLogin} className="flex items-center gap-2">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="w-36 px-2 py-1 bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
        />
        <button type="submit" disabled={loading} className="px-2 py-1 bg-indigo-600 rounded-lg text-xs text-white">
          {loading ? '...' : 'Go'}
        </button>
        <button type="button" onClick={() => setShowLogin(false)} className="text-xs text-gray-500">
          Cancel
        </button>
        {error && <span className="text-xs text-red-400">{error}</span>}
      </form>
    )
  }

  return (
    <button
      onClick={() => setShowLogin(true)}
      className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
    >
      Log in
    </button>
  )
}
