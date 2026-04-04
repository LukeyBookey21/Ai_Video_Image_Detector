# Contributing

## Development Setup

```bash
git clone https://github.com/LukeyBookey21/Ai_Video_Image_Detector.git
cd Ai_Video_Image_Detector
```

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### ML Models (optional)
```bash
cd backend
python install_ml.py --check  # Check status
python install_ml.py          # Install CPU models
python install_ml.py --gpu    # Install with CUDA
```

## Running Tests

```bash
# Unit tests (no server needed)
cd backend && python test_detector.py

# API tests (requires running server)
python scripts/test_api.py

# E2E tests (requires running server)
python scripts/test_e2e.py

# Accuracy benchmark
python scripts/benchmark.py test_data/real test_data/ai_generated

# All at once
make test
```

## Code Style

- Python: `black --line-length 120`
- Run `make format` before committing
- Run `make lint` to check

## Project Structure

```
backend/
  main.py           — FastAPI app, all routes, middleware
  detector.py       — Detection engine, 12 signal analyzers
  video_processor.py — Video frame extraction + temporal analysis
  database.py       — SQLite storage layer
  face_analysis.py  — Face-specific forensic analysis
  color_analysis.py — LAB/YCbCr color space forensics
  advanced_video.py — rPPG, identity consistency, BG/FG coherence
  heatmap.py        — Pixel-level artifact visualization
  install_ml.py     — ML model setup script

frontend/src/
  App.jsx           — Main page layout
  main.jsx          — Router + lazy loading
  components/       — 22 React components

scripts/
  benchmark.py      — Accuracy benchmarking
  calibrate_threshold.py — Threshold optimization
  test_api.py       — API integration tests
  test_e2e.py       — End-to-end tests
  generate_api_key.py — Developer API key generation

extension/          — Chrome extension
whatsapp-bot/       — WhatsApp bot (Twilio)
```

## Adding a New Detection Signal

1. Create a new analyzer class in `detector.py`:
```python
class MyAnalyzer:
    def analyze(self, image: Image.Image) -> dict:
        # Your analysis logic
        return {"ai_probability": 0.0, "my_metric": value}
```

2. Add it to `AIImageDetector.__init__()`:
```python
self.my_analyzer = MyAnalyzer()
```

3. Call it in `detect_image()`:
```python
my_result = self._sanitize_dict(self.my_analyzer.analyze(image_rgb))
```

4. Add the score to the ensemble (as a bonus signal or weighted):
```python
ensemble_score += my_result.get("ai_probability", 0) * 0.05
```

5. Add to the details dict for frontend display.

6. Add to the explanation generator if appropriate.

7. Run tests: `cd backend && python test_detector.py`

## Adding a New Frontend Page

1. Create component in `frontend/src/components/MyPage.jsx`
2. Add lazy import in `main.jsx`:
```js
const MyPage = lazy(() => import('./components/MyPage.jsx'))
```
3. Add route: `<Route path="/mypage" element={<MyPage />} />`
4. Build: `cd frontend && npm run build`

## Adding a New API Endpoint

1. Add to `backend/main.py` with appropriate rate limiting
2. Add test in `scripts/test_api.py`
3. Update README.md endpoint table
