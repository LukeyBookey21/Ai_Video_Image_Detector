"""
AI Image & Video Detection API
FastAPI backend with ensemble ML detection.
"""

import os
import tempfile
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import io

from detector import detector as ai_detector
from video_processor import get_video_processor

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/avi", "video/quicktime", "video/x-msvideo", "video/webm"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Pre-loading detection model...")
    ai_detector.load_model()
    print("Model ready.")
    yield


app = FastAPI(
    title="AI Image & Video Detector",
    description="Detect AI-generated images and videos using ensemble ML models",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "ml_model_loaded": ai_detector.ml_mode,
        "ml_models": ai_detector.ml_models_loaded,
        "detection_mode": "ml_ensemble" if ai_detector.ml_mode else "heuristic_only",
        "analyzers": ["frequency", "statistical", "texture", "srm", "metadata"]
            + (["ml_primary", "ml_deepfake"] if ai_detector.ml_mode else []),
    }


@app.post("/api/detect/image")
async def detect_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {file.content_type}. Supported: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 100MB.")

    try:
        image = Image.open(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not open image file.")

    start_time = time.time()
    result = ai_detector.detect_image(image, raw_bytes=contents)
    elapsed = round(time.time() - start_time, 2)

    return {
        "filename": file.filename,
        "file_type": "image",
        "file_size_mb": round(len(contents) / (1024 * 1024), 2),
        "processing_time_seconds": elapsed,
        **result,
    }


@app.post("/api/detect/video")
async def detect_video(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video type: {file.content_type}. Supported: {', '.join(ALLOWED_VIDEO_TYPES)}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 100MB.")

    # Write to temp file for OpenCV
    suffix = os.path.splitext(file.filename or ".mp4")[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        start_time = time.time()
        processor = get_video_processor(ai_detector)
        print(f"Analyzing video: {file.filename} ({len(contents) / 1024 / 1024:.1f} MB)")
        result = processor.analyze_video(tmp_path)
        elapsed = round(time.time() - start_time, 2)
        print(f"Video analysis complete: {result.get('verdict')} ({elapsed}s)")
    except Exception as e:
        print(f"Video analysis error: {e}")
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {
        "filename": file.filename,
        "file_type": "video",
        "file_size_mb": round(len(contents) / (1024 * 1024), 2),
        "processing_time_seconds": elapsed,
        **result,
    }


@app.post("/api/detect")
async def detect_auto(file: UploadFile = File(...)):
    """Auto-detect file type and route to the correct handler."""
    if file.content_type in ALLOWED_IMAGE_TYPES:
        return await detect_image(file)
    elif file.content_type in ALLOWED_VIDEO_TYPES:
        return await detect_video(file)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Supported images: {', '.join(ALLOWED_IMAGE_TYPES)}. Supported videos: {', '.join(ALLOWED_VIDEO_TYPES)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
