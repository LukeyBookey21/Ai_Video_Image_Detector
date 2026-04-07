"""
Diffusion Model Artifact Detector

Detects signatures specific to diffusion model (Stable Diffusion, DALL-E, Midjourney) outputs:
1. Smooth gradient banding in mid-tones
2. Over-sharpened edges compared to surrounding flat regions
3. "Painterly" texture in flat regions (low local entropy)
"""

import numpy as np
from PIL import Image, ImageFilter
from scipy.stats import entropy as scipy_entropy


def analyze(image: Image.Image) -> dict:
    """Detect diffusion model-specific artifacts."""
    try:
        img = np.array(image.convert("RGB").resize((512, 512)), dtype=np.float64)
        gray = np.mean(img, axis=2)

        scores = []

        # 1. Gradient banding detection
        # Diffusion models produce smoother gradients than cameras
        # Compute gradient magnitude histogram — AI has lower variance in mid-tones
        gy, gx = np.gradient(gray)
        grad_mag = np.sqrt(gx**2 + gy**2)

        # Mid-tone gradient analysis (most revealing region)
        mid_mask = (gray > 60) & (gray < 200)
        if np.sum(mid_mask) > 100:
            mid_grads = grad_mag[mid_mask]
            grad_std = np.std(mid_grads)
            grad_mean = np.mean(mid_grads)

            # AI images have lower gradient variance in mid-tones
            if grad_std < 3.0 and grad_mean < 5.0:
                scores.append(0.15)
            elif grad_std < 5.0 and grad_mean < 8.0:
                scores.append(0.08)

        # 2. Edge sharpness analysis
        # Diffusion models can produce over-sharpened edges
        from scipy.ndimage import laplace
        lap = np.abs(laplace(gray))

        # Find edges (high Laplacian) and flat regions (low Laplacian)
        edge_threshold = np.percentile(lap, 95)
        flat_threshold = np.percentile(lap, 50)

        edge_response = np.mean(lap[lap > edge_threshold])
        flat_response = np.mean(lap[lap < flat_threshold])

        edge_contrast = edge_response / (flat_response + 1e-10)

        # Very high edge contrast = over-sharpened (diffusion artifact)
        if edge_contrast > 50:
            scores.append(0.12)
        elif edge_contrast > 30:
            scores.append(0.06)

        # 3. Local entropy analysis ("painterly" texture)
        # Diffusion models produce unnaturally low entropy in flat regions
        block_size = 16
        h, w = gray.shape
        entropies = []
        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = gray[y:y+block_size, x:x+block_size].flatten()
                hist, _ = np.histogram(block, bins=32, range=(0, 255))
                hist = hist / (hist.sum() + 1e-10)
                e = scipy_entropy(hist + 1e-10)
                entropies.append(e)

        if entropies:
            entropy_array = np.array(entropies)
            low_entropy_ratio = np.sum(entropy_array < 1.5) / len(entropy_array)

            # Many low-entropy blocks = flat "painterly" regions
            if low_entropy_ratio > 0.5:
                scores.append(0.12)
            elif low_entropy_ratio > 0.3:
                scores.append(0.06)

        score = min(sum(scores), 1.0)
        confidence = min(score * 1.5, 1.0)

        return {
            "signal_name": "diffusion_artifacts",
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "details": {
                "gradient_banding": round(float(grad_std) if 'grad_std' in dir() else 0, 4),
                "edge_contrast": round(float(edge_contrast), 4),
                "low_entropy_ratio": round(float(low_entropy_ratio) if 'low_entropy_ratio' in dir() else 0, 4),
            },
        }
    except Exception:
        return {"signal_name": "diffusion_artifacts", "score": 0.0, "confidence": 0.0, "details": {}}
