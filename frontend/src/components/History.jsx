/* History — recent analysis results from localStorage */
import React from 'react'

function relativeTime(isoString) {
  if (!isoString) return ''
  const diff = Date.now() - new Date(isoString).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins} minute${mins === 1 ? '' : 's'} ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days} days ago`
  return new Date(isoString).toLocaleDateString()
}

function truncate(str, len) {
  if (!str) return ''
  return str.length > len ? str.slice(0, len) + '...' : str
}

export default function History({ history, onClear, onSelect }) {
  if (!history.length) return null

  return (
    <div className="mt-8">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">Recent checks</h3>
        <button
          onClick={onClear}
          className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
        >
          Clear history
        </button>
      </div>
      <div className="space-y-2">
        {history.map((item, index) => {
          const isAI = item.verdict === 'AI-Generated'
          return (
            <button
              key={item.id || index}
              onClick={() => onSelect && onSelect(item)}
              className="w-full flex items-center justify-between px-4 py-3 bg-gray-900/50 border border-gray-800 rounded-xl text-sm hover:border-gray-700 hover:bg-gray-900 transition-colors text-left"
            >
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${isAI ? 'bg-red-500' : 'bg-green-500'}`} />
                <div className="min-w-0 flex-1">
                  <span className="text-gray-300 truncate block">{truncate(item.filename, 40)}</span>
                  {item.confidencePhrase && (
                    <span className="text-xs text-gray-500 block mt-0.5">{item.confidencePhrase}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0 ml-3">
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  isAI ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'
                }`}>
                  {isAI ? 'AI' : 'Real'}
                </span>
                <span className="text-gray-600 text-xs whitespace-nowrap">{relativeTime(item.timestamp)}</span>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
