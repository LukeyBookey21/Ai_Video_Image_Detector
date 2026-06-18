# Development Progress

Continuation notes for autonomous development sessions.

## Current State (last session)

- **18 detection signals** (15 image-level in the feature vector + video signals)
- **Data-driven ensemble meta-classifier** blends 50/50 with hand-tuned weights
- **Model version:** v2.1 (in every API response)

### Test baseline (must not regress)
- Unit tests: `cd backend && python test_detector.py` → **6/6**
- Verification set (9 GitHub real-world images): **9/9**
- Documented benchmark: 192 images 97.4%, 100 videos 98% (see BENCHMARK.md)

### IMPORTANT: environment resets between sessions
Dependencies and `/tmp` test data are wiped. At session start, run:
```bash
pip install -q numpy scipy opencv-python-headless Pillow fastapi "uvicorn[standard]" \
    python-multipart slowapi requests filelock aiofiles reportlab
cd frontend && npm install
```
Re-download verification images to `/tmp/verify/{real,ai}` from GitHub raw
(ultralytics/yolov5, pytorch/hub, ageitgey/face_recognition, opencv, CompVis/stable-diffusion, NVlabs/stylegan2-3).

## Completed This Session
- ✅ Tier 1 #1: GAN fingerprint detector (`backend/signals/gan_fingerprint.py`)
- ✅ Tier 1 #3: Diffusion artifact detector (`backend/signals/diffusion_artifacts.py`)
- ✅ Tier 1 #4: Noise inconsistency map (`backend/signals/noise_map.py`)
- ✅ Tier 1 #6: PRNU sensor fingerprint (`backend/signals/prnu.py`)
- ✅ Tier 1 #5: Copy-move forgery (`backend/signals/copy_move.py`)
- ✅ Tier 5 #14: Parallel signal processing (ThreadPoolExecutor)
- ✅ Tier 2 #8: Ensemble meta-classifier (`scripts/train_ensemble.py`, `models/ensemble_weights.json`)
  - Fixed both documented BENCHMARK.md limitations (real-PNG FP, recompressed-AI FN)
  - Widened real/AI margin 2.2% → 14.4% on verification set
- ✅ Tier 5 #16: Model versioning (`MODEL_VERSION` in detector.py)
- ✅ Tier 4 #13: PDF forensic report (`backend/pdf_report.py`, `POST /api/report`)
- ✅ Tier 3 #12: Signal radar chart (`frontend/src/components/SignalRadar.jsx`, pure SVG)

## Architecture Notes
- All signals run in a parallel pool in `detector.detect_image()` (~line 1060)
- Feature vector exposed in API response as `feature_vector` (15 keys)
- Meta-classifier: `_meta_classifier_predict()` loads `models/ensemble_weights.json`,
  applies logistic regression, blends 50/50. Graceful fallback if file missing.
- New signal format: `{"signal_name", "score" 0-1, "confidence" 0-1, "details"}`
- To add a signal: create in `backend/signals/`, add to the ThreadPoolExecutor
  futures dict, add to `feature_vector`, optionally to ensemble bonus loop + details.

## Next Priorities (not yet done)
- Tier 2 #9: Platt scaling / calibration of meta-classifier probabilities
- Tier 2 #10: Signal redundancy (Pearson correlation matrix) → down-weight redundant pairs
- Tier 3 #11: Heatmap overlay API (ELA, noise_map as PNG overlays)
- Tier 1 #2: CLIP semantic scorer (needs open-clip-torch — network/size risk)
- Tier 1 #7: Lighting consistency check (specular highlight direction on faces)
- Tier 5 #15: Persistent SQLite result cache (in-memory LRU already exists)
- Tier 5 #17: Admin dashboard — signal histograms, avg processing time, cache hit rate
- Tier 6 #18-20: JPEG re-compression / resize / adversarial-noise robustness

## Commit Convention
`feat(signal):`, `feat(ensemble):`, `feat(report):`, `feat(ui):`, `perf:`, `fix:`
Always run `python test_detector.py` before committing.
