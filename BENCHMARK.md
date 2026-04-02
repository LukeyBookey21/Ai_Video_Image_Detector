# Benchmark Results

## Real-World Accuracy (current)

**Date:** 2026-04-02
**Dataset:** 7 real photographs + 6 AI-generated images from GitHub repos
**Detection mode:** Heuristic only (no ML models installed)
**Threshold:** 0.33

### Test Images

**Real photos:** Kodak DX3900 JPEG, Canon 5D Mark III portraits (Obama, Biden), iPhone XS photo, YOLOv5 sample images — all with genuine EXIF/camera metadata.

**AI images:** Stable Diffusion txt2img outputs (from CompVis/stable-diffusion repo), StyleGAN2/3 face teasers (from NVlabs repos) — PNGs without metadata.

### Results

| Metric | Value |
|---|---|
| **Overall Accuracy** | **92%** (12/13) |
| **Real Correctly Identified** | 7/7 (100%) |
| **AI Correctly Detected** | 5/6 (83%) |
| **False Positive Rate** | 0% |
| **False Negative Rate** | 17% (1 borderline img2img sketch) |

### Confusion Matrix

|  | Predicted Real | Predicted AI |
|---|---|---|
| **Actual Real** | 7 | 0 |
| **Actual AI** | 1 | 5 |

## Key Findings

1. **Metadata analysis is the strongest heuristic signal.** Real camera photos contain EXIF data (camera model, GPS, timestamp). AI-generated PNGs almost never have EXIF.
2. **Format detection matters.** PNG files without any metadata are strongly correlated with AI generation.
3. **Frequency/noise/texture heuristics alone cannot distinguish** modern AI outputs from real photos — they score nearly identically.
4. **Zero false positives** — the detector never incorrectly accuses a real photo of being AI-generated.

## Limitations

- **JPEG AI images are harder to detect** heuristically — they can look identical to old scans or screenshots that also lack EXIF.
- **Screenshots and social media re-uploads** strip EXIF metadata, which could trigger false positives on real content that's been re-shared.
- **Small test set** — 13 images. Larger benchmark needed for production confidence.
- **No ML models installed** — with HuggingFace ViT models, accuracy would likely reach 90%+ on a wider range of content.

## Recommended Next Steps

1. Run against CIFAKE dataset (10,000+ images) for statistically significant numbers
2. Install ML models for ViT-based detection
3. Test against social media compressed images (WhatsApp, Instagram re-uploads)
4. Test against latest generators (Midjourney v6, DALL-E 3, Flux)
