"""
Integration tests for the API endpoints.
Requires the backend to be running on localhost:8000.
Usage: python scripts/test_api.py
"""

import io
import json
import sys

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0


def test(name, response, expect_status, expect_contains=None):
    global PASS, FAIL
    ok = response.status_code == expect_status
    if expect_contains and ok:
        body = response.text
        if expect_contains not in body:
            ok = False

    status = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{status}] {name} (HTTP {response.status_code})")
    if not ok:
        print(f"         Expected {expect_status}, got {response.status_code}")
        print(f"         Body: {response.text[:200]}")


def create_test_jpeg():
    """Create a minimal valid JPEG in memory."""
    from PIL import Image
    from PIL.ExifTags import Base as ExifBase

    img = Image.new("RGB", (100, 100), (128, 100, 80))
    exif = img.getexif()
    exif[ExifBase.Make] = "TestCamera"
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80, exif=exif.tobytes())
    buf.seek(0)
    return buf


def create_test_png():
    """Create a minimal valid PNG in memory (no EXIF)."""
    from PIL import Image

    img = Image.new("RGB", (512, 512), (100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def main():
    print("=" * 55)
    print("  API Integration Tests")
    print("=" * 55)

    # Check server is up
    try:
        r = requests.get(f"{BASE}/api/health", timeout=5)
        if r.status_code != 200:
            print("Backend not responding. Start it first: python backend/main.py")
            sys.exit(1)
    except Exception:
        print("Cannot connect to backend at localhost:8000")
        sys.exit(1)

    print("\n-- Health & Info --")
    test("GET /api/health", requests.get(f"{BASE}/api/health"), 200, '"status":"ok"')
    test("GET /api/stats", requests.get(f"{BASE}/api/stats"), 200, "total_analyses")
    test("GET /api/docs", requests.get(f"{BASE}/api/docs"), 200, "AI Detector API")

    print("\n-- File Upload --")
    test(
        "POST /api/detect with valid JPEG",
        requests.post(f"{BASE}/api/detect", files={"file": ("test.jpg", create_test_jpeg(), "image/jpeg")}),
        200,
        "verdict",
    )
    test(
        "POST /api/detect with valid PNG",
        requests.post(f"{BASE}/api/detect", files={"file": ("test.png", create_test_png(), "image/png")}),
        200,
        "verdict",
    )
    test(
        "POST /api/detect with no file",
        requests.post(f"{BASE}/api/detect"),
        422,
    )
    test(
        "POST /api/detect with text file as JPEG",
        requests.post(f"{BASE}/api/detect", files={"file": ("fake.jpg", io.BytesIO(b"not an image"), "image/jpeg")}),
        400,
        "INVALID_FILE_TYPE",
    )

    print("\n-- URL Analysis --")
    test(
        "POST /api/detect-url with localhost (SSRF)",
        requests.post(f"{BASE}/api/detect-url", json={"url": "http://localhost:8000/api/health"}),
        400,
        "URL_NOT_ALLOWED",
    )
    test(
        "POST /api/detect-url with private IP (SSRF)",
        requests.post(f"{BASE}/api/detect-url", json={"url": "http://192.168.1.1/image.png"}),
        400,
        "URL_NOT_ALLOWED",
    )
    test(
        "POST /api/detect-url with invalid scheme",
        requests.post(f"{BASE}/api/detect-url", json={"url": "ftp://example.com/file.png"}),
        400,
    )

    print("\n-- Waitlist --")
    test(
        "POST /api/waitlist with valid email",
        requests.post(f"{BASE}/api/waitlist", json={"email": f"apitest_{id(main)}@test.com"}),
        200,
    )
    test(
        "POST /api/waitlist with invalid email",
        requests.post(f"{BASE}/api/waitlist", json={"email": "not-an-email"}),
        422,
    )

    print("\n-- Developer API Auth --")
    test(
        "POST /api/v1/detect without key",
        requests.post(f"{BASE}/api/v1/detect", files={"file": ("t.jpg", create_test_jpeg(), "image/jpeg")}),
        401,
    )
    test(
        "GET /api/v1/usage without key",
        requests.get(f"{BASE}/api/v1/usage"),
        401,
    )
    test(
        "POST /api/v1/detect with bad key",
        requests.post(
            f"{BASE}/api/v1/detect",
            files={"file": ("t.jpg", create_test_jpeg(), "image/jpeg")},
            headers={"X-API-Key": "invalid-key"},
        ),
        401,
    )

    print("\n-- Security --")
    test(
        "Path traversal in filename",
        requests.post(
            f"{BASE}/api/detect",
            files={"file": ("../../etc/passwd", create_test_jpeg(), "image/jpeg")},
        ),
        400,
    )
    test(
        "Long filename (10000 chars)",
        requests.post(
            f"{BASE}/api/detect",
            files={"file": ("A" * 10000 + ".jpg", create_test_jpeg(), "image/jpeg")},
        ),
        400,
    )

    print(f"\n{'=' * 55}")
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print(f"{'=' * 55}")

    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
