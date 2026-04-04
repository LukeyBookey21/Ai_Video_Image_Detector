"""
Benchmark the detection pipeline against labelled test data.

Usage:
  python scripts/benchmark.py test_data/real test_data/ai_generated
  python scripts/benchmark.py --cifake          # Use CIFAKE dataset from HuggingFace
  python scripts/benchmark.py --cifake --limit 200
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from PIL import Image
from detector import detector as ai_detector


def run_benchmark(real_dir: str, ai_dir: str, limit: int = 0) -> dict:
    """Run all images through the detector and compute metrics."""
    ai_detector.load_model()

    results = []
    all_images = []

    for fname in sorted(os.listdir(real_dir)):
        path = os.path.join(real_dir, fname)
        if os.path.isfile(path):
            all_images.append((path, fname, "real"))

    for fname in sorted(os.listdir(ai_dir)):
        path = os.path.join(ai_dir, fname)
        if os.path.isfile(path):
            all_images.append((path, fname, "ai_generated"))

    if limit > 0:
        # Take equal amounts from each class
        reals = [x for x in all_images if x[2] == "real"][:limit]
        ais = [x for x in all_images if x[2] == "ai_generated"][:limit]
        all_images = reals + ais

    print(f"Running benchmark on {len(all_images)} images...")
    start = time.time()

    for i, (path, fname, ground_truth) in enumerate(all_images):
        try:
            img = Image.open(path)
            with open(path, "rb") as f:
                raw = f.read()
            result = ai_detector.detect_image(img, raw_bytes=raw)

            predicted = "ai_generated" if result["verdict"] == "AI-Generated" else "real"
            results.append(
                {
                    "filename": fname,
                    "ground_truth": ground_truth,
                    "predicted": predicted,
                    "ai_probability": result["ai_probability"],
                    "confidence": result["confidence"],
                    "correct": predicted == ground_truth,
                }
            )
        except Exception as e:
            print(f"  Error on {fname}: {e}")
            results.append(
                {
                    "filename": fname,
                    "ground_truth": ground_truth,
                    "predicted": "error",
                    "ai_probability": None,
                    "confidence": None,
                    "correct": False,
                }
            )

        if (i + 1) % 25 == 0:
            print(f"  Processed {i + 1}/{len(all_images)}...")

    elapsed = round(time.time() - start, 1)
    print(f"Benchmark complete in {elapsed}s\n")

    # Calculate metrics
    tp = sum(1 for r in results if r["ground_truth"] == "ai_generated" and r["predicted"] == "ai_generated")
    fp = sum(1 for r in results if r["ground_truth"] == "real" and r["predicted"] == "ai_generated")
    tn = sum(1 for r in results if r["ground_truth"] == "real" and r["predicted"] == "real")
    fn = sum(1 for r in results if r["ground_truth"] == "ai_generated" and r["predicted"] == "real")

    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

    metrics = {
        "total_images": total,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "elapsed_seconds": elapsed,
        "detection_mode": "ml_ensemble" if ai_detector.ml_mode else "heuristic_only",
    }

    # Print results
    print("=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"  Mode:               {metrics['detection_mode']}")
    print(f"  Total images:       {total}")
    print(f"  Accuracy:           {accuracy:.1%}")
    print(f"  Precision:          {precision:.1%}")
    print(f"  Recall:             {recall:.1%}")
    print(f"  F1 Score:           {f1:.1%}")
    print(f"  False Positive Rate: {fpr:.1%}")
    print()
    print("  Confusion Matrix:")
    print(f"                    Predicted Real  Predicted AI")
    print(f"    Actual Real       {tn:>6}          {fp:>6}")
    print(f"    Actual AI         {fn:>6}          {tp:>6}")
    print()

    # Show misclassifications
    errors = [r for r in results if not r["correct"]]
    if errors:
        print(f"  Misclassified ({len(errors)}):")
        for r in errors[:10]:
            print(f"    {r['filename']}: {r['ground_truth']} -> {r['predicted']} ({r['ai_probability']}% AI)")
    print("=" * 60)

    return {"metrics": metrics, "results": results}


def download_cifake(limit: int = 100):
    """Download CIFAKE dataset from HuggingFace."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("Installing datasets library...")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets"])
        from datasets import load_dataset

    real_dir = os.path.join(os.path.dirname(__file__), "..", "test_data", "cifake_real")
    ai_dir = os.path.join(os.path.dirname(__file__), "..", "test_data", "cifake_ai")
    os.makedirs(real_dir, exist_ok=True)
    os.makedirs(ai_dir, exist_ok=True)

    print(f"Downloading CIFAKE dataset ({limit} per class)...")
    ds = load_dataset("CIFAKE/CIFAKE", split="test")

    real_count = ai_count = 0
    for sample in ds:
        if real_count >= limit and ai_count >= limit:
            break
        img = sample["image"]
        label = sample["label"]
        if label == 0 and real_count < limit:
            img.save(os.path.join(real_dir, f"real_{real_count:04d}.png"))
            real_count += 1
        elif label == 1 and ai_count < limit:
            img.save(os.path.join(ai_dir, f"ai_{ai_count:04d}.png"))
            ai_count += 1

    print(f"Downloaded: {real_count} real, {ai_count} AI to test_data/")
    return real_dir, ai_dir


def main():
    parser = argparse.ArgumentParser(description="Benchmark the AI detection pipeline")
    parser.add_argument("real_dir", nargs="?", help="Directory of real images")
    parser.add_argument("ai_dir", nargs="?", help="Directory of AI-generated images")
    parser.add_argument("--cifake", action="store_true", help="Download and use CIFAKE dataset")
    parser.add_argument("--limit", type=int, default=100, help="Images per class (default: 100)")
    parser.add_argument("--output", default="benchmark_results.json", help="Output file")
    args = parser.parse_args()

    if args.cifake:
        real_dir, ai_dir = download_cifake(args.limit)
    elif args.real_dir and args.ai_dir:
        real_dir, ai_dir = args.real_dir, args.ai_dir
    else:
        print("Usage: python benchmark.py <real_dir> <ai_dir>")
        print("   or: python benchmark.py --cifake")
        sys.exit(1)

    data = run_benchmark(real_dir, ai_dir, limit=args.limit)

    out_path = os.path.join(os.path.dirname(__file__), "..", args.output)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    main()
