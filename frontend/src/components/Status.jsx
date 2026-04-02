/* Status — system health check page for debugging */
import React, { useState, useEffect } from 'react'

function HealthItem({ label, value, ok }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-800/50 last:border-0">
      <span className="text-sm text-gray-400">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-300 font-mono">{value}</span>
        <span className={`w-2 h-2 rounded-full ${ok ? 'bg-green-500' : 'bg-red-500'}`} />
      </div>
    </div>
  )
}

export default function Status() {
  const [health, setHealth] = useState(null)
  const [latency, setLatency] = useState(null)
  const [error, setError] = useState(null)

  const check = async () => {
    const start = Date.now()
    try {
      const res = await fetch('/api/health')
      setLatency(Date.now() - start)
      if (res.ok) {
        setHealth(await res.json())
        setError(null)
      } else {
        setError(`HTTP ${res.status}`)
      }
    } catch (e) {
      setLatency(Date.now() - start)
      setError(e.message)
    }
  }

  useEffect(() => {
    check()
    const interval = setInterval(check, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-lg mx-auto px-6 py-12">
        <a href="/" className="text-sm text-indigo-400 hover:text-indigo-300 mb-6 block">Back to detector</a>
        <h1 className="text-2xl font-bold text-white mb-8">System Status</h1>

        {error ? (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl mb-6">
            <p className="text-sm text-red-400">Backend unreachable: {error}</p>
          </div>
        ) : health ? (
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
            <HealthItem label="Status" value={health.status} ok={health.status === 'ok'} />
            <HealthItem label="Version" value={health.version} ok={true} />
            <HealthItem label="ML Models" value={health.models_loaded ? 'Loaded' : 'Not loaded'} ok={health.models_loaded} />
            <HealthItem label="Detection Mode" value={health.detection_mode} ok={true} />
            <HealthItem label="Analyzers" value={`${health.analyzers?.length || 0} active`} ok={health.analyzers?.length > 0} />
            <HealthItem label="API Latency" value={`${latency}ms`} ok={latency < 500} />
          </div>
        ) : (
          <p className="text-gray-500">Checking...</p>
        )}

        <p className="text-xs text-gray-600 mt-4 text-center">Auto-refreshes every 10 seconds</p>
      </div>
    </div>
  )
}
