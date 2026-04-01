"""
Pixel-Level AI Artifact Heatmap Generator

Divides the image into a grid of patches and scores each patch independently.
Returns a heatmap showing WHERE the AI artifacts are concentrated.
Uses frequency + noise + texture signals per patch.
"""

import base64
import io
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from scipy.fft import dctn
from scipy.ndimage import uniform_filter
from scipy.stats import kurtosis


def generate_heatmap(image: Image.Image, grid_size: int = 16) -> dict:
    """Analyze image in a grid and return per-patch AI scores + rendered heatmap."""
    img_rgb = image.convert("RGB")
    w, h = img_rgb.size

    # Ensure minimum size
    if w < 64 or h < 64:
        return {"heatmap_grid": [], "heatmap_image": None}

    patch_w = w // grid_size
    patch_h = h // grid_size

    if patch_w < 8 or patch_h < 8:
        grid_size = min(w // 8, h // 8, 8)
        patch_w = w // grid_size
        patch_h = h // grid_size

    grid_scores = []

    for row in range(grid_size):
        row_scores = []
        for col in range(grid_size):
            x1 = col * patch_w
            y1 = row * patch_h
            x2 = min(x1 + patch_w, w)
            y2 = min(y1 + patch_h, h)

            patch = img_rgb.crop((x1, y1, x2, y2))
            score = _analyze_patch(patch)
            row_scores.append(round(score, 3))

        grid_scores.append(row_scores)

    # Render heatmap overlay
    heatmap_b64 = _render_heatmap(img_rgb, grid_scores, grid_size, patch_w, patch_h)

    return {
        "heatmap_grid": grid_scores,
        "heatmap_image": heatmap_b64,
        "grid_size": grid_size,
        "patch_size": f"{patch_w}x{patch_h}",
    }


def _analyze_patch(patch: Image.Image) -> float:
    """Score a single image patch for AI likelihood (0.0 to 1.0)."""
    arr = np.array(patch.convert("L").resize((32, 32)), dtype=np.float64)

    score = 0.0

    # 1. DCT flatness
    dct = dctn(arr, norm="ortho")
    mag = np.abs(dct)
    high = mag[16:, 16:]
    low = mag[:8, :8]
    ratio = np.mean(high) / (np.mean(low) + 1e-10)
    if ratio < 0.005:
        score += 0.3
    elif ratio < 0.02:
        score += 0.15

    # 2. Local variance (smoothness)
    local_var = np.var(arr)
    if local_var < 50:
        score += 0.25
    elif local_var < 200:
        score += 0.12

    # 3. Noise level
    blurred = np.array(patch.convert("L").resize((32, 32)).filter(ImageFilter.GaussianBlur(radius=1)), dtype=np.float64)
    noise_std = np.std(arr - blurred)
    if noise_std < 1.5:
        score += 0.25
    elif noise_std < 3.0:
        score += 0.12

    # 4. Edge density
    edges = np.abs(np.diff(arr, axis=0))
    edge_density = np.mean(edges > 10)
    if edge_density < 0.05:
        score += 0.15

    return min(score, 1.0)


def _render_heatmap(image: Image.Image, grid: list, grid_size: int, patch_w: int, patch_h: int) -> str:
    """Render a colored heatmap overlay and return as base64 PNG."""
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for row in range(len(grid)):
        for col in range(len(grid[row])):
            score = grid[row][col]
            x1 = col * patch_w
            y1 = row * patch_h
            x2 = x1 + patch_w
            y2 = y1 + patch_h

            # Color: green (safe) → yellow → red (AI)
            if score > 0.6:
                r, g, b = 255, int(60 * (1 - score)), 0
            elif score > 0.3:
                t = (score - 0.3) / 0.3
                r, g, b = int(255 * t), 255, 0
            else:
                r, g, b = 0, int(200 + 55 * score / 0.3), 0

            alpha = int(80 + 100 * score)  # More opaque for higher scores
            draw.rectangle([x1, y1, x2, y2], fill=(r, g, b, alpha))

    # Composite
    result = Image.alpha_composite(image.convert("RGBA"), overlay)
    result = result.convert("RGB")

    buf = io.BytesIO()
    result.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
