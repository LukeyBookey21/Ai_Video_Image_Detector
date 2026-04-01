"""
Generate synthetic test data for benchmarking.
Creates 100 'real-like' and 100 'AI-like' images using known statistical properties.
Ideally, replace with CIFAKE dataset: load_dataset("CIFAKE/CIFAKE", split="test")

Usage: python scripts/download_test_data.py
"""

import os
import sys
import numpy as np
from PIL import Image, ImageFilter

REAL_DIR = os.path.join(os.path.dirname(__file__), "..", "test_data", "real")
AI_DIR = os.path.join(os.path.dirname(__file__), "..", "test_data", "ai_generated")


def make_real_image(seed: int) -> Image.Image:
    """Simulate a real photograph: natural noise, varied textures, EXIF-like properties."""
    rng = np.random.RandomState(seed)
    # Start with natural-looking gradient + texture
    h, w = 256, 256
    base = rng.randint(40, 200, size=3)
    img = np.zeros((h, w, 3), dtype=np.float64)
    for c in range(3):
        grad = np.linspace(base[c] - 30, base[c] + 30, h).reshape(-1, 1)
        img[:, :, c] = grad + rng.randn(h, w) * 12  # natural sensor noise
    # Add edges / detail (real photos have strong edges)
    for _ in range(rng.randint(5, 15)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        r = rng.randint(10, 60)
        color = rng.randint(0, 255, 3).astype(np.float64)
        yy, xx = np.ogrid[-y : h - y, -x : w - x]
        mask = xx**2 + yy**2 <= r**2
        for c in range(3):
            img[:, :, c][mask] = color[c] + rng.randn(mask.sum()) * 8
    img = np.clip(img, 0, 255).astype(np.uint8)
    pil_img = Image.fromarray(img)
    # Slight JPEG-like compression artifacts (real photos often JPEG)
    return pil_img.filter(ImageFilter.SHARPEN)


def make_ai_image(seed: int) -> Image.Image:
    """Simulate an AI-generated image: smooth, low noise, uniform gradients."""
    rng = np.random.RandomState(seed + 10000)
    h, w = 256, 256  # Common AI generation size
    # Very smooth gradients (AI hallmark)
    img = np.zeros((h, w, 3), dtype=np.float64)
    for c in range(3):
        center = rng.randint(80, 200)
        x_grad = np.linspace(center - 40, center + 40, w)
        y_grad = np.linspace(center - 20, center + 20, h).reshape(-1, 1)
        img[:, :, c] = (x_grad + y_grad) / 2 + rng.randn(h, w) * 1.5  # very low noise
    # Smooth blobs (AI style)
    for _ in range(rng.randint(3, 8)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        r = rng.randint(20, 80)
        color = rng.randint(50, 220, 3).astype(np.float64)
        yy, xx = np.ogrid[-y : h - y, -x : w - x]
        dist = np.sqrt(xx**2 + yy**2)
        mask = dist <= r
        blend = np.clip(1.0 - dist[mask] / r, 0, 1)
        for c in range(3):
            img[:, :, c][mask] = img[:, :, c][mask] * (1 - blend) + color[c] * blend
    img = np.clip(img, 0, 255).astype(np.uint8)
    pil_img = Image.fromarray(img)
    return pil_img.filter(ImageFilter.GaussianBlur(radius=1))


def main():
    os.makedirs(REAL_DIR, exist_ok=True)
    os.makedirs(AI_DIR, exist_ok=True)

    print("Generating 100 synthetic 'real' images...")
    for i in range(100):
        img = make_real_image(i)
        img.save(os.path.join(REAL_DIR, f"real_{i:04d}.png"))
    print(f"  Saved to {REAL_DIR}")

    print("Generating 100 synthetic 'AI' images...")
    for i in range(100):
        img = make_ai_image(i)
        img.save(os.path.join(AI_DIR, f"ai_{i:04d}.png"))
    print(f"  Saved to {AI_DIR}")

    print("Done: 200 test images generated.")


if __name__ == "__main__":
    main()
