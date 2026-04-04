# Benchmark Results

## Comprehensive Accuracy (192 images + 100 videos)

**Date:** 2026-04-04
**Detection mode:** Heuristic only (no ML models installed)

### Image Detection

| Dataset | Images | Accuracy | Real Correct | AI Correct |
|---|---|---|---|---|
| 100 synthetic (EXIF+PNG) | 100 | **100%** | 50/50 | 50/50 |
| 18 real-world (GitHub repos) | 18 | **100%** | 11/11 | 7/7 |
| 64 mixed (downloads+synthetic) | 64 | **95.3%** | 40/42 | 21/22 |
| 10 adversarial edge cases | 10 | **80%** | 3/5 | 5/5 |
| **TOTAL** | **192** | **97.4%** | **104/108 (96.3%)** | **83/84 (98.8%)** |

- **False positive rate:** 3.7% (4/108 real images incorrectly flagged)
- **False negative rate:** 1.2% (1/84 AI images missed)
- **Processing speed:** 0.32 seconds per image

### Video Detection

| Metric | Value |
|---|---|
| Total videos tested | 100 |
| **Overall accuracy** | **98%** |
| Real videos correct | 50/50 (100%) |
| AI animation correct | 48/50 (96%) |
| False positives | 0 |
| False negatives | 2 |

### False Positive Analysis

The 4 false positives are:
1. Two synthetic web JPEGs without EXIF scoring 34.0-34.3% (threshold 33%)
2. Old 512x512 scan without EXIF — identical metadata profile to AI images
3. Real photo saved as PNG without EXIF — triggers PNG-no-EXIF signal

All are within 1.5% of the detection threshold.

### False Negative Analysis

The 1 missed AI image is a latent diffusion research diagram (`ldm_sample.png`) scoring 32.9%.

### Key Detection Signals (ranked by impact)

1. **PNG without EXIF** — strongest single signal (0.45 weight)
2. **Camera EXIF data** — negative weight when present (-0.15 to -0.30)
3. **JPEG quality 100** — real cameras never save at Q100
4. **Dimensions divisible by 64** — common in diffusion models
5. **Low color correlation** (<0.55) — unusual for real photos
6. **Frame duplication** — catches stop-motion animation
7. **Limited color palette** (<20 unique) — catches animation

### Known Limitations

1. **Re-compressed images** — AI images re-saved as JPEG (WhatsApp/social media) lose metadata signals. Heuristic detection drops significantly.
2. **Real PNGs without EXIF** — indistinguishable from AI PNGs without ML.
3. **512x512 old scans** — same dimensions as common AI output.
4. **Threshold sensitivity** — 4 borderline cases within 1.5% of threshold.

### What would fix the remaining failures

- **ML models** (ViT/SDXL detector) — would catch content-level differences invisible to heuristics
- **Hive API** — commercial detection trained on millions of images

### Running benchmarks

```bash
# Image benchmark
python scripts/benchmark.py test_data/real test_data/ai_generated

# CIFAKE dataset (requires network)
python scripts/benchmark.py --cifake --limit 200

# Unit tests
cd backend && python test_detector.py

# API tests (requires running server)
python scripts/test_api.py
```
