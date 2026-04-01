/* ProgressIndicator — animated multi-step loading indicator */
import React, { useState, useEffect } from 'react'

const STEPS = [
  { label: 'Uploading your file', delay: 0 },
  { label: 'Reading file metadata', delay: 800 },
  { label: 'Running frequency analysis', delay: 1800 },
  { label: 'Checking for facial patterns', delay: 3000 },
  { label: 'Running AI model analysis', delay: 4500 },
  { label: 'Calculating final result', delay: 6500 },
]

export default function ProgressIndicator() {
  const [activeStep, setActiveStep] = useState(0)
  const [showHint, setShowHint] = useState(false)

  useEffect(() => {
    const timers = STEPS.map((step, i) => {
      if (i === 0) return null
      return setTimeout(() => setActiveStep(i), step.delay)
    })
    const hintTimer = setTimeout(() => setShowHint(true), 3000)

    return () => {
      timers.forEach(t => t && clearTimeout(t))
      clearTimeout(hintTimer)
    }
  }, [])

  return (
    <div className="space-y-3 py-2">
      {STEPS.map((step, i) => {
        const isComplete = i < activeStep
        const isActive = i === activeStep
        const isPending = i > activeStep

        return (
          <div key={i} className="flex items-center gap-3">
            {/* Status dot */}
            <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
              {isComplete && (
                <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              )}
              {isActive && (
                <span className="block w-2.5 h-2.5 bg-indigo-400 rounded-full animate-pulse" />
              )}
              {isPending && (
                <span className="block w-2 h-2 bg-gray-700 rounded-full" />
              )}
            </div>
            {/* Label */}
            <span className={`text-sm transition-colors duration-300 ${
              isComplete ? 'text-gray-500' : isActive ? 'text-gray-200' : 'text-gray-700'
            }`}>
              {step.label}
            </span>
          </div>
        )
      })}

      {showHint && (
        <p className="text-xs text-gray-600 mt-2 pl-8 transition-opacity duration-500">
          This usually takes 10-20 seconds
        </p>
      )}
    </div>
  )
}
