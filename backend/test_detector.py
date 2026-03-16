"""Test the detection pipeline with synthetic test images."""

import time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from detector import detector


def create_photo_like():
    """Simulate a natural photo with realistic noise and texture."""
    np.random.seed(42)
    # Start with a gradient (sky-like)
    arr = np.zeros((512, 512, 3), dtype=np.float64)
    for i in range(512):
        arr[i, :, 0] = 100 + (i / 512) * 80  # R gradient
        arr[i, :, 1] = 140 + (i / 512) * 60  # G gradient
        arr[i, :, 2] = 200 - (i / 512) * 40  # B gradient

    # Add realistic noise (Gaussian + shot noise)
    arr += np.random.normal(0, 12, arr.shape)
    arr += np.random.poisson(3, arr.shape).astype(np.float64)

    # Add some structure (rectangles, circles)
    arr[200:350, 150:400, :] = arr[200:350, 150:400, :] * 0.5 + 40
    arr[100:140, 300:450, :] = arr[100:140, 300:450, :] * 0.7 + 30

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    # Apply slight blur to simulate lens
    return img.filter(ImageFilter.GaussianBlur(radius=0.5))


def create_ai_like():
    """Simulate an AI-generated image: smooth gradients, low noise, high color correlation."""
    arr = np.zeros((512, 512, 3), dtype=np.float64)

    # Very smooth gradients (typical of AI images)
    for i in range(512):
        for j in range(512):
            arr[i, j, 0] = 128 + 80 * np.sin(i / 50) * np.cos(j / 60)
            arr[i, j, 1] = 128 + 80 * np.sin(i / 50 + 0.5) * np.cos(j / 60 + 0.3)
            arr[i, j, 2] = 128 + 80 * np.sin(i / 50 + 1.0) * np.cos(j / 60 + 0.6)

    # Very minimal noise (AI characteristic)
    arr += np.random.normal(0, 1.5, arr.shape)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def create_flat_image():
    """Solid color with minor variation — should be ambiguous."""
    arr = np.full((512, 512, 3), 128, dtype=np.uint8)
    arr = arr.astype(np.float64) + np.random.normal(0, 2, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def test_image(name, image):
    start = time.time()
    result = detector.detect_image(image)
    elapsed = time.time() - start

    print(f"\n{'─' * 50}")
    print(f"  {name}")
    print(f"{'─' * 50}")
    print(f"  Verdict:        {result['verdict']}")
    print(f"  Confidence:     {result['confidence']}%")
    print(f"  AI Probability: {result['ai_probability']}%")
    print(f"  ── Breakdown ──")
    d = result["details"]
    print(f"  Frequency:      {d['frequency_analysis']['ai_score']}%  (slope={d['frequency_analysis']['power_law_slope']})")
    print(f"  Statistical:    {d['statistical_analysis']['ai_score']}%  (noise={d['statistical_analysis']['noise_level']})")
    print(f"  Texture:        {d['texture_analysis']['ai_score']}%  (edges={d['texture_analysis']['edge_density']})")
    print(f"  Time:           {elapsed:.3f}s")
    return result


def main():
    print("=" * 50)
    print("  AI Image Detector — Pipeline Test")
    print("=" * 50)

    r1 = test_image("Photo-like (should be Real)", create_photo_like())
    r2 = test_image("AI-like smooth (should be AI)", create_ai_like())
    r3 = test_image("Flat/ambiguous image", create_flat_image())

    print(f"\n{'=' * 50}")
    print("  Summary")
    print(f"{'=' * 50}")
    results = [
        ("Photo-like", r1, "Real/Authentic"),
        ("AI-like", r2, "AI-Generated"),
    ]
    all_pass = True
    for name, r, expected in results:
        status = "PASS" if r["verdict"] == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  {status}: {name} → {r['verdict']} (expected {expected})")

    print(f"\n  Pipeline status: {'ALL PASS' if all_pass else 'SOME FAILED'}")
    print("=" * 50)


if __name__ == "__main__":
    main()
