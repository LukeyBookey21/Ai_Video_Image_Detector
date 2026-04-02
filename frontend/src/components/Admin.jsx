/* Admin — stats dashboard with visual metrics (unlisted route) */
import React, { useState, useEffect } from 'react'

function MetricCard({ label, value, color, subtitle }) {
  return (
    <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-xl sm:text-2xl md:text-3xl font-bold font-mono ${color || 'text-white'}`}>{value}</p>
      {subtitle && <p className="text-xs text-gray-600 mt-1">{subtitle}</p>}
    </div>
  )
}

function BarChart({ aiPct, authPct, uncertainPct }) {
  return (
    <div className="mt-6 bg-gray-900/50 border border-gray-800 rounded-xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-4">Detection breakdown</p>
      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-red-400">AI Detected</span>
            <span className="text-gray-400 font-mono">{aiPct}%</span>
          </div>
          <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-red-500 rounded-full transition-all duration-1000" style={{ width: `${aiPct}%` }} />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-green-400">Authentic</span>
            <span className="text-gray-400 font-mono">{authPct}%</span>
          </div>
          <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-green-500 rounded-full transition-all duration-1000" style={{ width: `${authPct}%` }} />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-yellow-400">Uncertain</span>
            <span className="text-gray-400 font-mono">{uncertainPct}%</span>
          </div>
          <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-yellow-500 rounded-full transition-all duration-1000" style={{ width: `${uncertainPct}%` }} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Admin() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/stats')
      if (!res.ok) throw new Error('Failed to fetch stats')
      setStats(await res.json())
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  if (error) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center">
        <p className="text-red-400 mb-2">{error}</p>
        <button onClick={fetchStats} className="text-sm text-indigo-400 hover:text-indigo-300">Retry</button>
      </div>
    </div>
  )

  if (!stats) return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-2xl mx-auto px-6 py-12">
        <h1 className="text-2xl font-bold text-white mb-8">Admin Dashboard</h1>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-gray-900/50 border border-gray-800 rounded-xl p-5 animate-pulse">
              <div className="h-3 w-16 bg-gray-800 rounded mb-3" />
              <div className="h-8 w-24 bg-gray-800 rounded" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const total = stats.total_analyses || 0
  const detectionRate = total > 0 ? ((stats.ai_detected / total) * 100).toFixed(1) : '0.0'
  const authRate = total > 0 ? ((stats.authentic / total) * 100).toFixed(1) : '0.0'
  const uncertainRate = total > 0 ? ((stats.uncertain / total) * 100).toFixed(1) : '0.0'

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-2xl mx-auto px-6 py-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
            <p className="text-xs text-gray-500 mt-1">Auto-refreshes every 30 seconds</p>
          </div>
          <a href="/" className="text-sm text-indigo-400 hover:text-indigo-300">Back to detector</a>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <MetricCard label="Total Analyses" value={total} color="text-indigo-400" />
          <MetricCard label="AI Detected" value={stats.ai_detected} color="text-red-400" subtitle={`${detectionRate}% of total`} />
          <MetricCard label="Authentic" value={stats.authentic} color="text-green-400" subtitle={`${authRate}% of total`} />
          <MetricCard label="Uncertain" value={stats.uncertain} color="text-yellow-400" subtitle={`${uncertainRate}% of total`} />
          <MetricCard label="Detection Rate" value={`${detectionRate}%`} color="text-orange-400" subtitle="AI / total" />
        </div>

        {total > 0 && (
          <BarChart aiPct={detectionRate} authPct={authRate} uncertainPct={uncertainRate} />
        )}

        {stats.last_updated && (
          <p className="text-xs text-gray-600 mt-6 text-center">
            Last analysis: {new Date(stats.last_updated).toLocaleString()}
          </p>
        )}

        <RecentAnalyses />
      </div>
    </div>
  )
}

function RecentAnalyses() {
  const [analyses, setAnalyses] = React.useState([])

  React.useEffect(() => {
    fetch('/api/stats/recent')
      .then(r => r.ok ? r.json() : { analyses: [] })
      .then(d => setAnalyses(d.analyses || []))
      .catch(() => {})
  }, [])

  if (analyses.length === 0) return null

  return (
    <div className="mt-8">
      <h2 className="text-sm font-medium text-gray-400 mb-3">Recent analyses</h2>
      <div className="space-y-1">
        {analyses.slice(0, 20).map((a, i) => (
          <div key={i} className="flex items-center justify-between px-3 py-2 bg-gray-900/30 rounded-lg text-xs">
            <span className="text-gray-400 truncate flex-1 mr-2">{a.filename || 'unknown'}</span>
            <span className={`font-medium ${
              a.verdict === 'AI-Generated' ? 'text-red-400' : a.verdict === 'Real/Authentic' ? 'text-green-400' : 'text-yellow-400'
            }`}>{a.verdict === 'AI-Generated' ? 'AI' : a.verdict === 'Real/Authentic' ? 'Real' : '?'}</span>
            <span className="text-gray-600 ml-3 w-16 text-right">{a.processing_time}s</span>
          </div>
        ))}
      </div>
    </div>
  )
}
