"""
Analyze redundancy between detection signals.

Runs the detector over one or more folders of images, collects every
signal's raw score into a matrix, and computes the pairwise Pearson
correlation across signals. Highly correlated signal pairs add little
independent information, so this report flags them for down-weighting.

Usage:
    python scripts/analyze_redundancy.py <image_dir1> [<image_dir2> ...]

Output:
    - Correlation table (signals x signals) printed to stdout.
    - Redundant pairs with |correlation| > 0.85.
    - Per-signal mean score and fire rate (score > 0.3).
    - models/signal_correlations.json with the full matrix + redundant pairs.

Pure numpy + PIL. No sklearn, no pandas.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import numpy as np
from PIL import Image
from detector import detector as ai_detector
from detector import AIImageDetector

# Canonical signal order — matches the detector's feature vector / training.
SIGNALS = AIImageDetector.META_FEATURES

FIRE_THRESHOLD = 0.3
REDUNDANT_THRESHOLD = 0.85

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}


def collect_rows(folders):
    """Run the detector on every image in the folders, returning a list of
    score rows (one per image, ordered by SIGNALS) plus the processed count."""
    rows = []
    for folder in folders:
        if not os.path.isdir(folder):
            print(f"  WARNING: not a directory, skipping: {folder}")
            continue
        for fname in sorted(os.listdir(folder)):
            path = os.path.join(folder, fname)
            if not os.path.isfile(path):
                continue
            if os.path.splitext(fname)[1].lower() not in IMAGE_EXTS:
                continue
            try:
                img = Image.open(path)
                with open(path, "rb") as f:
                    raw = f.read()
                result = ai_detector.detect_image(img, raw_bytes=raw)
                fv = result.get("feature_vector", {})
                rows.append([float(fv.get(k, 0.0)) for k in SIGNALS])
            except Exception as e:
                print(f"  skip {fname}: {e}")
    return rows


def correlation_matrix(matrix):
    """Pearson correlation across columns (signals). Constant/zero-variance
    columns are handled gracefully: their correlations are set to 0 rather
    than producing nan / divide-by-zero warnings."""
    n_signals = matrix.shape[1]
    # np.corrcoef expects variables in rows, so transpose.
    with np.errstate(divide="ignore", invalid="ignore"):
        corr = np.corrcoef(matrix.T)
    # corrcoef returns a scalar for a single variable; normalize to 2-D.
    corr = np.atleast_2d(corr)
    if corr.shape != (n_signals, n_signals):
        corr = np.full((n_signals, n_signals), np.nan)
    # Zero-variance columns yield nan rows/cols — replace with 0 correlation.
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    # Keep the diagonal as a clean 1.0 for any column that has variance.
    variances = matrix.var(axis=0)
    for i in range(n_signals):
        corr[i, i] = 1.0 if variances[i] > 0 else 0.0
    return corr


def print_corr_table(corr):
    """Print a readable signals x signals correlation table (2 decimals)."""
    # Short labels keep columns narrow but readable.
    col_w = 8
    # Truncate to col_w-1 so there is always a separating space in the header.
    labels = [s[: col_w - 1] for s in SIGNALS]
    header = " " * 14 + "".join(f"{lab:>{col_w}}" for lab in labels)
    print(header)
    for i, name in enumerate(SIGNALS):
        cells = "".join(f"{corr[i, j]:>{col_w}.2f}" for j in range(len(SIGNALS)))
        print(f"{name[:13]:<14}{cells}")


def find_redundant_pairs(corr):
    """Return all upper-triangle signal pairs with |correlation| > threshold."""
    pairs = []
    n = len(SIGNALS)
    for i in range(n):
        for j in range(i + 1, n):
            c = corr[i, j]
            if abs(c) > REDUNDANT_THRESHOLD:
                pairs.append((SIGNALS[i], SIGNALS[j], float(c)))
    pairs.sort(key=lambda p: -abs(p[2]))
    return pairs


def main():
    folders = sys.argv[1:]
    if not folders:
        print("Usage: python scripts/analyze_redundancy.py <image_dir1> [<image_dir2> ...]")
        sys.exit(1)

    ai_detector.load_model()

    print("Extracting signal scores...")
    rows = collect_rows(folders)
    n_images = len(rows)
    print(f"  Processed {n_images} image(s) across {len(folders)} folder(s).")

    if n_images < 2:
        print("Need at least 2 images to compute correlations.")
        sys.exit(1)

    matrix = np.array(rows, dtype=np.float64)  # (n_images x n_signals)

    corr = correlation_matrix(matrix)

    print(f"\nPairwise Pearson correlation across {len(SIGNALS)} signals "
          f"({n_images} images):\n")
    print_corr_table(corr)

    # Redundant pairs
    pairs = find_redundant_pairs(corr)
    print(f"\nRedundant signal pairs (|correlation| > {REDUNDANT_THRESHOLD}):")
    if pairs:
        for a, b, c in pairs:
            # Recommend down-weighting the second signal of the pair.
            print(f"  {a:22s} <-> {b:22s}  r = {c:+.2f}  "
                  f"-> consider down-weighting '{b}'")
    else:
        print("  None. All signals appear sufficiently independent.")

    # Per-signal stats
    means = matrix.mean(axis=0)
    fire_rate = (matrix > FIRE_THRESHOLD).mean(axis=0) * 100.0
    print(f"\nPer-signal statistics (fire = score > {FIRE_THRESHOLD}):")
    print(f"  {'signal':22s} {'mean':>8s} {'fire %':>9s}")
    for i, name in enumerate(SIGNALS):
        print(f"  {name:22s} {means[i]:>8.3f} {fire_rate[i]:>8.1f}%")

    # Save results
    out = {
        "signals": SIGNALS,
        "n_images": n_images,
        "fire_threshold": FIRE_THRESHOLD,
        "redundant_threshold": REDUNDANT_THRESHOLD,
        "correlation_matrix": [[round(float(v), 4) for v in row] for row in corr],
        "redundant_pairs": [
            {"signal_a": a, "signal_b": b, "correlation": round(c, 4),
             "recommend_downweight": b}
            for a, b, c in pairs
        ],
        "signal_stats": {
            name: {
                "mean": round(float(means[i]), 4),
                "fire_rate_pct": round(float(fire_rate[i]), 2),
            }
            for i, name in enumerate(SIGNALS)
        },
    }
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(models_dir, exist_ok=True)
    out_path = os.path.join(models_dir, "signal_correlations.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved correlation report to {out_path}")


if __name__ == "__main__":
    main()
