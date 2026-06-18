"""
Azimuthal / Radial Power Spectrum Detector

Based on Durall et al., "Watch your Up-Convolution: CNN Based Generative Deep
Neural Networks are Failing to Reproduce Spectral Distributions" (CVPR 2020).

Real photographs have a smoothly-decaying radial power spectrum that follows a
roughly 1/f^a power law (a steep negative slope in log-log space). GAN- and
diffusion-generated images show characteristic deviations introduced by their
up-convolution (transposed-convolution / interpolate-then-conv) layers:
  * spectral peaks at high frequencies,
  * flatter high-frequency tails (slope closer to 0),
  * periodic spikes in the radial profile from the upsampling grid.

Method:
1. Grayscale, resize to 256x256.
2. 2D FFT -> shift -> magnitude -> log power spectrum.
3. Radially (azimuthally) average the power over each integer-radius ring,
   giving a 1D radial power profile (length ~128).
4. Fit a line to the mid-to-high frequency range of the log-log profile and
   measure the decay slope. Real photos: steep negative slope. AI: flat slope.
5. Measure the high-frequency energy ratio (outer 25% of radii vs inner 25%).
6. Detect periodic spikes (peaks rising above a local mean) -> up-conv artifacts.
7. Combine into an additive score, capped at 1.0.
"""

import numpy as np
from PIL import Image
from scipy.fft import fft2


def _radial_profile(power: np.ndarray) -> np.ndarray:
    """Azimuthally average a 2D (already fft-shifted) array over integer-radius
    rings centered on the spectrum, returning a 1D radial power profile."""
    h, w = power.shape
    cy, cx = h // 2, w // 2

    y, x = np.indices((h, w))
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    r = r.astype(np.int64)

    # Sum of power per radius and the count of pixels per radius -> mean per ring.
    tbin = np.bincount(r.ravel(), weights=power.ravel())
    nr = np.bincount(r.ravel())
    nr = np.where(nr == 0, 1, nr)
    radial_mean = tbin / nr

    # Limit to the largest fully-contained radius (~128 for a 256x256 image).
    max_r = min(cy, cx)
    return radial_mean[:max_r]


def analyze(image: Image.Image) -> dict:
    """Detect AI-generation artifacts via the azimuthally-averaged FFT power
    spectrum. Returns a dict with score/confidence/details."""
    try:
        # 1. Grayscale, resize to 256x256.
        gray = np.array(image.convert("L").resize((256, 256)), dtype=np.float64)

        # 2. 2D FFT -> shift -> magnitude -> log power spectrum.
        fft_result = fft2(gray)
        magnitude = np.abs(np.fft.fftshift(fft_result))
        power = magnitude ** 2
        log_power = np.log1p(power)

        # 3. Radially average -> 1D profile (length ~128).
        profile = _radial_profile(log_power)
        n = len(profile)
        if n < 16:
            raise ValueError("radial profile too short")

        # 4. Fit decay slope over the mid-to-high frequency range (log-log).
        # Skip the very low frequencies (DC / first few bins) which are dominated
        # by overall brightness and do not follow the power law.
        lo = max(1, int(n * 0.10))
        hi = n  # through to the highest contained radius
        radii = np.arange(lo, hi)
        prof_seg = profile[lo:hi]

        # log-log: x = log(radius), y = log(power). profile is already log-power,
        # so exponentiate-then-log would be lossy; instead treat the log-power as
        # the y axis directly against log(radius) (slope is the spectral exponent).
        log_r = np.log(radii.astype(np.float64) + 1e-10)
        log_p = prof_seg  # already in log domain
        # Guard against constant input (flat synthetic images).
        if np.std(log_r) < 1e-9:
            slope = 0.0
        else:
            slope = float(np.polyfit(log_r, log_p, 1)[0])

        # 5. High-frequency energy ratio: outer 25% of radii vs inner 25%.
        q = max(1, n // 4)
        inner = profile[:q]
        outer = profile[-q:]
        inner_mean = float(np.mean(inner))
        outer_mean = float(np.mean(outer))
        hf_ratio = outer_mean / (inner_mean + 1e-10)

        # 6. Detect periodic spikes: peaks rising clearly above a local mean.
        # Use a sliding window over the mid-to-high portion of the profile.
        periodic_spikes = 0
        win = 5
        start = lo
        for i in range(start + win, n - win):
            local = profile[i - win:i + win + 1]
            local_mean = float(np.mean(local))
            local_std = float(np.std(local))
            val = float(profile[i])
            # A spike is a local maximum standing notably above its neighborhood.
            if (
                val == float(np.max(local))
                and val > local_mean + 2.0 * local_std
                and local_std > 1e-6
            ):
                periodic_spikes += 1

        # 7. Combine into an additive score (higher = more likely AI).
        score = 0.0

        # Flat / non-decaying spectrum -> up-convolution failing to reproduce the
        # natural 1/f^a falloff. Real photos sit around -1 to -2.5.
        if slope > -0.5:
            score += 0.20
        elif slope > -1.0:
            score += 0.10

        # Elevated high-frequency energy relative to low frequencies.
        if hf_ratio > 0.85:
            score += 0.15
        elif hf_ratio > 0.70:
            score += 0.08

        # Periodic spikes from the upsampling grid.
        if periodic_spikes >= 3:
            score += 0.15
        elif periodic_spikes >= 1:
            score += 0.08

        score = float(min(score, 1.0))
        confidence = float(min(score * 1.5, 1.0))

        return {
            "signal_name": "azimuthal_spectrum",
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "details": {
                "slope": round(slope, 4),
                "hf_ratio": round(hf_ratio, 4),
                "periodic_spikes": int(periodic_spikes),
                "inner_power_mean": round(inner_mean, 4),
                "outer_power_mean": round(outer_mean, 4),
                "profile_length": int(n),
            },
        }
    except Exception:
        return {"signal_name": "azimuthal_spectrum", "score": 0.0, "confidence": 0.0, "details": {}}
