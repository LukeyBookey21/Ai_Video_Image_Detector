import React from 'react'

export default function History({ history, onClear }) {
  if (!history.length) return null

  return (
    <div className="mt-8">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">Recent Analyses</h3>
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
            <div
              key={index}
              className="flex items-center justify-between px-4 py-3 bg-gray-900/50 border border-gray-800 rounded-xl text-sm"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${isAI ? 'bg-red-500' : 'bg-green-500'}`} />
                <span className="text-gray-300 truncate">{item.filename}</span>
              </div>
              <div className="flex items-center gap-4 flex-shrink-0">
                <span className={`font-mono font-medium ${isAI ? 'text-red-400' : 'text-green-400'}`}>
                  {item.ai_probability}%
                </span>
                <span className="text-gray-600 text-xs">{item.file_type}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
