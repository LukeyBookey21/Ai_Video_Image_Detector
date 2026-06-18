"""
AI Image Detection Module — Multi-Model Ensemble

Detection signals (7 total):
1. ViT ML Model (primary) — Organika/sdxl-detector for diffusion model detection
2. Deepfake ML Model — prithivMLmods deepfake detector for face/video fakes
3. DCT Frequency Analysis — spectral artifacts in frequency domain
4. FFT Power Spectrum — 1/f power law deviation analysis
5. Statistical/Noise Analysis — pixel distributions, noise patterns, color stats
6. Texture & Edge Analysis — local variance, edge density, gradient patterns
7. SRM Noise Fingerprint — steganalysis-based noise residual patterns
8. Metadata Analysis — EXIF, compression artifacts, format anomalies

Ensemble scoring with calibrated confidence weighting.
"""

import io
import logging
import os
import struct
import warnings

import cv2
import numpy as np
from PIL import Image, ImageFilter
from PIL.ExifTags import TAGS
from scipy.fft import dctn, fft2
from scipy.stats import kurtosis, skew, entropy
from scipy.ndimage import uniform_filter, convolve

# Try to import ML libraries
_HAS_ML = False
try:
    from transformers import pipeline as hf_pipeline

    _HAS_ML = True
except ImportError:
    pass

# Model version — bump minor when signals change, major when ensemble weights change
MODEL_VERSION = "v2.1"


# ─── SRM Filters (Steganalysis Rich Model) ───────────────────────────────────

SRM_FILTER_1 = np.array(
    [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 1, -2, 1, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ],
    dtype=np.float64,
)

SRM_FILTER_2 = np.array(
    [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, -2, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0],
    ],
    dtype=np.float64,
)

SRM_FILTER_3 = np.array(
    [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, -1, 1, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ],
    dtype=np.float64,
)

SRM_FILTER_EDGE = (
    np.array(
        [
            [-1, 2, -2, 2, -1],
            [2, -6, 8, -6, 2],
            [-2, 8, -12, 8, -2],
            [2, -6, 8, -6, 2],
            [-1, 2, -2, 2, -1],
        ],
        dtype=np.float64,
    )
    / 12.0
)


class ViTDetector:
    """Pre-trained Vision Transformer for AI image detection."""

    def __init__(self, model_name, label_map=None):
        self.pipe = None
        self.model_name = model_name
        self.label_map = label_map or {}
        self.available = False
        self.error = None

    def load(self):
        if not _HAS_ML:
            self.error = "torch/transformers not installed"
            return False
        try:
            logging.info(f"  Loading: {self.model_name}...")
            self.pipe = hf_pipeline("image-classification", model=self.model_name, device=-1)
            self.available = True
            logging.info(f"  Loaded: {self.model_name}")
            return True
        except Exception as e:
            self.error = str(e)
            logging.warning(f"  Failed: {self.model_name}: {e}")
            return False

    def predict(self, image: Image.Image) -> float:
        if not self.available or self.pipe is None:
            return None
        try:
            results = self.pipe(image)
            scores = {r["label"].lower(): r["score"] for r in results}

            # Try known AI labels
            for label_key in ["artificial", "ai", "fake", "deepfake", "ai_generated"]:
                if label_key in scores:
                    return scores[label_key]

            # Check label_map
            for mapped_label, target in self.label_map.items():
                if mapped_label in scores:
                    return scores[mapped_label] if target == "ai" else 1.0 - scores[mapped_label]

            # Fallback: infer from first result
            if results:
                label = results[0]["label"].lower()
                score = results[0]["score"]
                if any(k in label for k in ["artificial", "ai", "fake", "generated"]):
                    return score
                else:
                    return 1.0 - score
            return None
        except Exception as e:
            logging.warning(f"  ML prediction error ({self.model_name}): {e}")
            return None


class FrequencyAnalyzer:
    """DCT + FFT frequency domain analysis."""

    def analyze(self, image: Image.Image) -> dict:
        img_gray = np.array(image.convert("L").resize((256, 256)), dtype=np.float64)

        # ── DCT Analysis ──
        dct_coeffs = dctn(img_gray, norm="ortho")
        magnitude = np.abs(dct_coeffs)
        log_mag = np.log1p(magnitude)

        h, w = magnitude.shape
        q = h // 4
        low = magnitude[:q, :q]
        mid = magnitude[q : 2 * q, q : 2 * q]
        high = magnitude[2 * q :, 2 * q :]

        low_e = np.mean(low)
        mid_e = np.mean(mid)
        high_e = np.mean(high)
        total_e = low_e + mid_e + high_e + 1e-10

        high_ratio = high_e / total_e
        mid_ratio = mid_e / total_e

        # Spectral flatness (Wiener entropy)
        sv = log_mag.flatten()
        sv = sv[sv > 0]
        geo_mean = np.exp(np.mean(np.log(sv + 1e-10)))
        arith_mean = np.mean(sv) + 1e-10
        spectral_flatness = geo_mean / arith_mean

        # ── FFT + Radial Power Spectrum ──
        fft_result = fft2(img_gray)
        fft_mag = np.abs(np.fft.fftshift(fft_result))
        fft_log = np.log1p(fft_mag)

        cy, cx = h // 2, w // 2
        Y, X = np.ogrid[:h, :w]
        r = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2).astype(int)
        max_r = min(cy, cx)
        radial = np.zeros(max_r)
        for i in range(max_r):
            mask = r == i
            if np.any(mask):
                radial[i] = np.mean(fft_log[mask])

        # Power law slope (natural images ≈ -1.0 to -1.5)
        slope = -1.0
        if len(radial) > 10:
            freqs = np.arange(1, len(radial))
            power = radial[1:]
            valid = power > 0
            if np.sum(valid) > 5:
                slope = np.polyfit(np.log(freqs[valid]), np.log(power[valid]), 1)[0]

        slope_dev = abs(slope - (-1.2))

        # ── DCT Block Artifact Analysis ──
        # JPEG-like block artifacts from AI generators
        block_scores = []
        for bsize in [8, 16]:
            block_boundary_energy = 0
            block_interior_energy = 0
            for y in range(0, h - bsize, bsize):
                for x in range(0, w - bsize, bsize):
                    block = img_gray[y : y + bsize, x : x + bsize]
                    # Edge energy at block boundaries
                    if y > 0:
                        block_boundary_energy += np.mean(
                            np.abs(img_gray[y, x : x + bsize] - img_gray[y - 1, x : x + bsize])
                        )
                    block_interior_energy += np.mean(np.abs(np.diff(block, axis=0)))
            ratio = block_boundary_energy / (block_interior_energy + 1e-10)
            block_scores.append(ratio)

        block_artifact_score = np.mean(block_scores)

        # ── Scoring ──
        score = 0.0

        # High-freq energy
        if high_ratio < 0.005:
            score += 0.22
        elif high_ratio < 0.02:
            score += 0.15
        elif high_ratio < 0.04:
            score += 0.08

        # Spectral flatness
        if spectral_flatness > 0.80:
            score += 0.25
        elif spectral_flatness > 0.60:
            score += 0.18
        elif spectral_flatness > 0.45:
            score += 0.10

        # Power law deviation
        if slope_dev > 0.9:
            score += 0.28
        elif slope_dev > 0.6:
            score += 0.20
        elif slope_dev > 0.35:
            score += 0.12

        # Mid-frequency
        if mid_ratio > 0.25:
            score += 0.15
        elif mid_ratio > 0.12:
            score += 0.08

        # Block artifacts
        if block_artifact_score > 1.5:
            score += 0.10
        elif block_artifact_score < 0.5:
            score += 0.08  # Unnaturally smooth boundaries

        return {
            "ai_probability": round(min(max(score, 0.0), 1.0), 4),
            "high_freq_ratio": round(high_ratio, 6),
            "mid_freq_ratio": round(mid_ratio, 6),
            "spectral_flatness": round(float(spectral_flatness), 4),
            "power_law_slope": round(float(slope), 4),
            "slope_deviation": round(float(slope_dev), 4),
            "block_artifact": round(float(block_artifact_score), 4),
        }


class StatisticalAnalyzer:
    """Pixel statistics, noise patterns, color analysis."""

    def analyze(self, image: Image.Image) -> dict:
        img = np.array(image.convert("RGB").resize((512, 512)), dtype=np.float64)
        scores = []

        # ── Channel Statistics ──
        channel_names = ["R", "G", "B"]
        channel_stats = {}
        for i, name in enumerate(channel_names):
            ch = img[:, :, i].flatten()
            std = np.std(ch)
            k = float(kurtosis(ch)) if std > 0.01 else 0.0
            s = float(skew(ch)) if std > 0.01 else 0.0
            k = k if np.isfinite(k) else 0.0
            s = s if np.isfinite(s) else 0.0
            channel_stats[name] = {"mean": np.mean(ch), "std": std, "kurtosis": k, "skewness": s}

        avg_kurtosis = np.mean([abs(channel_stats[c]["kurtosis"]) for c in channel_names])
        if avg_kurtosis < 0.8:
            score_k = 0.22
        elif avg_kurtosis < 1.5:
            score_k = 0.15
        elif avg_kurtosis < 2.5:
            score_k = 0.08
        elif avg_kurtosis > 7.0:
            score_k = 0.12
        else:
            score_k = 0.0
        scores.append(score_k)

        # ── Multi-Scale Noise Analysis ──
        img_pil = image.convert("L").resize((512, 512))
        noise_scores = []
        for radius in [1, 2, 4]:
            blurred = img_pil.filter(ImageFilter.GaussianBlur(radius=radius))
            noise = np.array(img_pil, dtype=np.float64) - np.array(blurred, dtype=np.float64)
            ns = np.std(noise)
            nk = float(kurtosis(noise.flatten()))
            nk = nk if np.isfinite(nk) else 0.0
            noise_scores.append((ns, nk))

        # Primary noise (radius=2)
        noise_std = noise_scores[1][0]
        noise_kurtosis = noise_scores[1][1]

        # Noise consistency across scales
        noise_stds = [ns for ns, _ in noise_scores]
        noise_consistency = np.std(noise_stds) / (np.mean(noise_stds) + 1e-10)

        if noise_std < 1.5:
            scores.append(0.28)
        elif noise_std < 3.0:
            scores.append(0.18)
        elif noise_std < 5.0:
            scores.append(0.10)
        # Note: high noise alone is NOT evidence of real — AI panoramas and
        # composite images can have high noise. Only trust noise as evidence
        # of real when combined with camera EXIF (handled in metadata analyzer).

        if abs(noise_kurtosis) > 6.0:
            scores.append(0.15)
        elif abs(noise_kurtosis) > 3.5:
            scores.append(0.10)

        # AI images have unnaturally consistent noise across scales
        if noise_consistency < 0.15:
            scores.append(0.12)

        # ── Color Channel Correlation ──
        r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                corrs_raw = [
                    np.corrcoef(r.flatten(), g.flatten())[0, 1],
                    np.corrcoef(r.flatten(), b.flatten())[0, 1],
                    np.corrcoef(g.flatten(), b.flatten())[0, 1],
                ]
            corrs = [c for c in corrs_raw if np.isfinite(c)]
            avg_corr = np.mean([abs(c) for c in corrs]) if corrs else 0.5
        except Exception:
            avg_corr = 0.5

        if avg_corr > 0.97:
            scores.append(0.15)  # Extremely high = AI
        elif avg_corr > 0.93:
            scores.append(0.08)  # Very high = suspicious
        elif avg_corr < 0.55:
            scores.append(0.12)  # Very low = unusual for real photos (AI generators can produce decorrelated channels)

        # ── Histogram Smoothness ──
        for i in range(3):
            ch = img[:, :, i].flatten().astype(int)
            hist, _ = np.histogram(ch, bins=256, range=(0, 255))
            # AI images often have smoother histograms (less spiky)
            hist_diff = np.abs(np.diff(hist.astype(float)))
            hist_roughness = np.mean(hist_diff) / (np.mean(hist) + 1e-10)
            if hist_roughness < 0.3:
                scores.append(0.06)
                break

        # ── Saturation Analysis ──
        hsv = np.array(image.convert("HSV").resize((512, 512)), dtype=np.float64)
        sat = hsv[:, :, 1]
        sat_std = np.std(sat)
        if sat_std < 20:  # Unnaturally uniform saturation
            scores.append(0.08)

        total_score = min(sum(scores), 1.0)
        return {
            "ai_probability": round(total_score, 4),
            "noise_std": round(noise_std, 4),
            "noise_kurtosis": round(noise_kurtosis, 4),
            "noise_consistency": round(noise_consistency, 4),
            "avg_kurtosis": round(avg_kurtosis, 4),
            "color_correlation": round(avg_corr, 4),
        }


class TextureAnalyzer:
    """Local texture, edge density, gradient analysis."""

    def analyze(self, image: Image.Image) -> dict:
        img_gray = np.array(image.convert("L").resize((256, 256)), dtype=np.float64)

        # ── Local Variance (multi-scale) ──
        variances = []
        for size in [4, 8, 16]:
            lm = uniform_filter(img_gray, size=size)
            lsm = uniform_filter(img_gray**2, size=size)
            lv = np.maximum(lsm - lm**2, 0)
            variances.append(np.mean(lv))

        avg_local_var = variances[1]  # size=8
        var_of_var = np.var(np.maximum(uniform_filter(img_gray**2, size=8) - uniform_filter(img_gray, size=8) ** 2, 0))

        # Variance ratio across scales (AI is more scale-invariant)
        var_ratio = variances[0] / (variances[2] + 1e-10)

        scores = []

        if avg_local_var < 30:
            scores.append(0.28)
        elif avg_local_var < 100:
            scores.append(0.20)
        elif avg_local_var < 250:
            scores.append(0.10)
        elif avg_local_var < 500:
            scores.append(0.04)

        if var_of_var < 1000:
            scores.append(0.22)
        elif var_of_var < 5000:
            scores.append(0.14)
        elif var_of_var < 12000:
            scores.append(0.06)

        # Scale invariance (AI tends to be more uniform across scales)
        if 0.8 < var_ratio < 1.3:
            scores.append(0.10)

        # ── Edge Analysis ──
        edges = np.array(image.convert("L").resize((256, 256)).filter(ImageFilter.FIND_EDGES), dtype=np.float64)
        edge_density = np.mean(edges > 30)
        edge_std = np.std(edges)

        if edge_density < 0.02:
            scores.append(0.22)
        elif edge_density < 0.06:
            scores.append(0.14)
        elif edge_density < 0.10:
            scores.append(0.06)
        # Note: high edge density alone is NOT evidence of real — AI composites
        # and tiled images can have high edge density too.

        # Low edge variance = uniform edge distribution (AI-like)
        if edge_std < 15:
            scores.append(0.10)

        # ── Gradient Analysis ──
        gy, gx = np.gradient(img_gray)
        grad_mag = np.sqrt(gx**2 + gy**2)
        grad_entropy_val = float(entropy(np.histogram(grad_mag.flatten(), bins=64, density=True)[0] + 1e-10))

        # Gradient orientation uniformity
        grad_angle = np.arctan2(gy, gx)
        angle_hist, _ = np.histogram(grad_angle.flatten(), bins=36, density=True)
        angle_entropy = float(entropy(angle_hist + 1e-10))

        if grad_entropy_val < 1.2:
            scores.append(0.15)
        elif grad_entropy_val < 2.0:
            scores.append(0.08)

        # Very uniform gradient orientations (AI tends to be smoother)
        if angle_entropy > 3.5:
            scores.append(0.06)

        total_score = min(sum(scores), 1.0)
        return {
            "ai_probability": round(total_score, 4),
            "avg_local_variance": round(float(avg_local_var), 2),
            "variance_of_variance": round(float(var_of_var), 2),
            "edge_density": round(float(edge_density), 4),
            "edge_std": round(float(edge_std), 2),
            "gradient_entropy": round(float(grad_entropy_val), 4),
            "var_ratio": round(float(var_ratio), 4),
        }


class SRMAnalyzer:
    """Steganalysis Rich Model noise residual analysis.

    Uses SRM high-pass filters to extract noise residuals, then analyzes
    their statistical properties. AI-generated images have different
    noise fingerprints than camera-captured photos.
    """

    def analyze(self, image: Image.Image) -> dict:
        img_gray = np.array(image.convert("L").resize((256, 256)), dtype=np.float64)

        residuals = []
        for filt in [SRM_FILTER_1, SRM_FILTER_2, SRM_FILTER_3, SRM_FILTER_EDGE]:
            res = convolve(img_gray, filt, mode="reflect")
            residuals.append(res)

        scores = []

        # ── Residual statistics ──
        all_residual_stds = []
        all_residual_kurtoses = []
        for res in residuals:
            flat = res.flatten()
            std = np.std(flat)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                k = float(kurtosis(flat))
            k = k if np.isfinite(k) else 0.0
            all_residual_stds.append(std)
            all_residual_kurtoses.append(k)

        avg_res_std = np.mean(all_residual_stds)
        avg_res_kurtosis = np.mean(all_residual_kurtoses)

        # AI images have lower noise residuals (smoother)
        if avg_res_std < 1.0:
            scores.append(0.30)
        elif avg_res_std < 2.5:
            scores.append(0.20)
        elif avg_res_std < 5.0:
            scores.append(0.10)

        # Residual kurtosis (AI differs from natural camera noise)
        if avg_res_kurtosis > 15:
            scores.append(0.20)
        elif avg_res_kurtosis > 8:
            scores.append(0.12)
        elif avg_res_kurtosis < 1.0:
            scores.append(0.15)

        # ── Cross-filter consistency ──
        # AI images have more consistent residuals across different filters
        std_variation = np.std(all_residual_stds) / (np.mean(all_residual_stds) + 1e-10)
        if std_variation < 0.3:
            scores.append(0.15)
        elif std_variation < 0.5:
            scores.append(0.08)

        # ── Spatial correlation of residuals ──
        # AI residuals tend to be more spatially correlated
        for res in residuals[:2]:
            autocorr = np.corrcoef(res[:-1, :].flatten(), res[1:, :].flatten())[0, 1]
            if np.isfinite(autocorr) and abs(autocorr) > 0.5:
                scores.append(0.08)
                break

        total_score = min(sum(scores), 1.0)
        return {
            "ai_probability": round(total_score, 4),
            "avg_residual_std": round(float(avg_res_std), 4),
            "avg_residual_kurtosis": round(float(avg_res_kurtosis), 4),
            "residual_consistency": round(float(std_variation), 4),
        }


class ScreenshotDetector:
    """Detect screenshots and screen recordings.
    Screenshots have: sharp pixel boundaries, UI elements, specific DPI, no camera noise."""

    def analyze(self, image: Image.Image) -> dict:
        try:
            img = np.array(image.convert("RGB"))
            h, w = img.shape[:2]

            indicators = []

            # 1. Check for perfectly horizontal/vertical sharp edges (UI elements)
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if len(img.shape) == 3 else img
            small = cv2.resize(gray, (min(w, 512), min(h, 512)))
            edges_h = cv2.Sobel(small, cv2.CV_64F, 0, 1, ksize=3)
            edges_v = cv2.Sobel(small, cv2.CV_64F, 1, 0, ksize=3)

            # Screenshots have many perfectly horizontal/vertical edges
            h_edge_ratio = np.sum(np.abs(edges_h) > 30) / (small.shape[0] * small.shape[1] + 1)
            v_edge_ratio = np.sum(np.abs(edges_v) > 30) / (small.shape[0] * small.shape[1] + 1)

            # High ratio of aligned edges = UI/screenshot
            if h_edge_ratio > 0.15 and v_edge_ratio > 0.15:
                indicators.append("ui_edges")

            # 2. Check for solid-color rectangular regions (buttons, bars, backgrounds)
            # Quantize and look for large uniform blocks
            quantized = (img // 32) * 32
            block_size = max(8, min(h, w) // 32)
            uniform_blocks = 0
            total_blocks = 0
            for by in range(0, h - block_size, block_size):
                for bx in range(0, w - block_size, block_size):
                    block = quantized[by : by + block_size, bx : bx + block_size]
                    if np.std(block) < 2:
                        uniform_blocks += 1
                    total_blocks += 1

            uniform_ratio = uniform_blocks / (total_blocks + 1)
            if uniform_ratio > 0.40:
                indicators.append("uniform_blocks")

            # 3. Check for common screenshot dimensions (phone screens, desktop)
            screenshot_ratios = [16 / 9, 9 / 16, 4 / 3, 3 / 4, 19.5 / 9, 9 / 19.5]
            aspect = w / h if h > 0 else 1
            is_screen_ratio = any(abs(aspect - r) < 0.05 for r in screenshot_ratios)
            # Common screen widths
            is_screen_width = w in [320, 375, 390, 414, 428, 768, 1024, 1080, 1170, 1284, 1440, 1920, 2560, 3840]

            if is_screen_ratio and is_screen_width:
                indicators.append("screen_dimensions")

            is_screenshot = len(indicators) >= 2
            return {
                "is_screenshot": is_screenshot,
                "indicators": indicators,
                "uniform_block_ratio": round(uniform_ratio, 3),
            }
        except Exception:
            return {"is_screenshot": False, "indicators": [], "uniform_block_ratio": 0}


class PatchConsistencyAnalyzer:
    """Analyze local noise consistency across image patches.
    Real photos have uniform sensor noise; AI images often have varying noise levels."""

    def analyze(self, image: Image.Image) -> dict:
        try:
            img = np.array(image.convert("L").resize((256, 256)), dtype=np.float64)
            patch_size = 32
            h, w = img.shape

            # Compute local noise level in each patch (std of high-pass filtered patch)
            noise_levels = []
            for y in range(0, h - patch_size + 1, patch_size):
                for x in range(0, w - patch_size + 1, patch_size):
                    patch = img[y : y + patch_size, x : x + patch_size]
                    # High-pass filter to isolate noise
                    from scipy.ndimage import median_filter

                    smoothed = median_filter(patch, size=3)
                    noise = patch - smoothed
                    noise_levels.append(np.std(noise))

            if len(noise_levels) < 4:
                return {"ai_probability": 0.0, "noise_consistency": 1.0}

            noise_array = np.array(noise_levels)
            mean_noise = np.mean(noise_array)
            std_noise = np.std(noise_array)
            cv = std_noise / (mean_noise + 1e-10)  # Coefficient of variation

            # Real photos: consistent noise (low CV, typically 0.2-0.5)
            # AI images: can have very inconsistent noise or artificially uniform noise
            scores = []

            # Very low mean noise = AI smoothness
            if mean_noise < 1.5:
                scores.append(0.15)

            # Very high noise variation across patches = possible compositing or AI
            if cv > 0.7:
                scores.append(0.10)

            # Artificially uniform noise (too perfect) = possibly AI
            if cv < 0.15 and mean_noise < 3.0:
                scores.append(0.12)

            ai_prob = min(sum(scores), 0.3)
            return {
                "ai_probability": round(ai_prob, 4),
                "noise_consistency": round(1.0 - cv, 4),
                "mean_patch_noise": round(float(mean_noise), 4),
                "noise_cv": round(float(cv), 4),
            }
        except Exception:
            return {"ai_probability": 0.0, "noise_consistency": 1.0}


class ELAAnalyzer:
    """Error Level Analysis — re-compress and measure error uniformity.
    Real photos have varied ELA (different regions compress differently).
    AI images have more uniform ELA (generated at consistent quality)."""

    def analyze(self, image: Image.Image) -> dict:
        try:
            img = image.convert("RGB")
            # Re-compress at quality 90
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            buf.seek(0)
            recompressed = Image.open(buf).convert("RGB")

            # Compute error level
            original = np.array(img, dtype=np.float64)
            recomp = np.array(recompressed, dtype=np.float64)
            ela = np.abs(original - recomp)

            # Scale for visibility
            ela_mean = np.mean(ela)
            ela_std = np.std(ela)

            # Compute regional ELA variance
            h, w = ela.shape[:2]
            block = 32
            regional_means = []
            for y in range(0, h - block, block):
                for x in range(0, w - block, block):
                    regional_means.append(np.mean(ela[y : y + block, x : x + block]))

            if len(regional_means) < 4:
                return {"ai_probability": 0.0, "ela_uniformity": 0.0}

            regional_cv = np.std(regional_means) / (np.mean(regional_means) + 1e-10)

            # AI images: very uniform ELA (low regional CV, typically < 0.5)
            # Real photos: varied ELA (high regional CV, typically 0.8-2.0)
            scores = []
            if regional_cv < 0.3:
                scores.append(0.12)
            elif regional_cv < 0.5:
                scores.append(0.06)

            return {
                "ai_probability": round(min(sum(scores), 0.2), 4),
                "ela_uniformity": round(1.0 - min(regional_cv, 2.0) / 2.0, 4),
                "ela_mean": round(float(ela_mean), 4),
            }
        except Exception:
            return {"ai_probability": 0.0, "ela_uniformity": 0.0}


class JPEGGhostAnalyzer:
    """Detect JPEG compression inconsistencies (double compression, format conversion)."""

    def analyze(self, image: Image.Image, raw_bytes: bytes = None) -> dict:
        if raw_bytes is None:
            return {"ai_probability": 0.0, "ghost_score": 0.0, "compression_type": "unknown"}

        # Detect format from raw bytes
        is_jpeg = raw_bytes[:2] == b"\xff\xd8"
        if not is_jpeg:
            # Non-JPEG: check if it's a clean PNG (common for AI)
            is_png = raw_bytes[:4] == b"\x89PNG"
            if is_png:
                # PNG images — check for unusual smoothness in DCT domain
                # (would show compression ghosts if it was originally JPEG)
                return {"ai_probability": 0.05, "ghost_score": 0.0, "compression_type": "png_original"}
            return {"ai_probability": 0.0, "ghost_score": 0.0, "compression_type": "other"}

        try:
            img_array = np.array(image.convert("RGB"), dtype=np.float64)
            if img_array.shape[0] < 16 or img_array.shape[1] < 16:
                return {"ai_probability": 0.0, "ghost_score": 0.0, "compression_type": "too_small"}

            # Re-compress at multiple quality levels and measure difference
            # Double-compressed JPEGs show minimum error at the original quality
            errors = []
            for quality in [60, 70, 80, 90, 95]:
                buf = io.BytesIO()
                image.save(buf, format="JPEG", quality=quality)
                buf.seek(0)
                recompressed = np.array(Image.open(buf).convert("RGB"), dtype=np.float64)
                diff = np.mean(np.abs(img_array - recompressed))
                errors.append((quality, diff))

            # In a single-compressed JPEG, error decreases monotonically with quality
            # In a double-compressed JPEG, there's a dip at the original quality
            diffs = [e[1] for e in errors]
            min_idx = np.argmin(diffs)
            monotonic = all(diffs[i] >= diffs[i + 1] for i in range(len(diffs) - 1))

            # Ghost score: how non-monotonic is the error curve
            ghost_score = 0.0
            if not monotonic and min_idx > 0 and min_idx < len(diffs) - 1:
                # Local minimum in the middle = double compression
                ghost_score = (diffs[min_idx - 1] - diffs[min_idx]) / (diffs[0] + 1e-10)

            # Very low overall error at high quality = likely never compressed before
            # (AI PNGs saved as JPEG for the first time)
            if diffs[-1] < 0.5:
                ai_prob = 0.08  # Suspiciously clean
            elif ghost_score > 0.1:
                ai_prob = 0.0  # Double compression = likely real (been shared around)
            else:
                ai_prob = 0.0

            return {
                "ai_probability": round(ai_prob, 4),
                "ghost_score": round(ghost_score, 4),
                "compression_type": "double_jpeg" if ghost_score > 0.1 else "single_jpeg",
            }
        except Exception:
            return {"ai_probability": 0.0, "ghost_score": 0.0, "compression_type": "error"}


class MetadataAnalyzer:
    """Analyzes image metadata, format, and compression for AI indicators."""

    def analyze(self, image: Image.Image, raw_bytes: bytes = None) -> dict:
        scores = []
        metadata_flags = []

        # ── EXIF Analysis ──
        exif_data = {}
        try:
            raw_exif = image.getexif()
            if raw_exif:
                for tag_id, value in raw_exif.items():
                    tag_name = TAGS.get(tag_id, str(tag_id))
                    exif_data[tag_name] = str(value)
        except Exception:
            pass

        has_camera_info = any(k in exif_data for k in ["Make", "Model", "LensModel", "FocalLength"])
        has_gps = any(k in exif_data for k in ["GPSInfo"])
        has_datetime = any(k in exif_data for k in ["DateTime", "DateTimeOriginal"])
        has_software = "Software" in exif_data

        # Camera metadata is strong evidence of real photo
        if has_camera_info:
            scores.append(-0.15)  # Negative = evidence of real
            metadata_flags.append("has_camera_info")
        if has_gps:
            scores.append(-0.10)
            metadata_flags.append("has_gps")
        if has_datetime and has_camera_info:
            scores.append(-0.05)

        # Detect format from raw bytes (image.format is lost after .convert())
        img_format = (image.format or "").upper()
        if not img_format and raw_bytes:
            if raw_bytes[:4] == b"\x89PNG":
                img_format = "PNG"
            elif raw_bytes[:2] == b"\xff\xd8":
                img_format = "JPEG"
            elif raw_bytes[:4] == b"RIFF" and raw_bytes[8:12] == b"WEBP":
                img_format = "WEBP"

        # No EXIF at all — suspicious, especially for PNG
        if not exif_data:
            if img_format == "PNG":
                # PNG without any metadata is the #1 AI image indicator
                scores.append(0.45)
                metadata_flags.append("png_no_exif")
            else:
                # JPEG without EXIF could be old scan, screenshot, or AI
                scores.append(0.20)
                metadata_flags.append("no_exif_data")
        elif not has_camera_info and not has_gps and not has_datetime:
            if img_format == "PNG":
                scores.append(0.30)
                metadata_flags.append("png_no_camera_metadata")
            else:
                scores.append(0.15)
                metadata_flags.append("no_camera_metadata")

        # Known AI software tags
        if has_software:
            sw = exif_data.get("Software", "").lower()
            ai_keywords = [
                "stable diffusion",
                "midjourney",
                "dall-e",
                "comfyui",
                "automatic1111",
                "novelai",
                "nai",
                "diffusion",
            ]
            if any(kw in sw for kw in ai_keywords):
                scores.append(0.60)
                metadata_flags.append(f"ai_software:{exif_data['Software']}")

        # JPEG with JFIF/EXIF headers is normal for real photos
        if img_format == "JPEG" and has_camera_info:
            scores.append(-0.10)

        # ── Image Properties ──
        w, h = image.size

        # Perfect power-of-2 or common AI dimensions
        ai_dimensions = [
            (512, 512),
            (768, 768),
            (1024, 1024),
            (1536, 1536),
            (2048, 2048),
            (512, 768),
            (768, 512),
            (1024, 768),
            (768, 1024),
            (1024, 1792),
            (1792, 1024),
            (1344, 768),
            (768, 1344),
        ]
        if (w, h) in ai_dimensions:
            scores.append(0.15)
            metadata_flags.append(f"ai_dimension:{w}x{h}")

        # Dimensions divisible by 64 (common in diffusion models) but not standard camera
        if w % 64 == 0 and h % 64 == 0 and not has_camera_info:
            scores.append(0.08)
            metadata_flags.append("dimensions_divisible_64")

        # ── JPEG Quantization Table Analysis ──
        if img_format == "JPEG" and raw_bytes:
            try:
                # Re-open from raw bytes to get quantization tables
                # (image.convert("RGB") strips them)
                original = Image.open(io.BytesIO(raw_bytes))
                qtables = getattr(original, "quantization", None)
                if qtables:
                    table0 = list(qtables.get(0, []))
                    if table0:
                        # All-ones table = quality 100 JPEG (real cameras never do this)
                        if all(v == 1 for v in table0[:8]):
                            scores.append(0.15)
                            metadata_flags.append("jpeg_quality_100")
                        # Standard JPEG table starts with [16, 11, 10, 16, 24, ...]
                        elif table0[0] == 16 and table0[1] == 11:
                            scores.append(0.08)
                            metadata_flags.append("standard_jpeg_qtable")
                        elif has_camera_info:
                            # Custom table + camera info = very likely real
                            scores.append(-0.08)
                            metadata_flags.append("camera_jpeg_qtable")
            except Exception:
                pass

        # ── Compression Analysis ──
        if raw_bytes:
            file_size = len(raw_bytes)
            pixel_count = w * h
            bits_per_pixel = (file_size * 8) / (pixel_count + 1)

            # Very high bpp in PNG = raw AI output (not compressed for web)
            if img_format == "PNG" and bits_per_pixel > 15:
                scores.append(0.08)

            # JPEG with normal compression from camera = real
            if img_format == "JPEG" and 1.0 < bits_per_pixel < 8.0:
                scores.append(-0.05)

        # Clamp to [0, 1]
        total_score = max(min(sum(scores), 1.0), 0.0)
        return {
            "ai_probability": round(total_score, 4),
            "has_camera_info": has_camera_info,
            "has_gps": has_gps,
            "has_datetime": has_datetime,
            "flags": metadata_flags,
            "dimensions": f"{w}x{h}",
        }


class AIImageDetector:
    """Multi-model ensemble detector with 9+ analysis signals."""

    def __init__(self):
        self.vit_primary = ViTDetector("Organika/sdxl-detector")
        self.vit_deepfake = ViTDetector("prithivMLmods/deepfake-detector-model-v1")
        self.freq_analyzer = FrequencyAnalyzer()
        self.stat_analyzer = StatisticalAnalyzer()
        self.texture_analyzer = TextureAnalyzer()
        self.srm_analyzer = SRMAnalyzer()
        self.metadata_analyzer = MetadataAnalyzer()
        self.jpeg_ghost_analyzer = JPEGGhostAnalyzer()
        self.patch_analyzer = PatchConsistencyAnalyzer()
        self.screenshot_detector = ScreenshotDetector()
        self.ela_analyzer = ELAAnalyzer()

        # Advanced analyzers
        from color_analysis import ColorSpaceAnalyzer
        from face_analysis import FaceAnalyzer

        self.color_analyzer = ColorSpaceAnalyzer()
        self.face_analyzer = FaceAnalyzer()

        self.ml_mode = False
        self.ml_models_loaded = []
        self.classifier = True

    def load_model(self):
        if not _HAS_ML:
            logging.info("ML libraries not available. Install with: python install_ml.py")
            logging.info("Running in heuristic-only mode.")
            return

        logging.info("Loading ML models...")
        loaded = []
        if self.vit_primary.load():
            loaded.append("sdxl-detector")
        if self.vit_deepfake.load():
            loaded.append("deepfake-detector")

        if loaded:
            self.ml_mode = True
            self.ml_models_loaded = loaded
            logging.info(f"ML ensemble active: {', '.join(loaded)}")
        else:
            logging.info("No ML models loaded. Running heuristic-only mode.")

    @staticmethod
    def _sanitize(val):
        if isinstance(val, (bool, np.bool_)):
            return bool(val)
        if isinstance(val, (float, np.floating)):
            return 0.0 if not np.isfinite(val) else float(val)
        if isinstance(val, np.integer):
            return int(val)
        return val

    def _sanitize_dict(self, d):
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k] = self._sanitize_dict(v)
            elif isinstance(v, list):
                result[k] = [self._sanitize(x) if not isinstance(x, (dict, list)) else x for x in v]
            else:
                result[k] = self._sanitize(v)
        return result

    # Canonical feature order — must match training (scripts/train_ensemble.py)
    META_FEATURES = [
        "frequency", "statistical", "texture", "srm", "color", "metadata",
        "face", "jpeg_ghost", "patch", "ela", "gan_fingerprint",
        "diffusion_artifacts", "noise_map", "prnu", "copy_move",
        "azimuthal_spectrum", "lighting_consistency",
    ]

    def _load_meta_classifier(self):
        """Lazy-load the trained logistic-regression weights, if present."""
        if hasattr(self, "_meta_weights"):
            return self._meta_weights
        import json

        path = os.path.join(os.path.dirname(__file__), "..", "models", "ensemble_weights.json")
        try:
            with open(path) as f:
                data = json.load(f)
            self._meta_weights = data
            logging.info("Loaded ensemble meta-classifier (%d features)", len(data.get("coef", [])))
        except Exception:
            self._meta_weights = None
        return self._meta_weights

    def _meta_classifier_predict(self, feature_vector: dict) -> float | None:
        """Apply the trained logistic regression. Returns probability or None."""
        weights = self._load_meta_classifier()
        if not weights:
            return None
        try:
            coef = weights["coef"]
            intercept = weights["intercept"]
            features = weights.get("features", self.META_FEATURES)
            z = intercept
            for i, name in enumerate(features):
                z += coef[i] * feature_vector.get(name, 0.0)
            return float(1.0 / (1.0 + np.exp(-z)))
        except Exception:
            return None

    def _call_hive_api(self, raw_bytes: bytes) -> float | None:
        """Call Hive Moderation API for AI-generated image detection. Returns score or None."""
        hive_key = os.environ.get("HIVE_API_KEY", "")
        if not hive_key:
            logging.debug("HIVE_API_KEY not set — skipping Hive signal")
            return None
        try:
            import requests

            resp = requests.post(
                "https://api.thehive.ai/api/v2/task/sync",
                headers={"Authorization": f"Token {hive_key}"},
                files={"media": ("image.jpg", io.BytesIO(raw_bytes), "image/jpeg")},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            for output in data.get("status", [{}])[0].get("response", {}).get("output", []):
                for cls in output.get("classes", []):
                    if cls.get("class") == "ai_generated":
                        return float(cls["score"])
        except Exception as e:
            logging.warning(f"Hive API error (continuing without it): {e}")
        return None

    def detect_image(self, image: Image.Image, raw_bytes: bytes = None) -> dict:
        image_rgb = image.convert("RGB")

        # Limit image size to prevent OOM on very large images (>4000px)
        w, h = image_rgb.size
        max_dim = 4096
        if w > max_dim or h > max_dim:
            scale = max_dim / max(w, h)
            image_rgb = image_rgb.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # Run all heuristic analyzers concurrently
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from signals import (
            gan_fingerprint,
            diffusion_artifacts,
            noise_map,
            prnu,
            copy_move,
            azimuthal_spectrum,
            lighting_consistency,
        )

        def _safe(fn, *args):
            try:
                return self._sanitize_dict(fn(*args))
            except Exception:
                return {}

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {
                pool.submit(_safe, self.freq_analyzer.analyze, image_rgb): "freq",
                pool.submit(_safe, self.stat_analyzer.analyze, image_rgb): "stat",
                pool.submit(_safe, self.texture_analyzer.analyze, image_rgb): "texture",
                pool.submit(_safe, self.srm_analyzer.analyze, image_rgb): "srm",
                pool.submit(_safe, self.metadata_analyzer.analyze, image_rgb, raw_bytes): "meta",
                pool.submit(_safe, self.color_analyzer.analyze, image_rgb): "color",
                pool.submit(_safe, self.face_analyzer.analyze, image_rgb): "face",
                pool.submit(_safe, self.jpeg_ghost_analyzer.analyze, image_rgb, raw_bytes): "jpeg_ghost",
                pool.submit(_safe, self.patch_analyzer.analyze, image_rgb): "patch",
                pool.submit(_safe, self.screenshot_detector.analyze, image_rgb): "screenshot",
                pool.submit(_safe, self.ela_analyzer.analyze, image_rgb): "ela",
                pool.submit(_safe, gan_fingerprint.analyze, image_rgb): "gan_fp",
                pool.submit(_safe, diffusion_artifacts.analyze, image_rgb): "diffusion",
                pool.submit(_safe, noise_map.analyze, image_rgb): "noise_inc",
                pool.submit(_safe, prnu.analyze, image_rgb): "prnu_result",
                pool.submit(_safe, copy_move.analyze, image_rgb): "copy_move",
                pool.submit(_safe, azimuthal_spectrum.analyze, image_rgb): "azimuthal",
                pool.submit(_safe, lighting_consistency.analyze, image_rgb): "lighting",
            }
            results = {}
            for future in as_completed(futures):
                name = futures[future]
                results[name] = future.result()

        freq = self._sanitize_dict(results.get("freq", {}))
        stat = self._sanitize_dict(results.get("stat", {}))
        texture = self._sanitize_dict(results.get("texture", {}))
        srm = self._sanitize_dict(results.get("srm", {}))
        meta = self._sanitize_dict(results.get("meta", {}))
        color = self._sanitize_dict(results.get("color", {}))
        face = self._sanitize_dict(results.get("face", {}))
        jpeg_ghost = self._sanitize_dict(results.get("jpeg_ghost", {}))
        patch = self._sanitize_dict(results.get("patch", {}))
        screenshot = results.get("screenshot", {})
        ela = self._sanitize_dict(results.get("ela", {}))
        gan_fp = results.get("gan_fp", {})
        diffusion = results.get("diffusion", {})
        noise_inc = results.get("noise_inc", {})
        prnu_result = results.get("prnu_result", {})
        copy_move_result = results.get("copy_move", {})
        azimuthal_result = results.get("azimuthal", {})
        lighting_result = results.get("lighting", {})

        # Run ML models
        vit1_score = self.vit_primary.predict(image_rgb) if self.ml_mode else None
        vit2_score = self.vit_deepfake.predict(image_rgb) if self.ml_mode else None

        # Optional Hive API signal
        hive_score = self._call_hive_api(raw_bytes) if raw_bytes else None

        # ── Ensemble Scoring ──
        has_faces = face.get("faces_found", 0) > 0
        face_weight = 0.08 if has_faces else 0.0
        hive_weight = 0.30 if hive_score is not None else 0.0

        if vit1_score is not None or vit2_score is not None:
            ml_scores = [s for s in [vit1_score, vit2_score] if s is not None]
            ml_avg = np.mean(ml_scores)

            ml_w = 0.40 * (1.0 - hive_weight)
            remaining = 1.0 - ml_w - face_weight - hive_weight
            weights = {
                "ml_models": ml_w,
                "frequency": remaining * 0.16,
                "statistical": remaining * 0.16,
                "texture": remaining * 0.12,
                "srm": remaining * 0.16,
                "color": remaining * 0.10,
                "metadata": remaining * 0.30,
            }
            if has_faces:
                weights["face"] = face_weight
            if hive_score is not None:
                weights["hive"] = hive_weight

            ensemble_score = (
                weights["ml_models"] * ml_avg
                + weights["frequency"] * freq["ai_probability"]
                + weights["statistical"] * stat["ai_probability"]
                + weights["texture"] * texture["ai_probability"]
                + weights["srm"] * srm["ai_probability"]
                + weights["color"] * color["ai_probability"]
                + weights["metadata"] * meta["ai_probability"]
                + (weights.get("face", 0) * face.get("ai_probability", 0))
                + (weights.get("hive", 0) * (hive_score or 0))
            )
            mode = "ml_ensemble"
        else:
            remaining = 1.0 - face_weight - hive_weight
            # Heuristic-only weights — metadata is the strongest real-world signal
            weights = {
                "frequency": remaining * 0.14,
                "statistical": remaining * 0.14,
                "texture": remaining * 0.10,
                "srm": remaining * 0.14,
                "color": remaining * 0.10,
                "metadata": remaining * 0.38,
            }
            if has_faces:
                weights["face"] = face_weight
            if hive_score is not None:
                weights["hive"] = hive_weight

            ensemble_score = (
                weights["frequency"] * freq["ai_probability"]
                + weights["statistical"] * stat["ai_probability"]
                + weights["texture"] * texture["ai_probability"]
                + weights["srm"] * srm["ai_probability"]
                + weights["color"] * color["ai_probability"]
                + weights["metadata"] * meta["ai_probability"]
                + (weights.get("face", 0) * face.get("ai_probability", 0))
                + (weights.get("hive", 0) * (hive_score or 0))
            )
            mode = "heuristic_only"

        # Add bonus signals as small adjustments
        ensemble_score += patch.get("ai_probability", 0) * 0.05
        ensemble_score += jpeg_ghost.get("ai_probability", 0) * 0.03
        # New modular signals — added as bonus adjustments
        # New signals only contribute when they are strong (score > 0.15)
        # to avoid pushing borderline cases over the threshold
        for sig, weight in [
            (gan_fp, 0.03),
            (diffusion, 0.02),
            (noise_inc, 0.02),
            (prnu_result, 0.02),
            (copy_move_result, 0.03),
            (azimuthal_result, 0.03),
            (lighting_result, 0.03),
        ]:
            s = sig.get("score", 0)
            if s > 0.20:
                ensemble_score += s * weight
        # ELA kept for details/display but not in ensemble (too marginal, risks false positives)

        # JPEG ghost detection: high ghost score on a JPEG without EXIF = likely re-saved AI image
        ghost_score = jpeg_ghost.get("ghost_score", 0)
        if ghost_score > 0.3 and not meta.get("has_camera_info"):
            ensemble_score += 0.04  # Re-compressed image without camera data

        ensemble_score = min(max(ensemble_score, 0.0), 1.0)

        # Ordered feature vector of every signal (used by meta-classifier + training)
        feature_vector = {
            "frequency": freq.get("ai_probability", 0),
            "statistical": stat.get("ai_probability", 0),
            "texture": texture.get("ai_probability", 0),
            "srm": srm.get("ai_probability", 0),
            "color": color.get("ai_probability", 0),
            "metadata": meta.get("ai_probability", 0),
            "face": face.get("ai_probability", 0) if has_faces else 0.0,
            "jpeg_ghost": jpeg_ghost.get("ai_probability", 0),
            "patch": patch.get("ai_probability", 0),
            "ela": ela.get("ai_probability", 0),
            "gan_fingerprint": gan_fp.get("score", 0),
            "diffusion_artifacts": diffusion.get("score", 0),
            "noise_map": noise_inc.get("score", 0),
            "prnu": prnu_result.get("score", 0),
            "copy_move": copy_move_result.get("score", 0),
            "azimuthal_spectrum": azimuthal_result.get("score", 0),
            "lighting_consistency": lighting_result.get("score", 0),
        }

        # If a trained meta-classifier exists, blend its prediction with the
        # hand-tuned ensemble score (50/50) for a calibrated result.
        meta_prob = self._meta_classifier_predict(feature_vector)
        if meta_prob is not None:
            ensemble_score = 0.5 * ensemble_score + 0.5 * meta_prob
            ensemble_score = min(max(ensemble_score, 0.0), 1.0)

        # Detection threshold calibrated from benchmark results — see BENCHMARK.md
        detection_threshold = 0.33
        verdict = "AI-Generated" if ensemble_score > detection_threshold else "Real/Authentic"
        confidence = ensemble_score if ensemble_score > detection_threshold else (1.0 - ensemble_score)

        details = {
            "frequency_analysis": {
                "ai_score": round(freq["ai_probability"] * 100, 1),
                "spectral_flatness": freq.get("spectral_flatness", 0),
                "power_law_slope": freq.get("power_law_slope", 0),
            },
            "statistical_analysis": {
                "ai_score": round(stat["ai_probability"] * 100, 1),
                "noise_level": stat.get("noise_std", 0),
                "color_correlation": stat.get("color_correlation", 0),
            },
            "texture_analysis": {
                "ai_score": round(texture["ai_probability"] * 100, 1),
                "edge_density": texture.get("edge_density", 0),
                "local_variance": texture.get("avg_local_variance", 0),
            },
            "srm_analysis": {
                "ai_score": round(srm["ai_probability"] * 100, 1),
                "residual_std": srm.get("avg_residual_std", 0),
                "residual_kurtosis": srm.get("avg_residual_kurtosis", 0),
            },
            "color_analysis": {
                "ai_score": round(color["ai_probability"] * 100, 1),
                "chroma_gradient": color.get("lab_chroma_gradient", 0),
                "luma_chroma_ratio": color.get("luma_chroma_ratio", 0),
                "cbcr_correlation": color.get("cbcr_correlation", 0),
            },
            "metadata_analysis": {
                "ai_score": round(meta["ai_probability"] * 100, 1),
                "flags": meta.get("flags", []),
                "dimensions": meta.get("dimensions", ""),
            },
            "ensemble_weights": weights,
            "detection_mode": mode,
        }

        if has_faces:
            details["face_analysis"] = {
                "ai_score": round(face["ai_probability"] * 100, 1),
                "faces_found": face.get("faces_found", 0),
                "face_details": face.get("face_details", []),
            }

        if vit1_score is not None:
            details["ml_model_primary"] = {
                "ai_score": round(vit1_score * 100, 1),
                "model": self.vit_primary.model_name,
            }
        if vit2_score is not None:
            details["ml_model_deepfake"] = {
                "ai_score": round(vit2_score * 100, 1),
                "model": self.vit_deepfake.model_name,
            }
        if hive_score is not None:
            details["hive_api"] = {
                "ai_score": round(hive_score * 100, 1),
                "source": "Hive Moderation API",
            }

        if patch.get("noise_cv") is not None:
            details["patch_analysis"] = {
                "noise_consistency": patch.get("noise_consistency", 0),
                "mean_patch_noise": patch.get("mean_patch_noise", 0),
            }
        if jpeg_ghost.get("compression_type") != "unknown":
            details["jpeg_ghost"] = {
                "ghost_score": jpeg_ghost.get("ghost_score", 0),
                "compression_type": jpeg_ghost.get("compression_type", "unknown"),
            }
        if screenshot.get("is_screenshot"):
            details["screenshot_detected"] = True
            details["screenshot_indicators"] = screenshot.get("indicators", [])
        if ela.get("ela_uniformity", 0) > 0:
            details["ela"] = {"uniformity": ela.get("ela_uniformity", 0), "mean_error": ela.get("ela_mean", 0)}
        # New modular signals
        if gan_fp.get("score", 0) > 0:
            details["gan_fingerprint"] = gan_fp.get("details", {})
            details["gan_fingerprint"]["score"] = gan_fp["score"]
        if diffusion.get("score", 0) > 0:
            details["diffusion_artifacts"] = diffusion.get("details", {})
            details["diffusion_artifacts"]["score"] = diffusion["score"]
        if noise_inc.get("score", 0) > 0:
            details["noise_map"] = noise_inc.get("details", {})
            details["noise_map"]["score"] = noise_inc["score"]
        if prnu_result.get("score", 0) > 0:
            details["prnu"] = prnu_result.get("details", {})
            details["prnu"]["score"] = prnu_result["score"]
        if copy_move_result.get("score", 0) > 0:
            details["copy_move"] = copy_move_result.get("details", {})
            details["copy_move"]["score"] = copy_move_result["score"]
        if azimuthal_result.get("score", 0) > 0:
            details["azimuthal_spectrum"] = azimuthal_result.get("details", {})
            details["azimuthal_spectrum"]["score"] = azimuthal_result["score"]
        if lighting_result.get("score", 0) > 0:
            details["lighting_consistency"] = lighting_result.get("details", {})
            details["lighting_consistency"]["score"] = lighting_result["score"]

        # ── Generate Explanation ──
        explanation = self._generate_explanation(
            verdict,
            ensemble_score,
            freq,
            stat,
            texture,
            srm,
            meta,
            color,
            face,
            vit1_score,
            vit2_score,
            mode,
        )

        # Append screenshot notice if detected
        if screenshot.get("is_screenshot"):
            explanation += " Note: this appears to be a screenshot, not a camera photo. Screenshots lose camera metadata which reduces detection accuracy."

        return {
            "verdict": verdict,
            "confidence": round(confidence * 100, 1),
            "ai_probability": round(ensemble_score * 100, 1),
            "detection_mode": mode,
            "model_version": MODEL_VERSION,
            "explanation": explanation,
            "details": details,
            "feature_vector": feature_vector,
        }

    def _generate_explanation(self, verdict, score, freq, stat, texture, srm, meta, color, face, vit1, vit2, mode):
        """Generate a human-readable explanation of what triggered the detection."""
        reasons = []
        mitigating = []

        # Collect strong signals
        if vit1 is not None and vit1 > 0.6:
            reasons.append(
                f"The ML model (SDXL detector) identified this as AI-generated with {vit1*100:.0f}% confidence"
            )
        if vit2 is not None and vit2 > 0.6:
            reasons.append(f"The deepfake detector flagged this with {vit2*100:.0f}% confidence")

        # Frequency
        fs = freq["ai_probability"]
        if fs > 0.5:
            parts = []
            if freq.get("slope_deviation", 0) > 0.5:
                parts.append("its frequency spectrum deviates from the natural 1/f power law")
            if freq.get("spectral_flatness", 0) > 0.6:
                parts.append("the spectral energy distribution is unusually flat")
            if parts:
                reasons.append("Frequency analysis flagged this because " + " and ".join(parts))
            else:
                reasons.append("Frequency domain analysis detected anomalous spectral patterns")

        # Statistical
        ss = stat["ai_probability"]
        if ss > 0.4:
            parts = []
            if stat.get("noise_std", 10) < 3:
                parts.append(f"very low noise level ({stat['noise_std']:.1f} — real photos typically show 5-15)")
            if stat.get("color_correlation", 0) > 0.95:
                parts.append("unnaturally high color channel correlation")
            if stat.get("noise_consistency", 1) < 0.15:
                parts.append("noise is suspiciously consistent across scales")
            if parts:
                reasons.append("Statistical analysis found " + ", ".join(parts))

        # Texture
        ts = texture["ai_probability"]
        if ts > 0.4:
            parts = []
            if texture.get("edge_density", 1) < 0.06:
                parts.append("very few sharp edges (image is unusually smooth)")
            if texture.get("avg_local_variance", 1000) < 200:
                parts.append("low texture variation (surfaces lack natural micro-detail)")
            if parts:
                reasons.append("Texture analysis detected " + ", ".join(parts))

        # SRM
        srm_s = srm["ai_probability"]
        if srm_s > 0.4:
            parts = []
            if srm.get("avg_residual_std", 10) < 2.5:
                parts.append("noise residuals are weaker than expected from a real camera sensor")
            if srm.get("avg_residual_kurtosis", 0) > 10:
                parts.append("noise pattern has non-Gaussian characteristics unlike camera noise")
            if parts:
                reasons.append("SRM noise fingerprinting found " + ", ".join(parts))

        # Color space
        cs = color["ai_probability"]
        if cs > 0.3:
            parts = []
            if color.get("lab_chroma_gradient", 10) < 1.0:
                parts.append("chrominance channels are unusually smooth (typical of AI generators)")
            if color.get("luma_chroma_ratio", 0) > 5:
                parts.append("luminance-to-chrominance noise ratio is abnormal")
            if parts:
                reasons.append("Color space analysis found " + ", ".join(parts))

        # Face analysis
        if face.get("faces_found", 0) > 0 and face.get("ai_probability", 0) > 0.3:
            parts = []
            for fd in face.get("face_details", []):
                if fd.get("skin_noise", 10) < 3:
                    parts.append("unnaturally smooth skin texture")
                if fd.get("symmetry_diff", 20) < 8:
                    parts.append("face is suspiciously symmetric")
                if fd.get("boundary_gradient", 0) > 20:
                    parts.append("sharp artifacts at face boundary (possible face swap)")
            if parts:
                reasons.append("Face analysis detected " + ", ".join(list(set(parts))[:3]))

        # Metadata
        ms = meta["ai_probability"]
        flags = meta.get("flags", [])
        if "png_no_exif" in flags:
            reasons.append(
                "This is a PNG file with no camera data at all — a very common format for AI-generated images"
            )
        elif "png_no_camera_metadata" in flags:
            reasons.append("PNG file without camera information — often seen in AI outputs")
        elif "no_exif_data" in flags:
            reasons.append("No camera EXIF data found in the file")
        elif "no_camera_metadata" in flags:
            reasons.append("No camera make/model/settings found in the metadata")
        if any("ai_software" in f for f in flags):
            reasons.append("File metadata contains AI generation software tags")
        if any("ai_dimension" in f for f in flags):
            dim = meta.get("dimensions", "")
            reasons.append(f"Image dimensions ({dim}) match common AI generator output sizes")
        if "dimensions_divisible_64" in flags:
            reasons.append("Image dimensions are multiples of 64 — a pattern typical of diffusion model outputs")
        if "jpeg_quality_100" in flags:
            reasons.append("JPEG saved at maximum quality (quality 100) — real cameras never do this")
        elif "standard_jpeg_qtable" in flags:
            reasons.append("JPEG uses standard quantization tables rather than camera-specific ones")

        # Mitigating factors
        if vit1 is not None and vit1 < 0.3:
            mitigating.append("ML model considers this likely authentic")
        if stat.get("noise_std", 0) > 8:
            mitigating.append("natural-looking noise levels present")
        if "has_camera_info" in flags:
            mitigating.append("contains real camera EXIF data (make, model, settings)")
        if "camera_jpeg_qtable" in flags:
            mitigating.append("JPEG uses camera-specific quantization tables")
        if "has_gps" in flags:
            mitigating.append("contains GPS location data")
        if texture.get("edge_density", 0) > 0.15:
            mitigating.append("rich edge detail consistent with real imagery")

        # Build explanation
        if verdict == "AI-Generated":
            if reasons:
                summary = "Key giveaways: " + ". ".join(reasons[:4]) + "."
            else:
                summary = "Multiple subtle signals across frequency, noise, and texture analysis suggest this is AI-generated, though no single factor was dominant."
        else:
            if mitigating:
                summary = "This appears authentic. " + ". ".join(mitigating[:3]) + "."
            else:
                summary = "Analysis did not find strong indicators of AI generation."

            if reasons:
                summary += " Minor flags: " + ". ".join(reasons[:2]) + "."

        return summary


# Singleton
detector = AIImageDetector()
