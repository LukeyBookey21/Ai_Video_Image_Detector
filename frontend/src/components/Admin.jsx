/* Admin — simple stats dashboard (unlisted route) */
import React, { useState, useEffect } from 'react'

function MetricCard({ label, value, color }) {
  return (
    <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5 text-center">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-xl sm:text-2xl md:text-3xl font-bold font-mono ${color || 'text-white'}`}>{value}</p>
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
      <p className="text-red-400">{error}</p>
    </div>
  )

  if (!stats) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <p className="text-gray-500">Loading stats...</p>
    </div>
  )

  const detectionRate = stats.total_analyses > 0
    ? ((stats.ai_detected / stats.total_analyses) * 100).toFixed(1)
    : '0.0'

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-2xl mx-auto px-6 py-12">
        <h1 className="text-2xl font-bold text-white mb-8">Admin Stats</h1>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <MetricCard label="Total Analyses" value={stats.total_analyses} color="text-indigo-400" />
          <MetricCard label="AI Detected" value={stats.ai_detected} color="text-red-400" />
          <MetricCard label="Authentic" value={stats.authentic} color="text-green-400" />
          <MetricCard label="Uncertain" value={stats.uncertain} color="text-yellow-400" />
          <MetricCard label="Detection Rate" value={`${detectionRate}%`} color="text-orange-400" />
        </div>

        {stats.last_updated && (
          <p className="text-xs text-gray-600 mt-6 text-center">
            Last updated: {new Date(stats.last_updated).toLocaleString()}
          </p>
        )}

        <p className="text-xs text-gray-700 mt-2 text-center">Auto-refreshes every 30 seconds</p>
      </div>
    </div>
  )
}
