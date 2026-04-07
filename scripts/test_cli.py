"""
Test the CLI tool.
Usage: python scripts/test_cli.py
"""

import io
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image
from PIL.ExifTags import Base as ExifBase

PASS = 0
FAIL = 0
CLI = os.path.join(os.path.dirname(__file__), "..", "cli.py")


def test(name, cmd, expect_exit=0, expect_contains=None, expect_not_contains=None):
    global PASS, FAIL
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    ok = result.returncode == expect_exit
    output = result.stdout + result.stderr

    if ok and expect_contains:
        if expect_contains not in output:
            ok = False

    if ok and expect_not_contains:
        if expect_not_contains in output:
            ok = False

    status = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{status}] {name}")
    if not ok:
        print(f"         Exit: {result.returncode} (expected {expect_exit})")
        print(f"         Output: {output[:200]}")


def make_test_jpeg():
    import numpy as np

    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    # Create a realistic-looking image with noise and texture
    rng = np.random.RandomState(42)
    arr = np.zeros((400, 600, 3), dtype=np.float64)
    for c in range(3):
        base = rng.randint(60, 180)
        grad = np.linspace(base - 40, base + 40, 400).reshape(-1, 1)
        arr[:, :, c] = grad + rng.randn(400, 600) * 12
    # Add objects for texture
    for _ in range(8):
        cx, cy = rng.randint(0, 600), rng.randint(0, 400)
        r = rng.randint(20, 80)
        col = rng.randint(30, 220, 3).astype(np.float64)
        yy, xx = np.ogrid[-cy : 400 - cy, -cx : 600 - cx]
        mask = xx**2 + yy**2 <= r**2
        for c in range(3):
            arr[:, :, c][mask] = col[c] + rng.randn(mask.sum()) * 10
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    exif = img.getexif()
    exif[ExifBase.Make] = "Canon"
    exif[ExifBase.Model] = "EOS R5"
    exif[ExifBase.DateTime] = "2024:06:15 14:30:00"
    img.save(path, format="JPEG", quality=90, exif=exif.tobytes())
    return path


def make_test_png():
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img = Image.new("RGB", (512, 512), (100, 150, 200))
    img.save(path, format="PNG")
    return path


def main():
    print("=" * 55)
    print("  CLI Tool Tests")
    print("=" * 55)

    jpeg_path = make_test_jpeg()
    png_path = make_test_png()

    try:
        test("--help shows usage", [sys.executable, CLI, "--help"], expect_exit=0, expect_contains="Check")

        test(
            "Single JPEG returns Real",
            [sys.executable, CLI, jpeg_path],
            expect_exit=0,
            expect_contains="Real/Authentic",
        )

        test(
            "Single PNG returns AI-Generated",
            [sys.executable, CLI, png_path],
            expect_exit=0,
            expect_contains="AI-Generated",
        )

        test(
            "Verbose mode shows signals",
            [sys.executable, CLI, "-v", jpeg_path],
            expect_exit=0,
            expect_contains="Signals",
        )

        test(
            "JSON output is valid JSON",
            [sys.executable, CLI, "--json", jpeg_path],
            expect_exit=0,
            expect_contains='"verdict"',
        )

        test(
            "Multiple files shows summary",
            [sys.executable, CLI, jpeg_path, png_path],
            expect_exit=0,
            expect_contains="files checked",
        )

        test(
            "Nonexistent file warns",
            [sys.executable, CLI, "does_not_exist.jpg"],
            expect_exit=1,
            expect_contains="not found",
        )

    finally:
        os.unlink(jpeg_path)
        os.unlink(png_path)

    print(f"\n{'=' * 55}")
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print(f"{'=' * 55}")

    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
