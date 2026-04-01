"""
Calibrate the detection threshold using benchmark results.
Tests thresholds from 0.25 to 0.80 and identifies optimal values.
Usage: python scripts/calibrate_threshold.py
"""

import json
import os
import sys


def main():
    results_path = os.path.join(os.path.dirname(__file__), "..", "benchmark_results.json")
    if not os.path.exists(results_path):
        print("Error: benchmark_results.json not found. Run benchmark.py first.")
        sys.exit(1)

    with open(results_path) as f:
        data = json.load(f)

    results = data["results"]
    valid = [r for r in results if r["ai_probability"] is not None]

    print(f"Calibrating thresholds on {len(valid)} images...\n")

    thresholds = [round(t, 2) for t in [x * 0.05 + 0.25 for x in range(12)]]  # 0.25 to 0.80

    best_f1 = 0
    best_f1_thresh = 0.42
    best_low_fpr_thresh = 0.42

    print(f"{'Threshold':>10} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'FPR':>10}")
    print("-" * 65)

    rows = []
    for thresh in thresholds:
        tp = sum(1 for r in valid if r["ground_truth"] == "ai_generated" and r["ai_probability"] / 100.0 > thresh)
        fp = sum(1 for r in valid if r["ground_truth"] == "real" and r["ai_probability"] / 100.0 > thresh)
        tn = sum(1 for r in valid if r["ground_truth"] == "real" and r["ai_probability"] / 100.0 <= thresh)
        fn = sum(1 for r in valid if r["ground_truth"] == "ai_generated" and r["ai_probability"] / 100.0 <= thresh)

        total = tp + fp + tn + fn
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

        rows.append((thresh, accuracy, precision, recall, f1, fpr))
        print(f"{thresh:>10.2f} {accuracy:>10.1%} {precision:>10.1%} {recall:>10.1%} {f1:>10.1%} {fpr:>10.1%}")

        if f1 > best_f1:
            best_f1 = f1
            best_f1_thresh = thresh

    # Find lowest FPR threshold with recall >= 0.80
    candidates = [(t, fpr) for t, acc, prec, rec, f1, fpr in rows if rec >= 0.80]
    if candidates:
        best_low_fpr_thresh = min(candidates, key=lambda x: x[1])[0]

    print()
    print(f"Best F1 threshold:                    {best_f1_thresh:.2f} (F1 = {best_f1:.1%})")
    print(f"Lowest FPR with recall >= 0.80:       {best_low_fpr_thresh:.2f}")
    print(f"\nRecommended threshold for production: {best_f1_thresh:.2f}")

    return best_f1_thresh


if __name__ == "__main__":
    optimal = main()
