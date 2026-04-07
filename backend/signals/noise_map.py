"""
Noise Inconsistency Map

Slides a window across the image and computes local noise variance per channel.
Flags regions where variance is abnormally uniform (inpainting) or
discontinuous (compositing/AI generation).
"""

import numpy as np
from PIL import Image
from scipy.ndimage import median_filter


def analyze(image: Image.Image) -> dict:
    """Detect noise inconsistencies across image regions."""
    try:
        img = np.array(image.convert("RGB").resize((256, 256)), dtype=np.float64)
        h, w, c = img.shape
        block = 32

        channel_maps = []
        for ch in range(c):
            channel = img[:, :, ch]
            smoothed = median_filter(channel, size=3)
            noise = channel - smoothed

            # Compute local noise variance in blocks
            variances = []
            for y in range(0, h - block, block // 2):
                row = []
                for x in range(0, w - block, block // 2):
                    patch_noise = noise[y:y+block, x:x+block]
                    row.append(np.var(patch_noise))
                variances.append(row)

            channel_maps.append(np.array(variances))

        # Average across channels
        noise_map = np.mean(channel_maps, axis=0)

        if noise_map.size < 4:
            return {"signal_name": "noise_map", "score": 0.0, "confidence": 0.0, "details": {}}

        # Compute statistics
        map_mean = np.mean(noise_map)
        map_std = np.std(noise_map)
        map_cv = map_std / (map_mean + 1e-10)

        # Min/max ratio — high ratio = inconsistent noise
        map_min = np.min(noise_map[noise_map > 0]) if np.any(noise_map > 0) else 0
        map_max = np.max(noise_map)
        variance_ratio = map_max / (map_min + 1e-10)

        scores = []

        # Very uniform noise = AI-generated (everything from same process)
        if map_cv < 0.3:
            scores.append(0.15)
        elif map_cv < 0.5:
            scores.append(0.08)

        # Very inconsistent noise = compositing or inpainting
        if variance_ratio > 20:
            scores.append(0.12)
        elif variance_ratio > 10:
            scores.append(0.06)

        # Very low overall noise = AI smoothness
        if map_mean < 5.0:
            scores.append(0.10)

        score = min(sum(scores), 1.0)
        confidence = min(score * 1.5, 1.0)

        return {
            "signal_name": "noise_map",
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "details": {
                "noise_cv": round(float(map_cv), 4),
                "variance_ratio": round(float(variance_ratio), 4),
                "mean_noise_level": round(float(map_mean), 4),
            },
        }
    except Exception:
        return {"signal_name": "noise_map", "score": 0.0, "confidence": 0.0, "details": {}}
