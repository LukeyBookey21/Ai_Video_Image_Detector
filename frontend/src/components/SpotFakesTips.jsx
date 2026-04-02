/* SpotFakesTips — practical tips for spotting AI content without tools */
import React from 'react'

const TIPS = [
  {
    title: 'Look at the hands and fingers',
    desc: 'AI often draws the wrong number of fingers, fused fingers, or hands that look waxy and unnatural.',
  },
  {
    title: 'Check the background',
    desc: 'Look for warped text, melting objects, or patterns that don\'t make sense. AI often struggles with background details.',
  },
  {
    title: 'Zoom in on teeth and ears',
    desc: 'Teeth may be blurred, asymmetric, or too perfect. Ears often look different from each other in AI images.',
  },
  {
    title: 'Look for the uncanny smoothness',
    desc: 'AI skin often looks too smooth and poreless. Real faces have pores, fine lines, and uneven skin tone.',
  },
  {
    title: 'Check if the lighting makes sense',
    desc: 'Shadows should fall consistently. AI sometimes puts light sources in contradictory positions.',
  },
]

export default function SpotFakesTips() {
  return (
    <div className="mt-10">
      <h3 className="text-sm font-medium text-gray-400 mb-4">How to spot fakes yourself</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {TIPS.map((tip, i) => (
          <div key={i} className="bg-gray-900/30 border border-gray-800/50 rounded-xl p-4">
            <p className="text-sm text-gray-300 font-medium mb-1">{tip.title}</p>
            <p className="text-xs text-gray-500 leading-relaxed">{tip.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
