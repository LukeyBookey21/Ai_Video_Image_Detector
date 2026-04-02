"""
End-to-end test suite — tests the full stack from file creation through API to response parsing.
Requires backend running on localhost:8000.
Usage: python scripts/test_e2e.py
"""

import io
import json
import sys
import time

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

from PIL import Image
from PIL.ExifTags import Base as ExifBase

BASE = "http://localhost:8000"
passed = 0
failed = 0


def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  [PASS] {name}")
    except AssertionError as e:
        failed += 1
        print(f"  [FAIL] {name}: {e}")
    except Exception as e:
        failed += 1
        print(f"  [ERR]  {name}: {e}")


def make_jpeg_with_exif():
    img = Image.new("RGB", (200, 200), (120, 90, 70))
    exif = img.getexif()
    exif[ExifBase.Make] = "Nikon"
    exif[ExifBase.Model] = "D850"
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90, exif=exif.tobytes())
    buf.seek(0)
    return buf


def make_ai_png():
    img = Image.new("RGB", (512, 512), (180, 160, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def main():
    print("=" * 55)
    print("  End-to-End Test Suite")
    print("=" * 55)

    # Check server
    try:
        r = requests.get(f"{BASE}/api/health", timeout=3)
        assert r.status_code == 200
    except Exception:
        print("Backend not running at localhost:8000")
        sys.exit(1)

    print("\n-- Health --")
    test("Health returns status ok", lambda: (
        r := requests.get(f"{BASE}/api/health"),
        assert r.status_code == 200,
        assert r.json()["status"] == "ok",
    ))

    print("\n-- Real photo detection --")
    def test_real_photo():
        r = requests.post(f"{BASE}/api/detect", files={"file": ("photo.jpg", make_jpeg_with_exif(), "image/jpeg")})
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        assert "verdict" in data, "No verdict in response"
        assert data["verdict"] == "Real/Authentic", f"Got {data['verdict']} (prob={data.get('ai_probability')})"
        assert "confidence" in data
        assert "explanation" in data
    test("JPEG with Nikon EXIF detected as real", test_real_photo)

    print("\n-- AI image detection --")
    def test_ai_png():
        r = requests.post(f"{BASE}/api/detect", files={"file": ("ai_art.png", make_ai_png(), "image/png")})
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        assert "verdict" in data
        # PNG with no EXIF at AI dimensions should be flagged
        assert data["ai_probability"] > 25, f"AI prob too low: {data['ai_probability']}"
    test("PNG 512x512 no EXIF gets high AI probability", test_ai_png)

    print("\n-- Caching --")
    def test_cache():
        buf = make_jpeg_with_exif()
        content = buf.read()
        # First request
        r1 = requests.post(f"{BASE}/api/detect", files={"file": ("test.jpg", io.BytesIO(content), "image/jpeg")})
        assert r1.status_code == 200
        # Second request with same content
        r2 = requests.post(f"{BASE}/api/detect", files={"file": ("test.jpg", io.BytesIO(content), "image/jpeg")})
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2.get("cached") == True, "Second request should be cached"
    test("Duplicate upload returns cached result", test_cache)

    print("\n-- Batch upload --")
    def test_batch():
        files = [
            ("files", ("a.jpg", make_jpeg_with_exif(), "image/jpeg")),
            ("files", ("b.png", make_ai_png(), "image/png")),
        ]
        r = requests.post(f"{BASE}/api/detect/batch", files=files)
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        assert data["total"] == 2, f"Expected 2 results, got {data['total']}"
        assert len(data["results"]) == 2
    test("Batch upload processes 2 files", test_batch)

    print("\n-- Error handling --")
    test("Missing file returns 422", lambda: (
        r := requests.post(f"{BASE}/api/detect"),
        assert r.status_code == 422,
    ))
    test("Invalid file type returns 400", lambda: (
        r := requests.post(f"{BASE}/api/detect", files={"file": ("bad.txt", io.BytesIO(b"hello"), "text/plain")}),
        assert r.status_code == 400,
    ))

    print("\n-- Stats --")
    def test_stats():
        r = requests.get(f"{BASE}/api/stats")
        assert r.status_code == 200
        data = r.json()
        assert "total_analyses" in data
        assert data["total_analyses"] > 0, "Should have at least 1 analysis from previous tests"
    test("Stats endpoint returns counters", test_stats)

    print("\n-- Metrics --")
    def test_metrics():
        r = requests.get(f"{BASE}/metrics")
        assert r.status_code == 200
        assert "ai_detector_analyses_total" in r.text
    test("Prometheus metrics endpoint works", test_metrics)

    print(f"\n{'=' * 55}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'=' * 55}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
