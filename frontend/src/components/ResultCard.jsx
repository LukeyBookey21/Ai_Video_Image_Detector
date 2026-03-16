import React from 'react'

function ScoreBar({ label, score, color }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-gray-400">{label}</span>
        <span className={`font-mono font-bold ${color}`}>{score}%</span>
      </div>
      <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ease-out ${
            score > 70 ? 'bg-red-500' : score > 40 ? 'bg-yellow-500' : 'bg-green-500'
          }`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
    </div>
  )
}

function scoreColor(score) {
  return score > 50 ? 'text-red-400' : 'text-green-400'
}

export default function ResultCard({ result }) {
  if (!result) return null

  const isAI = result.verdict === 'AI-Generated'
  const borderColor = isAI ? 'border-red-500/50' : 'border-green-500/50'
  const bgGlow = isAI ? 'shadow-red-500/10' : 'shadow-green-500/10'
  const verdictColor = isAI ? 'text-red-400' : 'text-green-400'
  const verdictBg = isAI ? 'bg-red-500/10' : 'bg-green-500/10'

  const d = result.details || {}

  return (
    <div className={`rounded-2xl border ${borderColor} bg-gray-900/80 shadow-lg ${bgGlow} overflow-hidden`}>
      {/* Verdict Banner */}
      <div className={`px-6 py-5 ${verdictBg}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400 mb-1">Verdict</p>
            <h2 className={`text-2xl font-bold ${verdictColor}`}>{result.verdict}</h2>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-400 mb-1">Confidence</p>
            <p className={`text-3xl font-bold font-mono ${verdictColor}`}>{result.confidence}%</p>
          </div>
        </div>
      </div>

      {/* Scores */}
      <div className="px-6 py-5 space-y-4">
        <ScoreBar
          label="AI Probability (Ensemble)"
          score={result.ai_probability}
          color={scoreColor(result.ai_probability)}
        />

        {d.frequency_analysis && (
          <ScoreBar
            label="Frequency Analysis (DCT + FFT)"
            score={d.frequency_analysis.ai_score}
            color={scoreColor(d.frequency_analysis.ai_score)}
          />
        )}

        {d.statistical_analysis && (
          <ScoreBar
            label="Statistical Analysis (Noise + Distribution)"
            score={d.statistical_analysis.ai_score}
            color={scoreColor(d.statistical_analysis.ai_score)}
          />
        )}

        {d.texture_analysis && (
          <ScoreBar
            label="Texture Analysis (Edges + Variance)"
            score={d.texture_analysis.ai_score}
            color={scoreColor(d.texture_analysis.ai_score)}
          />
        )}

        {/* Detail chips */}
        {d.frequency_analysis && (
          <div className="flex flex-wrap gap-2 pt-2">
            {d.frequency_analysis.spectral_flatness != null && (
              <span className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400">
                Spectral Flatness: {d.frequency_analysis.spectral_flatness}
              </span>
            )}
            {d.frequency_analysis.power_law_slope != null && (
              <span className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400">
                Power Law Slope: {d.frequency_analysis.power_law_slope}
              </span>
            )}
            {d.statistical_analysis?.noise_level != null && (
              <span className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400">
                Noise Level: {d.statistical_analysis.noise_level}
              </span>
            )}
            {d.texture_analysis?.edge_density != null && (
              <span className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400">
                Edge Density: {d.texture_analysis.edge_density}
              </span>
            )}
          </div>
        )}

        {/* Video frame analysis */}
        {result.frame_analysis && (
          <div className="mt-4 pt-4 border-t border-gray-800">
            <h3 className="text-sm font-medium text-gray-300 mb-3">Frame-by-Frame Analysis</h3>
            <div className="grid grid-cols-3 gap-3 text-center text-sm">
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-gray-500">Average</p>
                <p className="text-lg font-mono font-bold text-white">{result.frame_analysis.average_ai_score}%</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-gray-500">Highest</p>
                <p className="text-lg font-mono font-bold text-red-400">{result.frame_analysis.max_ai_score}%</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-gray-500">Lowest</p>
                <p className="text-lg font-mono font-bold text-green-400">{result.frame_analysis.min_ai_score}%</p>
              </div>
            </div>

            {/* Per-frame breakdown */}
            <div className="mt-3 flex gap-1">
              {result.frame_analysis.per_frame?.map((frame, i) => (
                <div
                  key={i}
                  className="flex-1 group relative"
                  title={`Frame ${i + 1}: ${frame.ai_probability}% AI`}
                >
                  <div
                    className={`h-8 rounded-sm ${
                      frame.ai_probability > 70 ? 'bg-red-500' :
                      frame.ai_probability > 40 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ opacity: 0.3 + (frame.ai_probability / 100) * 0.7 }}
                  />
                  <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-800 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                    {frame.ai_probability}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Video info */}
        {result.video_info && (
          <div className="mt-3 pt-3 border-t border-gray-800 grid grid-cols-3 gap-3 text-center text-xs text-gray-500">
            <div>
              <p className="text-gray-300 font-mono">{result.video_info.duration_seconds}s</p>
              <p>Duration</p>
            </div>
            <div>
              <p className="text-gray-300 font-mono">{result.video_info.fps}</p>
              <p>FPS</p>
            </div>
            <div>
              <p className="text-gray-300 font-mono">{result.video_info.frames_analyzed}</p>
              <p>Frames Analyzed</p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-6 py-3 bg-gray-900/50 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500">
        <span>{result.file_type === 'video' ? 'Video' : 'Image'} analysis</span>
        <span>{result.processing_time_seconds}s</span>
        <span>{result.file_size_mb} MB</span>
      </div>
    </div>
  )
}
