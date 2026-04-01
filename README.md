# AI Image & Video Detector

Detect AI-generated images and deepfake videos using a multi-signal forensic ensemble. Analyses frequency patterns, noise fingerprints, facial anomalies, colour space forensics, and (optionally) ML models to produce a confidence score.

## Quick Start (Development)

```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py
# API runs at http://localhost:8000

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
# UI runs at http://localhost:3000
```

## Docker Deployment

```bash
cp .env.example .env
# Edit .env with your settings
docker-compose up --build
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FRONTEND_ORIGIN` | `http://localhost:3000` | Frontend URL for CORS |
| `BACKEND_PORT` | `8000` | Backend port mapping |
| `FRONTEND_PORT` | `3000` | Frontend port mapping |
| `HIVE_API_KEY` | *(empty)* | Optional Hive Moderation API key for improved accuracy. Get one at thehive.ai |

## Detection Signals

The ensemble combines 9+ independent signals:

| Signal | Description |
|--------|-------------|
| ML Models (ViT) | SDXL detector + deepfake detector via HuggingFace (optional) |
| Hive API | External AI detection service (optional, requires API key) |
| Frequency (DCT+FFT) | Spectral artifacts and power law deviations |
| Statistical | Noise patterns, pixel distributions, colour correlations |
| Texture | Edge density, local variance, gradient patterns |
| SRM | Steganalysis rich model noise fingerprinting |
| Colour Space | LAB/YCbCr forensics, chroma gradient analysis |
| Face Analysis | Symmetry, skin texture, boundary artifacts |
| Metadata | EXIF data, compression artifacts, format anomalies |

For **videos**: analyses 15 keyframes individually plus temporal consistency (optical flow, noise, flicker).

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/health` | GET | None | Health check and model status |
| `/api/detect` | POST | None | Auto-detect file type and analyse |
| `/api/detect/image` | POST | None | Analyse an image |
| `/api/detect/video` | POST | None | Analyse a video |
| `/api/detect-url` | POST | None | Download and analyse from URL |
| `/api/stats` | GET | None | Analysis counters |
| `/api/waitlist` | POST | None | Join email waitlist |
| `/api/v1/detect` | POST | API Key | Developer API (X-API-Key header) |
| `/api/v1/usage` | GET | API Key | API key usage stats |
| `/api/docs` | GET | None | Developer API documentation |

### Rate Limits

- Web endpoints: 10 requests/hour per IP
- Developer API: 100 requests/day per API key
- Waitlist: 3 requests/hour per IP

### Generate an API Key

```bash
python scripts/generate_api_key.py --name "My App"
```

### Example

```bash
curl -X POST http://localhost:8000/api/detect/image -F "file=@photo.jpg"
```

## Supported Formats

- **Images**: JPEG, PNG, WebP, BMP, TIFF
- **Videos**: MP4, AVI, MOV, WebM
- **Max file size**: 50 MB

## Benchmarking

```bash
python scripts/download_test_data.py
python scripts/benchmark.py test_data/real test_data/ai_generated
python scripts/calibrate_threshold.py
```

See [BENCHMARK.md](BENCHMARK.md) for latest results.

## Tech Stack

- **Backend**: Python, FastAPI, NumPy, SciPy, OpenCV, Pillow, slowapi
- **Frontend**: React, Vite, Tailwind CSS, React Router, html2canvas
- **ML** (optional): PyTorch, HuggingFace Transformers

## Accuracy Disclaimer

This tool provides forensic analysis to help assess whether content may be AI-generated. **No detection tool is 100% accurate.** Results should be treated as a guide, not a definitive verdict. The tool works best on:

- AI-generated images from diffusion models (Stable Diffusion, DALL-E, Midjourney)
- Deepfake face-swap videos
- Uncompressed or lightly compressed content

Heavy social media compression, screenshots, and screen recordings reduce accuracy.

## Privacy

- Uploaded files are analysed in memory and deleted immediately
- URL downloads are saved to temporary files and deleted after analysis
- No uploaded content is stored, logged, or used for any purpose
- Email waitlist entries are stored locally in CSV format
- Analysis counters are stored locally with no personal data
