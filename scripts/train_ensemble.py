"""
Train the ensemble meta-classifier.

Extracts every signal's raw score for each labelled image, trains a
logistic-regression meta-classifier with a train/test split, and saves
the learned weights to models/ensemble_weights.json.

Usage:
    python scripts/train_ensemble.py <real_dir> <ai_dir>
    python scripts/train_ensemble.py --synthetic   # generate + train
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import numpy as np
from PIL import Image
from detector import detector as ai_detector
from detector import AIImageDetector

FEATURES = AIImageDetector.META_FEATURES


def extract_features(folder, label):
    """Run the detector on every image, collect raw feature vectors."""
    rows = []
    for fname in sorted(os.listdir(folder)):
        path = os.path.join(folder, fname)
        if not os.path.isfile(path):
            continue
        try:
            img = Image.open(path)
            with open(path, "rb") as f:
                raw = f.read()
            result = ai_detector.detect_image(img, raw_bytes=raw)
            fv = result.get("feature_vector", {})
            rows.append(([fv.get(k, 0.0) for k in FEATURES], label, fname))
        except Exception as e:
            print(f"  skip {fname}: {e}")
    return rows


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def train_logreg(X, y, epochs=2000, lr=0.5, l2=0.01):
    """Simple logistic regression via gradient descent (no sklearn dependency)."""
    n, d = X.shape
    w = np.zeros(d)
    b = 0.0
    for _ in range(epochs):
        z = X @ w + b
        p = sigmoid(z)
        grad_w = X.T @ (p - y) / n + l2 * w
        grad_b = np.mean(p - y)
        w -= lr * grad_w
        b -= lr * grad_b
    return w, b


def evaluate(X, y, w, b, threshold=0.5):
    p = sigmoid(X @ w + b)
    pred = (p > threshold).astype(int)
    acc = np.mean(pred == y)
    tp = np.sum((pred == 1) & (y == 1))
    fp = np.sum((pred == 1) & (y == 0))
    tn = np.sum((pred == 0) & (y == 0))
    fn = np.sum((pred == 0) & (y == 1))
    return acc, tp, fp, tn, fn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("real_dir", nargs="?")
    parser.add_argument("ai_dir", nargs="?")
    parser.add_argument("--synthetic", action="store_true", help="Generate synthetic training data")
    args = parser.parse_args()

    ai_detector.load_model()

    if args.synthetic:
        real_dir, ai_dir = generate_synthetic()
    elif args.real_dir and args.ai_dir:
        real_dir, ai_dir = args.real_dir, args.ai_dir
    else:
        print("Usage: train_ensemble.py <real_dir> <ai_dir>  OR  --synthetic")
        sys.exit(1)

    print("Extracting features...")
    real_rows = extract_features(real_dir, 0)
    ai_rows = extract_features(ai_dir, 1)
    all_rows = real_rows + ai_rows
    print(f"  {len(real_rows)} real, {len(ai_rows)} AI = {len(all_rows)} samples")

    if len(all_rows) < 10:
        print("Not enough samples to train.")
        sys.exit(1)

    X = np.array([r[0] for r in all_rows], dtype=np.float64)
    y = np.array([r[1] for r in all_rows], dtype=np.float64)

    # Shuffle + 80/20 split
    rng = np.random.RandomState(42)
    idx = rng.permutation(len(X))
    X, y = X[idx], y[idx]
    split = int(len(X) * 0.8)
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]

    # Standardize for stable training
    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0) + 1e-8
    X_train_n = (X_train - mean) / std
    X_test_n = (X_test - mean) / std

    w, b = train_logreg(X_train_n, y_train)

    train_acc, *_ = evaluate(X_train_n, y_train, w, b)
    test_acc, tp, fp, tn, fn = evaluate(X_test_n, y_test, w, b)

    print(f"\n  Train accuracy: {train_acc:.1%}")
    print(f"  Test accuracy:  {test_acc:.1%}")
    print(f"  Test confusion: TP={tp} FP={fp} TN={tn} FN={fn}")

    # Fold standardization into raw-feature coefficients so inference needs no scaler
    coef_raw = w / std
    intercept_raw = b - np.sum(w * mean / std)

    print("\n  Learned feature importance (|coef|):")
    importance = sorted(zip(FEATURES, np.abs(coef_raw)), key=lambda x: -x[1])
    for name, imp in importance:
        print(f"    {name:22s} {imp:.3f}")

    out = {
        "coef": coef_raw.tolist(),
        "intercept": float(intercept_raw),
        "features": FEATURES,
        "train_accuracy": round(float(train_acc), 4),
        "test_accuracy": round(float(test_acc), 4),
        "n_samples": len(all_rows),
    }
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(models_dir, exist_ok=True)
    out_path = os.path.join(models_dir, "ensemble_weights.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n  Saved to {out_path}")


def generate_synthetic():
    """Generate a synthetic train set: real (JPEG+EXIF+noise) vs AI (PNG smooth)."""
    from PIL import ImageFilter
    from PIL.ExifTags import Base as ExifBase
    import io

    base = os.path.join("/tmp", "train_data")
    real_dir = os.path.join(base, "real")
    ai_dir = os.path.join(base, "ai")
    os.makedirs(real_dir, exist_ok=True)
    os.makedirs(ai_dir, exist_ok=True)
    rng = np.random.RandomState(7)

    cams = [("Canon", "EOS R5"), ("Nikon", "D850"), ("Apple", "iPhone 15"), ("Sony", "A7 IV")]
    for i in range(60):
        make, model = cams[i % len(cams)]
        h, w = rng.choice([480, 600, 720]), rng.choice([640, 800, 960])
        arr = np.zeros((h, w, 3), dtype=np.float64)
        for c in range(3):
            arr[:, :, c] = np.linspace(rng.randint(40, 100), rng.randint(150, 210), h).reshape(-1, 1)
            arr[:, :, c] += rng.randn(h, w) * rng.uniform(6, 16)
        for _ in range(rng.randint(4, 12)):
            cx, cy, r = rng.randint(0, w), rng.randint(0, h), rng.randint(15, 70)
            col = rng.randint(20, 235, 3).astype(float)
            yy, xx = np.ogrid[-cy : h - cy, -cx : w - cx]
            m = xx**2 + yy**2 <= r**2
            for c in range(3):
                arr[:, :, c][m] = col[c] + rng.randn(m.sum()) * 9
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.SHARPEN)
        exif = img.getexif()
        exif[ExifBase.Make] = make
        exif[ExifBase.Model] = model
        exif[ExifBase.DateTime] = "2024:06:15 12:00:00"
        img.save(os.path.join(real_dir, f"r{i:03d}.jpg"), quality=int(rng.randint(78, 95)), exif=exif.tobytes())

    for i in range(60):
        h, w = rng.choice([512, 768, 1024]), rng.choice([512, 768, 1024])
        arr = np.zeros((h, w, 3), dtype=np.float64)
        for c in range(3):
            cen = rng.randint(90, 190)
            arr[:, :, c] = cen + rng.randn(h, w) * rng.uniform(0.5, 3)
        for _ in range(rng.randint(2, 7)):
            cx, cy, r = rng.randint(0, w), rng.randint(0, h), rng.randint(40, 160)
            col = rng.randint(60, 210, 3).astype(float)
            yy, xx = np.ogrid[-cy : h - cy, -cx : w - cx]
            dist = np.sqrt(xx**2 + yy**2)
            m = dist <= r
            blend = np.clip(1 - dist[m] / r, 0, 1)
            for c in range(3):
                arr[:, :, c][m] = arr[:, :, c][m] * (1 - blend) + col[c] * blend
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(rng.uniform(0.4, 1.1)))
        img.save(os.path.join(ai_dir, f"a{i:03d}.png"))

    print(f"Generated synthetic train set in {base}")
    return real_dir, ai_dir


if __name__ == "__main__":
    main()
