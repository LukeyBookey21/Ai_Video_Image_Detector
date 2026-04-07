"""
GAN Fingerprint Detector

Detects checkerboard artifacts at Nyquist frequency — a known signature
of GAN upsampling layers (transposed convolution with stride 2).

Method:
1. 2D FFT of image → magnitude spectrum
2. Check for energy peaks at (N/2, N/2) and sub-harmonics
3. Autocorrelation check for periodic grid patterns
4. Ratio of peak energy to average energy = fingerprint strength
"""

import numpy as np
from PIL import Image
from scipy.fft import fft2


def analyze(image: Image.Image) -> dict:
    """Detect GAN upsampling fingerprints in the frequency domain."""
    try:
        gray = np.array(image.convert("L").resize((256, 256)), dtype=np.float64)
        h, w = gray.shape

        # 2D FFT → magnitude spectrum
        fft_result = fft2(gray)
        magnitude = np.abs(np.fft.fftshift(fft_result))
        log_mag = np.log1p(magnitude)

        # Check Nyquist frequency peaks (N/2, N/2) — GAN checkerboard artifact
        cy, cx = h // 2, w // 2

        # Peak at Nyquist (edges of spectrum)
        nyquist_energy = np.mean([
            magnitude[0, cx],      # top center
            magnitude[-1, cx],     # bottom center
            magnitude[cy, 0],      # left center
            magnitude[cy, -1],     # right center
            magnitude[0, 0],       # corners
            magnitude[0, -1],
            magnitude[-1, 0],
            magnitude[-1, -1],
        ])

        # Average energy in mid-frequency band (avoiding DC and Nyquist)
        q = h // 4
        mid_band = magnitude[q:3*q, q:3*q]
        mid_energy = np.mean(mid_band)

        # Peak ratio — high ratio = GAN fingerprint
        peak_ratio = nyquist_energy / (mid_energy + 1e-10)

        # Sub-harmonic check (N/4, N/4 peaks — stride-4 artifacts)
        sub_points = [
            magnitude[q, cx], magnitude[3*q, cx],
            magnitude[cy, q], magnitude[cy, 3*q],
        ]
        sub_energy = np.mean(sub_points)
        sub_ratio = sub_energy / (mid_energy + 1e-10)

        # Autocorrelation for periodic grid patterns
        # Normalize image
        gray_norm = (gray - np.mean(gray)) / (np.std(gray) + 1e-10)
        # Compute autocorrelation via FFT
        power_spectrum = np.abs(fft2(gray_norm)) ** 2
        autocorr = np.real(np.fft.ifft2(power_spectrum))
        autocorr = np.fft.fftshift(autocorr)
        autocorr /= autocorr[cy, cx] + 1e-10  # Normalize by zero-lag

        # Check for periodic peaks (every 2 pixels = stride-2 GAN artifact)
        grid_peaks = []
        for offset in [2, 4, 8]:
            if cy + offset < h and cx + offset < w:
                val = autocorr[cy + offset, cx + offset]
                grid_peaks.append(val)

        grid_score = np.max(grid_peaks) if grid_peaks else 0.0
        grid_detected = grid_score > 0.3

        # Combine into final score
        scores = []
        if peak_ratio > 2.0:
            scores.append(0.25)
        elif peak_ratio > 1.5:
            scores.append(0.15)
        elif peak_ratio > 1.2:
            scores.append(0.08)

        if sub_ratio > 1.5:
            scores.append(0.15)

        if grid_detected:
            scores.append(0.20)

        score = min(sum(scores), 1.0)
        confidence = min(score * 1.5, 1.0)

        return {
            "signal_name": "gan_fingerprint",
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "details": {
                "peak_ratio": round(float(peak_ratio), 4),
                "sub_harmonic_ratio": round(float(sub_ratio), 4),
                "grid_score": round(float(grid_score), 4),
                "grid_detected": grid_detected,
            },
        }
    except Exception:
        return {"signal_name": "gan_fingerprint", "score": 0.0, "confidence": 0.0, "details": {}}
