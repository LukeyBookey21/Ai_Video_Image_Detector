"""
Benchmark the detection pipeline against labelled test data.
Usage: python scripts/benchmark.py test_data/real test_data/ai_generated
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from PIL import Image
from detector import detector as ai_detector


def run_benchmark(real_dir: str, ai_dir: str) -> dict:
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
    }

    # Print results
    print("=" * 50)
    print("BENCHMARK RESULTS")
    print("=" * 50)
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
    print("=" * 50)

    return {"metrics": metrics, "results": results}


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/benchmark.py <real_dir> <ai_dir>")
        sys.exit(1)

    real_dir = sys.argv[1]
    ai_dir = sys.argv[2]

    if not os.path.isdir(real_dir):
        print(f"Error: {real_dir} is not a directory")
        sys.exit(1)
    if not os.path.isdir(ai_dir):
        print(f"Error: {ai_dir} is not a directory")
        sys.exit(1)

    data = run_benchmark(real_dir, ai_dir)

    out_path = os.path.join(os.path.dirname(__file__), "..", "benchmark_results.json")
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    main()
