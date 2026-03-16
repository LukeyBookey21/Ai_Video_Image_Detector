import React from 'react'

function ScoreBar({ label, score, color, compact }) {
  return (
    <div className={compact ? "space-y-0.5" : "space-y-1"}>
      <div className="flex justify-between text-sm">
        <span className="text-gray-400">{label}</span>
        <span className={`font-mono font-bold ${color}`}>{score}%</span>
      </div>
      <div className={`w-full ${compact ? 'h-1.5' : 'h-2'} bg-gray-800 rounded-full overflow-hidden`}>
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
  return score > 60 ? 'text-red-400' : score > 40 ? 'text-yellow-400' : 'text-green-400'
}

function DetailChip({ label, value }) {
  return (
    <span className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400">
      {label}: <span className="text-gray-300">{value}</span>
    </span>
  )
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

      {/* Main Score */}
      <div className="px-6 pt-5 pb-3">
        <ScoreBar
          label="AI Probability (Ensemble)"
          score={result.ai_probability}
          color={scoreColor(result.ai_probability)}
        />
      </div>

      {/* ML Models */}
      {(d.ml_model_primary || d.ml_model_deepfake) && (
        <div className="px-6 py-3 space-y-2 border-t border-gray-800/50">
          <p className="text-xs font-medium text-indigo-400 uppercase tracking-wider">ML Models</p>
          {d.ml_model_primary && (
            <ScoreBar
              label="SDXL Detector (ViT)"
              score={d.ml_model_primary.ai_score}
              color={scoreColor(d.ml_model_primary.ai_score)}
              compact
            />
          )}
          {d.ml_model_deepfake && (
            <ScoreBar
              label="Deepfake Detector (SigLIP)"
              score={d.ml_model_deepfake.ai_score}
              color={scoreColor(d.ml_model_deepfake.ai_score)}
              compact
            />
          )}
        </div>
      )}

      {/* Heuristic Signals */}
      <div className="px-6 py-3 space-y-2 border-t border-gray-800/50">
        <p className="text-xs font-medium text-indigo-400 uppercase tracking-wider">Forensic Analysis</p>

        {d.frequency_analysis && (
          <ScoreBar
            label="Frequency (DCT + FFT)"
            score={d.frequency_analysis.ai_score}
            color={scoreColor(d.frequency_analysis.ai_score)}
            compact
          />
        )}

        {d.statistical_analysis && (
          <ScoreBar
            label="Statistical (Noise + Distribution)"
            score={d.statistical_analysis.ai_score}
            color={scoreColor(d.statistical_analysis.ai_score)}
            compact
          />
        )}

        {d.texture_analysis && (
          <ScoreBar
            label="Texture (Edges + Variance)"
            score={d.texture_analysis.ai_score}
            color={scoreColor(d.texture_analysis.ai_score)}
            compact
          />
        )}

        {d.srm_analysis && (
          <ScoreBar
            label="SRM Noise Fingerprint"
            score={d.srm_analysis.ai_score}
            color={scoreColor(d.srm_analysis.ai_score)}
            compact
          />
        )}

        {d.metadata_analysis && (
          <ScoreBar
            label="Metadata Analysis"
            score={d.metadata_analysis.ai_score}
            color={scoreColor(d.metadata_analysis.ai_score)}
            compact
          />
        )}
      </div>

      {/* Detail chips */}
      <div className="px-6 py-3 border-t border-gray-800/50">
        <div className="flex flex-wrap gap-1.5">
          {d.frequency_analysis?.spectral_flatness != null && (
            <DetailChip label="Spectral Flat." value={d.frequency_analysis.spectral_flatness} />
          )}
          {d.frequency_analysis?.power_law_slope != null && (
            <DetailChip label="Power Slope" value={d.frequency_analysis.power_law_slope} />
          )}
          {d.statistical_analysis?.noise_level != null && (
            <DetailChip label="Noise" value={d.statistical_analysis.noise_level} />
          )}
          {d.srm_analysis?.residual_std != null && (
            <DetailChip label="SRM Residual" value={d.srm_analysis.residual_std} />
          )}
          {d.texture_analysis?.edge_density != null && (
            <DetailChip label="Edge Density" value={d.texture_analysis.edge_density} />
          )}
          {d.metadata_analysis?.dimensions && (
            <DetailChip label="Dimensions" value={d.metadata_analysis.dimensions} />
          )}
          {d.metadata_analysis?.flags?.length > 0 && d.metadata_analysis.flags.map((flag, i) => (
            <span key={i} className="px-2 py-1 bg-yellow-900/30 border border-yellow-800/50 rounded text-xs text-yellow-400">
              {flag.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      </div>

      {/* Temporal analysis (video) */}
      {result.temporal_analysis && (
        <div className="px-6 py-3 border-t border-gray-800/50">
          <p className="text-xs font-medium text-indigo-400 uppercase tracking-wider mb-2">Temporal Analysis</p>
          <ScoreBar
            label="Temporal Consistency Score"
            score={result.temporal_analysis.temporal_ai_score}
            color={scoreColor(result.temporal_analysis.temporal_ai_score)}
            compact
          />
          <div className="flex gap-1.5 mt-2">
            <DetailChip label="Flow Consistency" value={result.temporal_analysis.flow_consistency} />
            <DetailChip label="Noise Consistency" value={result.temporal_analysis.noise_consistency} />
          </div>
        </div>
      )}

      {/* Video frame analysis */}
      {result.frame_analysis && (
        <div className="px-6 py-3 border-t border-gray-800/50">
          <h3 className="text-xs font-medium text-indigo-400 uppercase tracking-wider mb-3">Frame Analysis</h3>
          <div className="grid grid-cols-3 gap-3 text-center text-sm">
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-gray-500 text-xs">Average</p>
              <p className="text-lg font-mono font-bold text-white">{result.frame_analysis.average_ai_score}%</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-gray-500 text-xs">Highest</p>
              <p className="text-lg font-mono font-bold text-red-400">{result.frame_analysis.max_ai_score}%</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-gray-500 text-xs">Lowest</p>
              <p className="text-lg font-mono font-bold text-green-400">{result.frame_analysis.min_ai_score}%</p>
            </div>
          </div>

          {/* Frame heatmap */}
          <div className="mt-3 flex gap-0.5">
            {result.frame_analysis.per_frame?.map((frame, i) => (
              <div
                key={i}
                className="flex-1 group relative"
                title={`Frame ${i + 1}: ${frame.ai_probability}% AI`}
              >
                <div
                  className={`h-8 rounded-sm transition-all ${
                    frame.ai_probability > 70 ? 'bg-red-500' :
                    frame.ai_probability > 40 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ opacity: 0.3 + (frame.ai_probability / 100) * 0.7 }}
                />
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-800 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                  F{i + 1}: {frame.ai_probability}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Video info */}
      {result.video_info && (
        <div className="px-6 py-3 border-t border-gray-800/50 grid grid-cols-4 gap-3 text-center text-xs text-gray-500">
          <div>
            <p className="text-gray-300 font-mono">{result.video_info.duration_seconds}s</p>
            <p>Duration</p>
          </div>
          <div>
            <p className="text-gray-300 font-mono">{result.video_info.fps}</p>
            <p>FPS</p>
          </div>
          <div>
            <p className="text-gray-300 font-mono">{result.video_info.resolution}</p>
            <p>Resolution</p>
          </div>
          <div>
            <p className="text-gray-300 font-mono">{result.video_info.frames_analyzed}</p>
            <p>Frames</p>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="px-6 py-3 bg-gray-900/50 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500">
        <span>{result.file_type === 'video' ? 'Video' : 'Image'}</span>
        <span className={result.detection_mode === 'ml_ensemble' ? 'text-green-500' : 'text-yellow-500'}>
          {result.detection_mode === 'ml_ensemble' ? 'ML + Heuristic' : 'Heuristic Only'}
        </span>
        <span>{result.processing_time_seconds}s</span>
        <span>{result.file_size_mb} MB</span>
      </div>
    </div>
  )
}
