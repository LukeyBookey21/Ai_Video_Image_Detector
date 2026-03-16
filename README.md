# AI Image & Video Detector

A web application that detects AI-generated images and videos using an ensemble of forensic analysis techniques. No external API keys or GPU required — runs entirely on CPU.

## How It Works

The detector combines three independent analysis methods and ensembles their results:

| Method | Weight | What It Detects |
|--------|--------|----------------|
| **Frequency Analysis** (DCT + FFT) | 40% | Spectral artifacts, power law deviations, abnormal frequency distributions |
| **Statistical Analysis** | 35% | Noise patterns, pixel distribution anomalies, color channel correlations |
| **Texture Analysis** | 25% | Unnatural smoothness, edge density anomalies, gradient patterns |

For **videos**, the system extracts evenly-spaced keyframes, analyzes each independently, and aggregates scores (60% average + 40% max) to catch partial deepfakes.

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The API runs at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI runs at `http://localhost:3000` and proxies API calls to the backend.

### Run Tests

```bash
cd backend
python test_detector.py
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/detect` | POST | Auto-detect file type and analyze |
| `/api/detect/image` | POST | Analyze an image |
| `/api/detect/video` | POST | Analyze a video |

Upload a file as multipart form data with field name `file`.

### Example

```bash
curl -X POST http://localhost:8000/api/detect/image \
  -F "file=@photo.jpg"
```

### Response

```json
{
  "filename": "photo.jpg",
  "file_type": "image",
  "verdict": "AI-Generated",
  "confidence": 72.5,
  "ai_probability": 72.5,
  "details": {
    "frequency_analysis": { "ai_score": 65.0, "spectral_flatness": 0.82, "power_law_slope": -0.45 },
    "statistical_analysis": { "ai_score": 75.0, "noise_level": 2.1, "color_correlation": 0.91 },
    "texture_analysis": { "ai_score": 80.0, "edge_density": 0.02, "local_variance": 85.3 }
  }
}
```

## Supported Formats

- **Images**: JPEG, PNG, WebP, BMP, TIFF
- **Videos**: MP4, AVI, MOV, WebM
- **Max file size**: 100MB

## Tech Stack

- **Backend**: Python, FastAPI, NumPy, SciPy, OpenCV, Pillow
- **Frontend**: React, Vite, Tailwind CSS
- **Detection**: DCT/FFT frequency analysis, statistical forensics, texture analysis

## Limitations

- This is a forensic heuristic approach, not a trained ML classifier. Accuracy is lower than commercial tools that use fine-tuned neural networks.
- Works best on uncompressed or lightly compressed images. Heavy JPEG compression destroys forensic artifacts.
- Detection of the latest AI generators (which constantly improve) may be less reliable.
- For highest accuracy, consider integrating a HuggingFace model (e.g., `Organika/sdxl-detector`) — the codebase is designed to support this as a drop-in upgrade.

## Upgrading to ML Models

The architecture supports swapping in pre-trained HuggingFace models. To enable:

1. Install `torch` and `transformers`
2. Modify `detector.py` to add a `ViTDetector` class using `pipeline("image-classification", model="Organika/sdxl-detector")`
3. Add it to the ensemble with appropriate weighting

This gives ~94% accuracy on modern AI-generated images vs the current heuristic approach.
