/* EvidencePanel — plain-English "evidence for / against AI" breakdown.
   Turns the raw feature_vector scores into human-readable reasons so
   non-technical users understand WHY a verdict was reached. */
import React from 'react'

// Two phrasings per signal: `high` = evidence the content is AI-generated,
// `low` = evidence the content is authentic (a real photo/video).
const PHRASES = {
  frequency: {
    high: 'Unusual frequency spectrum unlike natural photos',
    low: 'Frequency spectrum looks like a natural photo',
  },
  statistical: {
    high: 'Pixel statistics look too clean to be a real photo',
    low: 'Pixel statistics match the noise of a real photo',
  },
  texture: {
    high: 'Textures are unnaturally smooth or repetitive',
    low: 'Textures vary naturally like a real photo',
  },
  srm: {
    high: 'Noise fingerprint matches AI-generated images',
    low: 'Noise fingerprint is consistent with a real camera',
  },
  color: {
    high: 'Colour distribution is unusual for a real photo',
    low: 'Colours are distributed like a real photo',
  },
  metadata: {
    high: 'No camera information found in the file',
    low: 'Contains camera metadata typical of real photos',
  },
  face: {
    high: 'Facial features show AI artifacts',
    low: 'Facial features look natural',
  },
  jpeg_ghost: {
    high: 'Compression traces suggest the image was AI-generated or edited',
    low: 'Compression traces are consistent with an original photo',
  },
  patch: {
    high: 'Repeated image patches typical of AI generation',
    low: 'No tell-tale repeated patches found',
  },
  ela: {
    high: 'Error-level analysis reveals inconsistent editing',
    low: 'Error-level analysis is uniform, as expected for an original',
  },
  gan_fingerprint: {
    high: 'Frequency patterns match known AI generator fingerprints',
    low: 'No known AI generator fingerprint detected',
  },
  diffusion_artifacts: {
    high: 'Tell-tale artifacts left by AI image generators',
    low: 'No diffusion-model artifacts detected',
  },
  noise_map: {
    high: 'Noise pattern is too uniform — typical of AI',
    low: 'Noise pattern varies naturally across the image',
  },
  prnu: {
    high: 'Missing camera sensor noise fingerprint',
    low: 'Camera sensor noise fingerprint is present',
  },
  copy_move: {
    high: 'Duplicated regions detected (possible manipulation)',
    low: 'No duplicated or cloned regions detected',
  },
}

const AI_THRESHOLD = 0.45 // score >= this => evidence for AI
const AUTHENTIC_THRESHOLD = 0.2 // score <= this => evidence for authentic
const MAX_ITEMS = 5

function pct(score) {
  return `${Math.round(Math.max(0, Math.min(1, score)) * 100)}%`
}

function EvidenceList({ title, items, dotColor, emptyText }) {
  return (
    <div>
      <p className="text-xs font-medium text-gray-400 mb-2">{title}</p>
      {items.length === 0 ? (
        <p className="text-xs text-gray-600">{emptyText}</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item.key} className="flex items-center gap-3">
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ background: dotColor }}
                aria-hidden="true"
              />
              <span className="flex-1 min-w-0 text-sm text-gray-300">{item.phrase}</span>
              <span className="text-xs font-mono text-gray-500 flex-shrink-0">{pct(item.score)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function EvidencePanel({ result }) {
  const featureVector = result?.feature_vector
  if (!featureVector || Object.keys(featureVector).length === 0) return null

  const forAI = []
  const forAuthentic = []

  for (const [key, raw] of Object.entries(featureVector)) {
    const phrases = PHRASES[key]
    if (!phrases) continue // skip unknown signals
    const score = Number(raw)
    if (!Number.isFinite(score)) continue

    if (score >= AI_THRESHOLD) {
      forAI.push({ key, score, phrase: phrases.high })
    } else if (score <= AUTHENTIC_THRESHOLD) {
      // For authentic evidence, lower score = stronger signal, so we rank by
      // how far below the threshold it sits (1 - score) when sorting.
      forAuthentic.push({ key, score, phrase: phrases.low })
    }
    // in-between scores are inconclusive and intentionally omitted
  }

  // Most significant first: AI evidence by highest score,
  // authentic evidence by lowest score (most clearly authentic).
  forAI.sort((a, b) => b.score - a.score)
  forAuthentic.sort((a, b) => a.score - b.score)

  const topForAI = forAI.slice(0, MAX_ITEMS)
  const topForAuthentic = forAuthentic.slice(0, MAX_ITEMS)

  // Nothing conclusive either way — render nothing rather than an empty shell.
  if (topForAI.length === 0 && topForAuthentic.length === 0) return null

  return (
    <div className="px-6 py-4 border-t border-gray-800/50 bg-gray-900/40">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
        Evidence breakdown
      </p>
      <div className="space-y-5">
        <EvidenceList
          title="Evidence suggesting AI"
          items={topForAI}
          dotColor="#ef4444"
          emptyText="No strong signs of AI generation."
        />
        <EvidenceList
          title="Evidence suggesting authentic"
          items={topForAuthentic}
          dotColor="#22c55e"
          emptyText="No strong signs of a genuine photo."
        />
      </div>
      <p className="text-xs text-gray-600 mt-4">
        Based on the strongest signals only. Inconclusive signals are not shown.
      </p>
    </div>
  )
}
