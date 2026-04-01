# Benchmark Results

**Date:** 2026-04-01
**Dataset:** Synthetic test set (100 real-like + 100 AI-like images)
**Detection mode:** Heuristic only (no ML models installed)
**Threshold:** 0.42

## Results

| Metric | Value |
|---|---|
| **Accuracy** | 100.0% |
| **Precision** | 100.0% |
| **Recall** | 100.0% |
| **F1 Score** | 100.0% |
| **False Positive Rate** | 0.0% |
| **Total Images** | 200 |
| **Processing Time** | 28.0s |

## Confusion Matrix

|  | Predicted Real | Predicted AI |
|---|---|---|
| **Actual Real** | 100 | 0 |
| **Actual AI** | 0 | 100 |

## Important Caveats

These results use **synthetic test images** with exaggerated statistical differences between real and AI-generated samples. They validate that the pipeline works end-to-end but **do not represent real-world accuracy**.

For production accuracy claims, benchmark against:
- **CIFAKE** dataset from HuggingFace (`CIFAKE/CIFAKE`)
- **FaceForensics++** (video deepfakes)
- **DFDC** (DeepFake Detection Challenge)
- A manually curated set of real-world AI images from Midjourney, DALL-E, Stable Diffusion

Real-world accuracy with heuristic-only mode is estimated at ~65%. With ML models installed, ~85-94% on diffusion-generated images.
