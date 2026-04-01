import React, { useState } from 'react'
import DetailedStats from './DetailedStats'

function getConfidencePhrase(confidence, isAI) {
  const subject = isAI ? 'AI-generated' : 'authentic'
  if (confidence >= 85) return `We're very confident this is ${subject}`
  if (confidence >= 65) return `We're fairly confident this is ${subject}`
  if (confidence >= 40) return 'We have some concerns about this content'
  return "We're not certain \u2014 treat with caution"
}

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
  const [showDetails, setShowDetails] = useState(false)

  if (!result) return null

  const isAI = result.verdict === 'AI-Generated'
  const confidence = result.confidence || 0
  const d = result.details || {}

  return (
    <div className="space-y-4">
      {/* ============================================ */}
      {/* LAYER 1 — THE VERDICT (always visible)       */}
      {/* ============================================ */}
      <div className={`rounded-2xl overflow-hidden border ${
        isAI ? 'border-red-500/50 shadow-lg shadow-red-500/10' : 'border-green-500/50 shadow-lg shadow-green-500/10'
      }`}>
        {/* Verdict Banner */}
        <div className={`px-6 py-8 text-center ${
          isAI ? 'bg-red-500/10' : 'bg-green-500/10'
        }`}>
          <p className={`text-4xl md:text-5xl font-bold mb-3 ${
            isAI ? 'text-red-400' : 'text-green-400'
          }`}>
            {isAI ? '\u26a0\ufe0f Likely AI-Generated' : '\u2713 Looks Authentic'}
          </p>
          <p className={`text-lg md:text-xl ${
            isAI ? 'text-red-300/80' : 'text-green-300/80'
          }`}>
            {getConfidencePhrase(confidence, isAI)}
          </p>
        </div>

        {/* Explanation */}
        {result.explanation && (
          <div className="px-6 py-5 border-t border-gray-800/50 bg-gray-900/60">
            <p className="text-gray-300 text-base leading-relaxed">
              {result.explanation}
            </p>
          </div>
        )}

        {/* What should I do? */}
        <div className="px-6 py-5 border-t border-gray-800/50 bg-gray-900/80">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
            What should I do?
          </h3>
          {isAI ? (
            <ul className="space-y-2 text-sm text-gray-400">
              <li className="flex items-start gap-2">
                <span className="text-red-400 mt-0.5 shrink-0">&#x2022;</span>
                <span><strong className="text-gray-300">Don't share this content</strong> until you've verified it from a trusted source</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-400 mt-0.5 shrink-0">&#x2022;</span>
                <span><strong className="text-gray-300">Don't send money or personal information</strong> based on what you see in this content</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-400 mt-0.5 shrink-0">&#x2022;</span>
                <span>If you suspect a scam, <strong className="text-gray-300">report it to Action Fraud (UK)</strong> at actionfraud.police.uk</span>
              </li>
            </ul>
          ) : (
            <ul className="space-y-2 text-sm text-gray-400">
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-0.5 shrink-0">&#x2022;</span>
                <span>This content appears genuine, but <strong className="text-gray-300">always verify important claims</strong> through official sources</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-0.5 shrink-0">&#x2022;</span>
                <span>No detection tool is 100% accurate — <strong className="text-gray-300">use your own judgement</strong> alongside this result</span>
              </li>
            </ul>
          )}
        </div>

        {/* File info footer */}
        <div className="px-6 py-3 bg-gray-900/50 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500">
          <span>{result.file_type === 'video' ? 'Video' : 'Image'} &middot; {result.file_size_mb} MB</span>
          <span className={result.detection_mode === 'ml_ensemble' ? 'text-green-500' : 'text-yellow-500'}>
            {result.detection_mode === 'ml_ensemble' ? 'ML + Heuristic' : 'Heuristic Only'}
          </span>
          <span>Analysed in {result.processing_time_seconds}s</span>
        </div>
      </div>

      {/* ============================================ */}
      {/* TOGGLE BUTTON                                */}
      {/* ============================================ */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-900/50 border border-gray-800 rounded-xl text-sm text-gray-400 hover:text-gray-200 hover:border-gray-700 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <span>{showDetails ? 'Hide technical details' : 'Show technical details'}</span>
        <span className="text-xs text-gray-600">(for researchers and advanced users)</span>
        <svg className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* ============================================ */}
      {/* LAYER 2 — TECHNICAL DETAILS (collapsed)      */}
      {/* ============================================ */}
      {showDetails && (
        <div className={`rounded-2xl border border-gray-800 bg-gray-900/80 overflow-hidden`}>
          <div className="px-6 py-4 border-b border-gray-800/50 bg-gray-900/50">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
              For researchers and advanced users
            </p>
          </div>

          {/* Confidence & Ensemble Score */}
          <div className="px-6 pt-5 pb-3">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400">Confidence</span>
              <span className={`text-2xl font-bold font-mono ${isAI ? 'text-red-400' : 'text-green-400'}`}>{confidence}%</span>
            </div>
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
              <ScoreBar label="Frequency (DCT + FFT)" score={d.frequency_analysis.ai_score} color={scoreColor(d.frequency_analysis.ai_score)} compact />
            )}
            {d.statistical_analysis && (
              <ScoreBar label="Statistical (Noise + Distribution)" score={d.statistical_analysis.ai_score} color={scoreColor(d.statistical_analysis.ai_score)} compact />
            )}
            {d.texture_analysis && (
              <ScoreBar label="Texture (Edges + Variance)" score={d.texture_analysis.ai_score} color={scoreColor(d.texture_analysis.ai_score)} compact />
            )}
            {d.srm_analysis && (
              <ScoreBar label="SRM Noise Fingerprint" score={d.srm_analysis.ai_score} color={scoreColor(d.srm_analysis.ai_score)} compact />
            )}
            {d.color_analysis && (
              <ScoreBar label="Color Space (LAB + YCbCr)" score={d.color_analysis.ai_score} color={scoreColor(d.color_analysis.ai_score)} compact />
            )}
            {d.face_analysis && (
              <ScoreBar label={`Face Analysis (${d.face_analysis.faces_found} face${d.face_analysis.faces_found !== 1 ? 's' : ''})`} score={d.face_analysis.ai_score} color={scoreColor(d.face_analysis.ai_score)} compact />
            )}
            {d.metadata_analysis && (
              <ScoreBar label="Metadata Analysis" score={d.metadata_analysis.ai_score} color={scoreColor(d.metadata_analysis.ai_score)} compact />
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
              {d.color_analysis?.chroma_gradient != null && (
                <DetailChip label="Chroma Grad." value={d.color_analysis.chroma_gradient} />
              )}
              {d.color_analysis?.cbcr_correlation != null && (
                <DetailChip label="CbCr Corr." value={d.color_analysis.cbcr_correlation} />
              )}
              {d.face_analysis?.face_details?.length > 0 && d.face_analysis.face_details.map((f, i) => (
                <React.Fragment key={`face-${i}`}>
                  {f.skin_noise != null && <DetailChip label={`Face${i+1} Skin`} value={f.skin_noise} />}
                  {f.symmetry_diff != null && <DetailChip label={`Face${i+1} Symm`} value={f.symmetry_diff} />}
                </React.Fragment>
              ))}
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

          {/* Heatmap overlay (image) */}
          {result.heatmap && (
            <div className="px-6 py-3 border-t border-gray-800/50">
              <p className="text-xs font-medium text-indigo-400 uppercase tracking-wider mb-2">Artifact Heatmap</p>
              <div className="rounded-lg overflow-hidden bg-gray-800">
                <img
                  src={`data:image/jpeg;base64,${result.heatmap}`}
                  alt="Artifact heatmap overlay"
                  className="w-full h-auto"
                />
              </div>
              <p className="text-xs text-gray-600 mt-1">Green = natural, Yellow = suspicious, Red = likely AI artifacts</p>
            </div>
          )}

          {/* Advanced Video Analysis */}
          {result.advanced_analysis && (
            <div className="px-6 py-3 border-t border-gray-800/50">
              <p className="text-xs font-medium text-purple-400 uppercase tracking-wider mb-2">Advanced Deepfake Detection</p>
              <ScoreBar
                label="Combined Advanced Score"
                score={result.advanced_analysis.combined_score}
                color={scoreColor(result.advanced_analysis.combined_score)}
                compact
              />
              <div className="mt-2 space-y-1.5">
                {result.advanced_analysis.physiological && (
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Physiological (rPPG)</span>
                    <span className={`font-mono ${result.advanced_analysis.physiological.ai_probability > 0.15 ? 'text-yellow-400' : 'text-green-400'}`}>
                      Signal: {result.advanced_analysis.physiological.signal_strength}
                    </span>
                  </div>
                )}
                {result.advanced_analysis.identity_consistency && (
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Identity Consistency</span>
                    <span className={`font-mono ${result.advanced_analysis.identity_consistency.ai_probability > 0.15 ? 'text-yellow-400' : 'text-green-400'}`}>
                      Score: {result.advanced_analysis.identity_consistency.consistency_score || 'N/A'}
                    </span>
                  </div>
                )}
                {result.advanced_analysis.bg_fg_coherence && (
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">BG/FG Coherence</span>
                    <span className={`font-mono ${result.advanced_analysis.bg_fg_coherence.ai_probability > 0.15 ? 'text-yellow-400' : 'text-green-400'}`}>
                      {(result.advanced_analysis.bg_fg_coherence.ai_probability * 100).toFixed(1)}% AI
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

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
            <div className="px-6 py-3 border-t border-gray-800/50 grid grid-cols-2 md:grid-cols-4 gap-3 text-center text-xs text-gray-500">
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

          {/* Detailed raw statistics */}
          <div className="px-6 py-3 border-t border-gray-800/50">
            <DetailedStats result={result} />
          </div>
        </div>
      )}
    </div>
  )
}
