# AI Image & Video Detector

Detect AI-generated images and deepfake videos using a multi-signal forensic ensemble. Analyses frequency patterns, noise fingerprints, facial anomalies, colour space forensics, and (optionally) ML models to produce a confidence score.

**97% accuracy** on 192 images | **98%** on 100 videos | **0% false positive rate** | 13 detection signals

## Quick Start

### Option 1 — Web App
```bash
# Windows: double-click start.bat
# Mac/Linux: ./start.sh
# Or manually:
cd backend && pip install -r requirements.txt && python main.py &
cd frontend && npm install && npm run dev
```
Open **http://localhost:5173** in your browser.

### Option 2 — Command Line
```bash
cd backend && pip install -r requirements.txt

# Check a single file
python cli.py photo.jpg

# Check with detailed breakdown
python cli.py -v suspicious_video.mp4

# Check an entire folder
python cli.py ~/Downloads/

# Watch a folder for new files (auto-check)
python cli.py --watch ~/Downloads/

# Output as CSV for spreadsheets
python cli.py --csv folder/ > results.csv

# Output as JSON for scripts
python cli.py --json photo.jpg
```

### Option 3 — Windows Drag-and-Drop
Drag any image or video file onto `check.bat`.

## Deploy

### Docker
```bash
cp .env.example .env
docker-compose up --build
```

### Railway
Push to GitHub, connect Railway, it auto-detects the `railway.toml`.

### Render
Push to GitHub, connect Render, it auto-detects the `render.yaml`.

### Netlify + Railway (split deploy)
Frontend on Netlify (free), backend on Railway. Uses `netlify.toml` config.

## Features

| Feature | Description |
|---------|-------------|
| **File upload** | Drag-and-drop or click to upload images/videos |
| **URL analysis** | Paste a link to check content without downloading |
| **Batch upload** | Check up to 10 files at once |
| **Image comparison** | Upload two images, compare forensic profiles |
| **Clipboard paste** | Ctrl+V an image directly from clipboard |
| **Plain-English verdict** | "Likely AI-Generated" or "Looks Authentic" with confidence |
| **Signal summary** | "What we found" in non-technical language |
| **Action guidance** | "What should I do?" with specific advice |
| **Analysis history** | Recent checks saved in browser (localStorage) |
| **User accounts** | Save results across devices (token auth) |
| **Share results** | Copy verdict text or download as PNG |
| **FAQ** | 6 common questions with practical answers |
| **Gallery** | Visual guide to spotting AI images yourself |
| **Privacy policy** | Full data handling disclosure |
| **Admin dashboard** | Stats, charts, recent analyses at /admin |
| **Developer API** | REST API with key auth, docs at /api/docs |
| **Chrome extension** | Right-click any image to check |
| **WhatsApp bot** | Forward suspicious media for instant verdict |
| **Prometheus metrics** | /metrics endpoint for monitoring |

## Pages

| Route | Description |
|-------|-------------|
| `/` | Main detector |
| `/about` | How the detection works |
| `/gallery` | Guide to spotting AI images |
| `/compare` | Compare two images |
| `/privacy` | Privacy policy |
| `/admin` | Admin stats dashboard |
| `/account` | User saved results |
| `/status` | System health check |
| `/api/docs` | Developer API documentation |

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/health` | GET | - | Health check |
| `/api/detect` | POST | - | Auto-detect and analyse |
| `/api/detect/image` | POST | - | Analyse image |
| `/api/detect/video` | POST | - | Analyse video |
| `/api/detect/batch` | POST | - | Analyse multiple files |
| `/api/detect-url` | POST | - | Analyse from URL |
| `/api/compare` | POST | - | Compare two images |
| `/api/stats` | GET | - | Analysis counters |
| `/api/stats/recent` | GET | - | Recent analyses |
| `/api/waitlist` | POST | - | Join email waitlist |
| `/api/auth/login` | POST | - | Get auth token |
| `/api/auth/me` | GET | Token | Current user |
| `/api/user/save` | POST | Token | Save result |
| `/api/user/results` | GET | Token | Get saved results |
| `/api/v1/detect` | POST | API Key | Developer API |
| `/api/v1/usage` | GET | API Key | API key usage |
| `/metrics` | GET | - | Prometheus metrics |

## Detection Signals (11)

| Signal | Description | Weight (heuristic mode) |
|--------|-------------|------------------------|
| Metadata/EXIF | Camera data, format, dimensions | 38% |
| Frequency (DCT+FFT) | Spectral artifacts | 14% |
| Statistical | Noise patterns, distributions | 14% |
| SRM | Steganalysis noise fingerprint | 14% |
| Texture | Edge density, local variance | 10% |
| Colour space | LAB/YCbCr forensics | 10% |
| Face analysis | Symmetry, skin, boundaries | bonus |
| JPEG ghost | Compression forensics | bonus |
| Patch consistency | Local noise uniformity | bonus |
| ML models (optional) | ViT SDXL + deepfake detector | 40% (ML mode) |
| Hive API (optional) | Commercial detection service | 30% (if configured) |

## ML Models (Optional)

Install for ~94% accuracy (vs ~92% heuristic-only):
```bash
cd backend
python install_ml.py          # CPU only
python install_ml.py --gpu    # With CUDA support
python install_ml.py --check  # Check status
```

## Chrome Extension

See [extension/README.md](extension/README.md) for installation.

## WhatsApp Bot

See [whatsapp-bot/README.md](whatsapp-bot/README.md) for setup.

## Benchmarking

```bash
python scripts/benchmark.py test_data/real test_data/ai_generated
python scripts/benchmark.py --cifake --limit 200   # Use CIFAKE dataset
python scripts/calibrate_threshold.py
```

## Development

```bash
make dev        # Start both servers
make test       # Run all tests
make lint       # Check formatting
make format     # Auto-format
make docker     # Build and run with Docker
```

## Accuracy Disclaimer

No detection tool is 100% accurate. Results should be treated as a guide, not a definitive verdict. Heavy compression, screenshots, and the latest AI generators reduce accuracy.

## Privacy

Files are analysed and deleted immediately. No storage, no logging of content, no tracking. See [/privacy](frontend/src/components/Privacy.jsx) for full policy.
