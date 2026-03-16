"""
Color Space Analysis Module

Analyzes images in LAB and YCbCr color spaces for AI artifacts.
AI generators often produce images with subtle anomalies in perceptual
color spaces that are invisible in RGB but detectable in LAB/YCbCr.
"""

import numpy as np
from PIL import Image
from scipy.stats import kurtosis, skew, entropy


def rgb_to_lab(img_array):
    """Convert RGB (0-255) to CIE LAB color space."""
    # Normalize to 0-1
    rgb = img_array.astype(np.float64) / 255.0

    # Linearize sRGB
    mask = rgb > 0.04045
    rgb[mask] = ((rgb[mask] + 0.055) / 1.055) ** 2.4
    rgb[~mask] = rgb[~mask] / 12.92

    # RGB to XYZ (D65 illuminant)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

    # Normalize by D65 white point
    x /= 0.95047
    z /= 1.08883

    # XYZ to LAB
    def f(t):
        mask = t > 0.008856
        result = np.zeros_like(t)
        result[mask] = t[mask] ** (1/3)
        result[~mask] = 7.787 * t[~mask] + 16/116
        return result

    L = 116 * f(y) - 16
    a = 500 * (f(x) - f(y))
    b_ch = 200 * (f(y) - f(z))

    return np.stack([L, a, b_ch], axis=-1)


class ColorSpaceAnalyzer:
    """Analyzes color space properties for AI detection."""

    def analyze(self, image: Image.Image) -> dict:
        img = np.array(image.convert("RGB").resize((256, 256)))
        scores = []

        # ── LAB Analysis ──
        lab = rgb_to_lab(img)
        L, a, b = lab[:, :, 0], lab[:, :, 1], lab[:, :, 2]

        # AI images often have limited a/b channel range
        a_range = np.ptp(a)
        b_range = np.ptp(b)
        if a_range < 30:
            scores.append(0.12)
        if b_range < 30:
            scores.append(0.12)

        # Chrominance smoothness (AI tends to be smoother in a/b)
        a_grad = np.mean(np.abs(np.diff(a, axis=0))) + np.mean(np.abs(np.diff(a, axis=1)))
        b_grad = np.mean(np.abs(np.diff(b, axis=0))) + np.mean(np.abs(np.diff(b, axis=1)))
        chroma_grad = (a_grad + b_grad) / 2

        if chroma_grad < 0.5:
            scores.append(0.20)
        elif chroma_grad < 1.0:
            scores.append(0.12)

        # L channel noise vs chrominance noise ratio
        L_noise = np.std(L - np.array(Image.fromarray(L.astype(np.uint8)).filter(
            __import__('PIL').ImageFilter.GaussianBlur(radius=2)), dtype=np.float64))
        a_noise = np.std(a[1:, :] - a[:-1, :])
        b_noise = np.std(b[1:, :] - b[:-1, :])

        # Real cameras have correlated noise across L and chroma
        luma_chroma_ratio = L_noise / (((a_noise + b_noise) / 2) + 1e-10)
        if luma_chroma_ratio > 5:  # Unnaturally clean chrominance
            scores.append(0.15)

        # ── YCbCr Analysis ──
        ycbcr = np.array(image.convert("YCbCr").resize((256, 256)), dtype=np.float64)
        Y, Cb, Cr = ycbcr[:, :, 0], ycbcr[:, :, 1], ycbcr[:, :, 2]

        # Cb/Cr channel statistics
        cb_kurtosis = float(kurtosis(Cb.flatten()))
        cr_kurtosis = float(kurtosis(Cr.flatten()))
        cb_kurtosis = cb_kurtosis if np.isfinite(cb_kurtosis) else 0.0
        cr_kurtosis = cr_kurtosis if np.isfinite(cr_kurtosis) else 0.0

        # AI images often have unusual Cb/Cr distributions
        if abs(cb_kurtosis) < 0.5 and abs(cr_kurtosis) < 0.5:
            scores.append(0.10)

        # Cb-Cr correlation (AI often has different Cb-Cr relationships)
        try:
            cbcr_corr = np.corrcoef(Cb.flatten(), Cr.flatten())[0, 1]
            cbcr_corr = cbcr_corr if np.isfinite(cbcr_corr) else 0.0
        except Exception:
            cbcr_corr = 0.0

        if abs(cbcr_corr) > 0.8:
            scores.append(0.10)

        # ── Color quantization artifacts ──
        # AI images sometimes show subtle quantization patterns
        for ch_name, ch_data in [("R", img[:,:,0]), ("G", img[:,:,1]), ("B", img[:,:,2])]:
            hist, _ = np.histogram(ch_data.flatten(), bins=256, range=(0, 255))
            # Check for periodic gaps in histogram (quantization)
            zero_bins = np.sum(hist == 0)
            if zero_bins > 50:  # Many unused intensity values
                scores.append(0.08)
                break

        total = min(sum(scores), 1.0)

        return {
            "ai_probability": round(total, 4),
            "lab_chroma_gradient": round(float(chroma_grad), 4),
            "lab_a_range": round(float(a_range), 2),
            "lab_b_range": round(float(b_range), 2),
            "luma_chroma_ratio": round(float(luma_chroma_ratio), 4),
            "ycbcr_cb_kurtosis": round(cb_kurtosis, 4),
            "ycbcr_cr_kurtosis": round(cr_kurtosis, 4),
            "cbcr_correlation": round(float(cbcr_corr), 4),
        }
