/* SignalSummary — plain-English summary of what the detector found */
import React from 'react'

function SignalItem({ label, description, level }) {
  const colors = {
    high: { bar: 'bg-red-500', text: 'text-red-400', label: 'Suspicious' },
    medium: { bar: 'bg-yellow-500', text: 'text-yellow-400', label: 'Moderate' },
    low: { bar: 'bg-green-500', text: 'text-green-400', label: 'Normal' },
    none: { bar: 'bg-gray-700', text: 'text-gray-500', label: 'Not checked' },
  }
  const c = colors[level] || colors.none
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: level === 'high' ? '#ef4444' : level === 'medium' ? '#eab308' : '#22c55e' }} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-300">{label}</p>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
      <span className={`text-xs font-medium ${c.text}`}>{c.label}</span>
    </div>
  )
}

function getLevel(score) {
  if (score >= 50) return 'high'
  if (score >= 30) return 'medium'
  return 'low'
}

export default function SignalSummary({ details, result }) {
  if (!details) return null

  const signals = []

  if (details.metadata_analysis) {
    const s = details.metadata_analysis.ai_score
    const flags = details.metadata_analysis.flags || []
    let desc = 'File metadata and format look normal'
    if (flags.includes('png_no_exif')) desc = 'PNG file with no camera data — common in AI images'
    else if (flags.includes('no_exif_data')) desc = 'No camera information found in the file'
    else if (flags.includes('has_camera_info')) desc = 'Real camera data found (model, settings, etc.)'
    else if (flags.includes('ai_software')) desc = 'AI generation software detected in file metadata'
    signals.push({ label: 'File origin', description: desc, level: getLevel(s) })
  }

  if (details.frequency_analysis) {
    const s = details.frequency_analysis.ai_score
    signals.push({
      label: 'Hidden patterns',
      description: s >= 50 ? 'Unusual frequency patterns detected in the pixels' : 'Frequency patterns look natural',
      level: getLevel(s),
    })
  }

  if (details.face_analysis && details.face_analysis.faces_found > 0) {
    const s = details.face_analysis.ai_score
    signals.push({
      label: `Face analysis (${details.face_analysis.faces_found} found)`,
      description: s >= 40 ? 'Facial features show potential AI artifacts' : 'Facial features appear natural',
      level: getLevel(s),
    })
  }

  if (details.color_analysis) {
    const s = details.color_analysis.ai_score
    signals.push({
      label: 'Colour patterns',
      description: s >= 40 ? 'Colour distribution shows signs of AI generation' : 'Colour distribution looks natural',
      level: getLevel(s),
    })
  }

  // Video-specific: animation detection
  if (result?.temporal_analysis?.animation_detected) {
    signals.push({
      label: 'Animation detected',
      description: 'This video shows signs of stop-motion animation or CGI — not real camera footage',
      level: 'high',
    })
  }

  if (signals.length === 0) return null

  return (
    <div className="px-6 py-4 border-t border-gray-800/50 bg-gray-900/40">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">What we found</p>
      <div className="divide-y divide-gray-800/50">
        {signals.map((s, i) => (
          <SignalItem key={i} {...s} />
        ))}
      </div>
    </div>
  )
}
