import React, { useState } from 'react'

function StatRow({ label, value, unit, warn }) {
  return (
    <div className="flex justify-between py-1.5 border-b border-gray-800/50 last:border-0">
      <span className="text-gray-500 text-xs">{label}</span>
      <span className={`font-mono text-xs ${warn ? 'text-yellow-400' : 'text-gray-300'}`}>
        {value}{unit && <span className="text-gray-600 ml-0.5">{unit}</span>}
      </span>
    </div>
  )
}

function StatSection({ title, icon, children }) {
  return (
    <div className="bg-gray-800/30 rounded-lg p-3">
      <h4 className="text-xs font-medium text-gray-400 mb-2 flex items-center gap-1.5">
        <span className="text-indigo-400">{icon}</span> {title}
      </h4>
      <div className="space-y-0">{children}</div>
    </div>
  )
}

export default function DetailedStats({ result }) {
  const [expanded, setExpanded] = useState(false)

  if (!result?.details && !result?.advanced_analysis) return null

  const d = result.details || {}

  return (
    <div className="mt-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-900/50 border border-gray-800 rounded-xl text-sm text-gray-400 hover:text-gray-200 hover:border-gray-700 transition-colors"
      >
        <span className="flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Detailed Statistics & Raw Data
        </span>
        <svg className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* Frequency Analysis */}
          {d.frequency_analysis && (
            <StatSection title="Frequency Domain" icon="~">
              <StatRow label="AI Score" value={d.frequency_analysis.ai_score + '%'} />
              <StatRow label="Spectral Flatness" value={d.frequency_analysis.spectral_flatness} warn={d.frequency_analysis.spectral_flatness > 0.6} />
              <StatRow label="Power Law Slope" value={d.frequency_analysis.power_law_slope} warn={Math.abs(d.frequency_analysis.power_law_slope + 1.2) > 0.5} />
            </StatSection>
          )}

          {/* Statistical Analysis */}
          {d.statistical_analysis && (
            <StatSection title="Noise & Distribution" icon="#">
              <StatRow label="AI Score" value={d.statistical_analysis.ai_score + '%'} />
              <StatRow label="Noise Level (std)" value={d.statistical_analysis.noise_level} warn={d.statistical_analysis.noise_level < 3} />
              <StatRow label="Color Correlation" value={d.statistical_analysis.color_correlation} warn={d.statistical_analysis.color_correlation > 0.95} />
            </StatSection>
          )}

          {/* Texture Analysis */}
          {d.texture_analysis && (
            <StatSection title="Texture & Edges" icon="*">
              <StatRow label="AI Score" value={d.texture_analysis.ai_score + '%'} />
              <StatRow label="Edge Density" value={d.texture_analysis.edge_density} warn={d.texture_analysis.edge_density < 0.05} />
              <StatRow label="Local Variance" value={d.texture_analysis.local_variance} warn={d.texture_analysis.local_variance < 200} />
            </StatSection>
          )}

          {/* SRM Analysis */}
          {d.srm_analysis && (
            <StatSection title="SRM Noise Fingerprint" icon="$">
              <StatRow label="AI Score" value={d.srm_analysis.ai_score + '%'} />
              <StatRow label="Residual Std" value={d.srm_analysis.residual_std} warn={d.srm_analysis.residual_std < 2} />
              <StatRow label="Residual Kurtosis" value={d.srm_analysis.residual_kurtosis} warn={d.srm_analysis.residual_kurtosis > 10} />
            </StatSection>
          )}

          {/* Color Space Analysis */}
          {d.color_analysis && (
            <StatSection title="Color Space (LAB/YCbCr)" icon="C">
              <StatRow label="AI Score" value={d.color_analysis.ai_score + '%'} />
              <StatRow label="Chroma Gradient" value={d.color_analysis.chroma_gradient} warn={d.color_analysis.chroma_gradient < 1.0} />
              <StatRow label="Luma/Chroma Ratio" value={d.color_analysis.luma_chroma_ratio} warn={d.color_analysis.luma_chroma_ratio > 5} />
              <StatRow label="CbCr Correlation" value={d.color_analysis.cbcr_correlation} warn={Math.abs(d.color_analysis.cbcr_correlation) > 0.8} />
            </StatSection>
          )}

          {/* Face Analysis */}
          {d.face_analysis && (
            <StatSection title={`Face Analysis (${d.face_analysis.faces_found} found)`} icon="F">
              <StatRow label="AI Score" value={d.face_analysis.ai_score + '%'} />
              <StatRow label="Faces Found" value={d.face_analysis.faces_found} />
              {d.face_analysis.face_details?.map((face, i) => (
                <React.Fragment key={i}>
                  {face.symmetry_diff != null && (
                    <StatRow label={`Face ${i+1} Symmetry`} value={face.symmetry_diff} warn={face.symmetry_diff < 8} />
                  )}
                  {face.skin_noise != null && (
                    <StatRow label={`Face ${i+1} Skin Noise`} value={face.skin_noise} warn={face.skin_noise < 3} />
                  )}
                  {face.boundary_gradient != null && (
                    <StatRow label={`Face ${i+1} Boundary`} value={face.boundary_gradient} warn={face.boundary_gradient > 20} />
                  )}
                  {face.eyes_detected != null && (
                    <StatRow label={`Face ${i+1} Eyes`} value={face.eyes_detected} warn={face.eyes_detected < 2} />
                  )}
                </React.Fragment>
              ))}
            </StatSection>
          )}

          {/* Metadata */}
          {d.metadata_analysis && (
            <StatSection title="Metadata & Format" icon="i">
              <StatRow label="AI Score" value={d.metadata_analysis.ai_score + '%'} />
              <StatRow label="Dimensions" value={d.metadata_analysis.dimensions} />
              {d.metadata_analysis.flags?.map((flag, i) => (
                <StatRow key={i} label={`Flag ${i + 1}`} value={flag.replace(/_/g, ' ')} warn />
              ))}
              {(!d.metadata_analysis.flags || d.metadata_analysis.flags.length === 0) && (
                <StatRow label="Flags" value="none" />
              )}
            </StatSection>
          )}

          {/* ML Models */}
          {(d.ml_model_primary || d.ml_model_deepfake) && (
            <StatSection title="ML Model Predictions" icon="M">
              {d.ml_model_primary && (
                <>
                  <StatRow label="SDXL Detector" value={d.ml_model_primary.ai_score + '%'} warn={d.ml_model_primary.ai_score > 50} />
                  <StatRow label="Model" value={d.ml_model_primary.model} />
                </>
              )}
              {d.ml_model_deepfake && (
                <>
                  <StatRow label="Deepfake Detector" value={d.ml_model_deepfake.ai_score + '%'} warn={d.ml_model_deepfake.ai_score > 50} />
                  <StatRow label="Model" value={d.ml_model_deepfake.model} />
                </>
              )}
            </StatSection>
          )}

          {/* Ensemble Info */}
          <StatSection title="Ensemble Configuration" icon="=">
            <StatRow label="Detection Mode" value={d.detection_mode === 'ml_ensemble' ? 'ML + Heuristic' : 'Heuristic Only'} />
            {d.ensemble_weights && Object.entries(d.ensemble_weights).map(([key, weight]) => (
              <StatRow key={key} label={`Weight: ${key}`} value={(weight * 100).toFixed(0) + '%'} />
            ))}
            <StatRow label="Processing Time" value={result.processing_time_seconds} unit="s" />
            <StatRow label="File Size" value={result.file_size_mb} unit="MB" />
          </StatSection>

          {/* Temporal (video only) */}
          {result.temporal_analysis && (
            <StatSection title="Temporal Consistency" icon="T">
              <StatRow label="Temporal AI Score" value={result.temporal_analysis.temporal_ai_score + '%'} warn={result.temporal_analysis.temporal_ai_score > 30} />
              <StatRow label="Optical Flow Var." value={result.temporal_analysis.flow_consistency} />
              <StatRow label="Noise Consistency" value={result.temporal_analysis.noise_consistency} warn={result.temporal_analysis.noise_consistency < 0.1} />
            </StatSection>
          )}

          {/* Advanced Video Analysis */}
          {result.advanced_analysis && (
            <StatSection title="Advanced Deepfake Detection" icon="D">
              <StatRow label="Combined Score" value={result.advanced_analysis.combined_score + '%'} warn={result.advanced_analysis.combined_score > 30} />
              {result.advanced_analysis.physiological && (
                <>
                  <StatRow label="rPPG Signal Strength" value={result.advanced_analysis.physiological.signal_strength} warn={result.advanced_analysis.physiological.signal_strength < 0.3} />
                  <StatRow label="Physio AI Prob." value={(result.advanced_analysis.physiological.ai_probability * 100).toFixed(1) + '%'} warn={result.advanced_analysis.physiological.ai_probability > 0.15} />
                </>
              )}
              {result.advanced_analysis.identity_consistency && (
                <>
                  <StatRow label="Identity Score" value={result.advanced_analysis.identity_consistency.consistency_score} />
                  <StatRow label="Identity AI Prob." value={(result.advanced_analysis.identity_consistency.ai_probability * 100).toFixed(1) + '%'} warn={result.advanced_analysis.identity_consistency.ai_probability > 0.15} />
                  {result.advanced_analysis.identity_consistency.frames_with_faces != null && (
                    <StatRow label="Frames w/ Faces" value={result.advanced_analysis.identity_consistency.frames_with_faces} />
                  )}
                </>
              )}
              {result.advanced_analysis.bg_fg_coherence && (
                <>
                  <StatRow label="BG/FG AI Prob." value={(result.advanced_analysis.bg_fg_coherence.ai_probability * 100).toFixed(1) + '%'} warn={result.advanced_analysis.bg_fg_coherence.ai_probability > 0.15} />
                  <StatRow label="BG/FG Frames" value={result.advanced_analysis.bg_fg_coherence.frames_analyzed} />
                </>
              )}
            </StatSection>
          )}
        </div>
      )}
    </div>
  )
}
