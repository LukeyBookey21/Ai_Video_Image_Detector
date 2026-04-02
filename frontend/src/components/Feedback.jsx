/* Feedback — simple thumbs up/down after analysis results */
import React, { useState } from 'react'

export default function Feedback() {
  const [submitted, setSubmitted] = useState(null)

  if (submitted) {
    return (
      <div className="text-center py-3">
        <p className="text-xs text-gray-500">
          {submitted === 'yes' ? 'Glad it helped!' : 'Thanks for the feedback — we\'ll work on improving.'}
        </p>
      </div>
    )
  }

  return (
    <div className="text-center py-3">
      <p className="text-xs text-gray-500 mb-2">Was this result helpful?</p>
      <div className="flex items-center justify-center gap-3">
        <button
          onClick={() => setSubmitted('yes')}
          className="px-3 py-1.5 text-xs text-gray-400 hover:text-green-400 border border-gray-800 hover:border-green-800 rounded-lg transition-colors min-h-[36px]"
        >
          Yes, helpful
        </button>
        <button
          onClick={() => setSubmitted('no')}
          className="px-3 py-1.5 text-xs text-gray-400 hover:text-red-400 border border-gray-800 hover:border-red-800 rounded-lg transition-colors min-h-[36px]"
        >
          Not sure
        </button>
      </div>
    </div>
  )
}
