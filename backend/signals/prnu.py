"""
PRNU — Photo Response Non-Uniformity Analysis

Real cameras leave a fixed-pattern noise unique to each sensor (PRNU).
AI images have random/flat residual noise with no periodic structure.

Method:
1. Extract noise residual (image minus Wiener-filtered version)
2. Check for spatial periodicity in residuals via autocorrelation
3. Real camera residuals show periodic structure; AI residuals don't
"""

import numpy as np
from PIL import Image
from scipy.fft import fft2
from scipy.ndimage import uniform_filter


def analyze(image: Image.Image) -> dict:
    """Analyze PRNU characteristics to distinguish camera vs AI."""
    try:
        gray = np.array(image.convert("L").resize((256, 256)), dtype=np.float64)
        h, w = gray.shape

        # Wiener-like denoising (simplified: local mean filter)
        denoised = uniform_filter(gray, size=3)
        residual = gray - denoised

        # Compute autocorrelation of residual noise
        residual_norm = residual - np.mean(residual)
        residual_std = np.std(residual_norm)
        if residual_std < 1e-10:
            return {"signal_name": "prnu", "score": 0.1, "confidence": 0.3, "details": {"residual_energy": 0.0}}

        residual_norm /= residual_std

        # FFT-based autocorrelation
        power = np.abs(fft2(residual_norm)) ** 2
        autocorr = np.real(np.fft.ifft2(power))
        autocorr = np.fft.fftshift(autocorr)
        cy, cx = h // 2, w // 2
        autocorr /= autocorr[cy, cx] + 1e-10

        # Check for periodic structure
        # Sample autocorrelation at various offsets
        periodic_peaks = []
        for dy in range(2, min(32, h // 4)):
            for dx in range(2, min(32, w // 4)):
                if cy + dy < h and cx + dx < w:
                    val = autocorr[cy + dy, cx + dx]
                    if val > 0.05:
                        periodic_peaks.append(val)

        has_periodic = len(periodic_peaks) > 5
        peak_strength = np.mean(periodic_peaks) if periodic_peaks else 0.0

        # Residual energy analysis
        residual_energy = np.mean(np.abs(residual))

        # Spectral flatness of residual
        fft_residual = np.abs(fft2(residual_norm))
        flat_vals = fft_residual.flatten()
        flat_vals = flat_vals[flat_vals > 0]
        geo_mean = np.exp(np.mean(np.log(flat_vals + 1e-10)))
        arith_mean = np.mean(flat_vals)
        spectral_flatness = geo_mean / (arith_mean + 1e-10)

        scores = []

        # No periodic structure in residuals = likely AI
        if not has_periodic and residual_energy < 5:
            scores.append(0.12)

        # Very flat residual spectrum = AI (no sensor-specific patterns)
        if spectral_flatness > 0.8:
            scores.append(0.08)
        elif spectral_flatness > 0.7:
            scores.append(0.04)

        # Has periodic structure = likely real camera
        if has_periodic and peak_strength > 0.1:
            scores.append(-0.05)  # Evidence of real

        score = max(min(sum(scores), 1.0), 0.0)
        confidence = min(abs(score) * 2, 1.0)

        return {
            "signal_name": "prnu",
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "details": {
                "residual_energy": round(float(residual_energy), 4),
                "spectral_flatness": round(float(spectral_flatness), 4),
                "periodic_peaks": len(periodic_peaks),
                "has_periodic_structure": has_periodic,
            },
        }
    except Exception:
        return {"signal_name": "prnu", "score": 0.0, "confidence": 0.0, "details": {}}
