"""Comprehensive test of the multi-signal detection pipeline."""

import io
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from PIL.ExifTags import Base as ExifBase
from detector import detector


def create_real_photo_like():
    """Simulate a natural photo: high noise, varied texture, saved as JPEG with EXIF."""
    np.random.seed(42)
    arr = np.zeros((512, 512, 3), dtype=np.float64)
    for i in range(512):
        arr[i, :, 0] = 100 + (i / 512) * 80
        arr[i, :, 1] = 140 + (i / 512) * 60
        arr[i, :, 2] = 200 - (i / 512) * 40

    arr += np.random.normal(0, 14, arr.shape)
    arr += np.random.poisson(4, arr.shape).astype(np.float64)
    arr[200:350, 150:400, :] = arr[200:350, 150:400, :] * 0.5 + 40
    arr[100:140, 300:450, :] = arr[100:140, 300:450, :] * 0.7 + 30
    arr[380:420, 50:200, :] = np.random.randint(60, 120, (40, 150, 3))
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(radius=0.5))

    # Add EXIF data to simulate a real camera photo
    exif = img.getexif()
    exif[ExifBase.Make] = "Canon"
    exif[ExifBase.Model] = "Canon EOS 5D"
    exif[ExifBase.DateTime] = "2024:06:15 14:30:00"

    # Save as JPEG to get real JPEG format + EXIF
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92, exif=exif.tobytes())
    buf.seek(0)
    return Image.open(buf), buf.getvalue()


def create_ai_smooth():
    """Simulate AI-generated: very smooth, low noise, high color correlation, PNG format."""
    arr = np.zeros((512, 512, 3), dtype=np.float64)
    for i in range(512):
        for j in range(512):
            arr[i, j, 0] = 128 + 80 * np.sin(i / 50) * np.cos(j / 60)
            arr[i, j, 1] = 128 + 80 * np.sin(i / 50 + 0.5) * np.cos(j / 60 + 0.3)
            arr[i, j, 2] = 128 + 80 * np.sin(i / 50 + 1.0) * np.cos(j / 60 + 0.6)
    arr += np.random.normal(0, 1.0, arr.shape)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Image.open(buf), buf.getvalue()


def create_ai_portrait():
    """Simulate AI portrait: smooth skin, 1024x1024 (common AI dimension), PNG."""
    img = Image.new("RGB", (1024, 1024), (180, 150, 130))
    arr = np.array(img, dtype=np.float64)
    for i in range(1024):
        arr[i, :, 0] = 200 - i / 10
        arr[i, :, 1] = 180 - i / 12
        arr[i, :, 2] = 220 - i / 8
    for i in range(300, 700):
        for j in range(350, 650):
            dist = np.sqrt(((i - 500) / 200) ** 2 + ((j - 500) / 150) ** 2)
            if dist < 1:
                arr[i, j] = [210 - dist * 30, 180 - dist * 20, 160 - dist * 15]
    arr += np.random.normal(0, 0.8, arr.shape)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Image.open(buf), buf.getvalue()


def create_real_noisy():
    """Simulate low-light phone photo: high ISO, saved as JPEG with phone EXIF."""
    np.random.seed(99)
    arr = np.random.randint(30, 60, (512, 512, 3), dtype=np.uint8).astype(np.float64)
    arr += np.random.normal(0, 20, arr.shape)
    arr[:, :, 0] += 15
    arr[:, :, 2] -= 10
    for _ in range(5):
        cx, cy = np.random.randint(50, 462, 2)
        rr = np.random.randint(10, 30)
        for i in range(max(0, cx - rr), min(512, cx + rr)):
            for j in range(max(0, cy - rr), min(512, cy + rr)):
                d = np.sqrt((i - cx) ** 2 + (j - cy) ** 2)
                if d < rr:
                    arr[i, j] += (1 - d / rr) * 150
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    exif = img.getexif()
    exif[ExifBase.Make] = "Apple"
    exif[ExifBase.Model] = "iPhone 14 Pro"
    exif[ExifBase.DateTime] = "2024:12:01 22:45:10"

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, exif=exif.tobytes())
    buf.seek(0)
    return Image.open(buf), buf.getvalue()


def test_image(name, image, raw_bytes, expected=None):
    start = time.time()
    result = detector.detect_image(image, raw_bytes=raw_bytes)
    elapsed = time.time() - start

    d = result["details"]
    status = ""
    if expected:
        status = "PASS" if result["verdict"] == expected else "FAIL"

    print(f"\n{'─' * 55}")
    print(f"  {name}")
    if expected:
        print(f"  [{status}] Expected: {expected}")
    print(f"{'─' * 55}")
    print(f"  Verdict:        {result['verdict']}")
    print(f"  Confidence:     {result['confidence']}%")
    print(f"  AI Probability: {result['ai_probability']}%")
    print(f"  Mode:           {result['detection_mode']}")
    print(f"  ── Signal Breakdown ──")
    if "ml_model_primary" in d:
        print(f"  ML Primary:     {d['ml_model_primary']['ai_score']}%")
    if "ml_model_deepfake" in d:
        print(f"  ML Deepfake:    {d['ml_model_deepfake']['ai_score']}%")
    print(f"  Frequency:      {d['frequency_analysis']['ai_score']}%")
    print(f"  Statistical:    {d['statistical_analysis']['ai_score']}%")
    print(f"  Texture:        {d['texture_analysis']['ai_score']}%")
    print(f"  SRM:            {d['srm_analysis']['ai_score']}%")
    print(f"  Metadata:       {d['metadata_analysis']['ai_score']}%")
    if d["metadata_analysis"].get("flags"):
        print(f"  Meta Flags:     {', '.join(d['metadata_analysis']['flags'])}")
    print(f"  Time:           {elapsed:.3f}s")
    return result


def main():
    print("=" * 55)
    print("  AI Detector — Multi-Signal Ensemble Test")
    print("=" * 55)

    test_cases = [
        ("Real Photo (JPEG + Canon EXIF)", *create_real_photo_like(), "Real/Authentic"),
        ("AI Smooth Gradients (PNG, no EXIF)", *create_ai_smooth(), "AI-Generated"),
        ("AI Portrait 1024x1024 (PNG, no EXIF)", *create_ai_portrait(), "AI-Generated"),
        ("Real Low-Light (JPEG + iPhone EXIF)", *create_real_noisy(), "Real/Authentic"),
    ]

    passes = 0
    total = 0
    for name, img, raw, expected in test_cases:
        r = test_image(name, img, raw, expected)
        total += 1
        if r["verdict"] == expected:
            passes += 1

    print(f"\n{'=' * 55}")
    print(f"  Results: {passes}/{total} passed")
    print(f"{'=' * 55}")

    if passes < total:
        exit(1)


if __name__ == "__main__":
    main()
