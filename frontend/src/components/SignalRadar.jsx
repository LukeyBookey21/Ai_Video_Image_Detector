/* SignalRadar — pure-SVG radar/spider chart of all signal scores. */
import React from 'react'

const LABELS = {
  frequency: 'Frequency',
  statistical: 'Statistical',
  texture: 'Texture',
  srm: 'SRM',
  color: 'Colour',
  metadata: 'Metadata',
  face: 'Face',
  jpeg_ghost: 'JPEG Ghost',
  patch: 'Patch',
  ela: 'ELA',
  gan_fingerprint: 'GAN',
  diffusion_artifacts: 'Diffusion',
  noise_map: 'Noise Map',
  prnu: 'PRNU',
  copy_move: 'Copy-Move',
}

export default function SignalRadar({ featureVector }) {
  if (!featureVector || Object.keys(featureVector).length === 0) return null

  // Keep only signals present, in a stable order
  const keys = Object.keys(LABELS).filter((k) => k in featureVector)
  if (keys.length < 3) return null

  const size = 260
  const cx = size / 2
  const cy = size / 2
  const radius = size / 2 - 40
  const n = keys.length

  const pointAt = (i, r) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2
    return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)]
  }

  // Grid rings
  const rings = [0.25, 0.5, 0.75, 1.0]

  // Data polygon
  const dataPoints = keys.map((k, i) => {
    const v = Math.max(0, Math.min(1, featureVector[k] || 0))
    return pointAt(i, radius * v)
  })
  const dataPath = dataPoints.map((p) => p.join(',')).join(' ')

  // Average score → colour
  const avg = keys.reduce((s, k) => s + (featureVector[k] || 0), 0) / n
  const strokeColor = avg > 0.5 ? '#ef4444' : avg > 0.33 ? '#eab308' : '#22c55e'
  const fillColor = avg > 0.5 ? 'rgba(239,68,68,0.18)' : avg > 0.33 ? 'rgba(234,179,8,0.18)' : 'rgba(34,197,94,0.18)'

  return (
    <div className="px-6 py-4 border-t border-gray-800/50">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Signal radar</p>
      <div className="flex justify-center">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Signal score radar chart">
          {/* Grid rings */}
          {rings.map((r, ri) => (
            <polygon
              key={ri}
              points={keys.map((_, i) => pointAt(i, radius * r).join(',')).join(' ')}
              fill="none"
              stroke="#27272a"
              strokeWidth="1"
            />
          ))}
          {/* Spokes */}
          {keys.map((_, i) => {
            const [x, y] = pointAt(i, radius)
            return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#27272a" strokeWidth="1" />
          })}
          {/* Data polygon */}
          <polygon points={dataPath} fill={fillColor} stroke={strokeColor} strokeWidth="2" />
          {/* Data dots */}
          {dataPoints.map((p, i) => (
            <circle key={i} cx={p[0]} cy={p[1]} r="2.5" fill={strokeColor} />
          ))}
          {/* Labels */}
          {keys.map((k, i) => {
            const [x, y] = pointAt(i, radius + 18)
            return (
              <text
                key={k}
                x={x}
                y={y}
                fontSize="7.5"
                fill="#9ca3af"
                textAnchor={Math.abs(x - cx) < 8 ? 'middle' : x > cx ? 'start' : 'end'}
                dominantBaseline="middle"
              >
                {LABELS[k]}
              </text>
            )
          })}
        </svg>
      </div>
      <p className="text-xs text-gray-600 text-center mt-1">Distance from centre = how AI-like each signal scored</p>
    </div>
  )
}
