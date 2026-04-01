"""
AI Image & Video Detection API
FastAPI backend with multi-signal ensemble ML detection.
"""

import ipaddress
import json
import os
import socket
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from filelock import FileLock

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Request, Response
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from PIL import Image
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import io


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


from detector import detector as ai_detector
from video_processor import get_video_processor
from heatmap import generate_heatmap

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/avi", "video/quicktime", "video/x-msvideo", "video/webm"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Magic byte signatures for file type validation
MAGIC_SIGNATURES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG"],
    "image/gif": [b"GIF87a", b"GIF89a"],
    "image/webp": [],  # checked via RIFF...WEBP below
    "image/bmp": [b"BM"],
    "image/tiff": [b"II\x2a\x00", b"MM\x00\x2a"],
    "video/mp4": [],  # ftyp box checked below
    "video/quicktime": [],  # ftyp box checked below
    "video/x-msvideo": [b"RIFF"],
    "video/avi": [b"RIFF"],
    "video/webm": [b"\x1a\x45\xdf\xa3"],
}


def validate_magic_bytes(header: bytes, content_type: str) -> bool:
    """Validate file magic bytes match the declared content type."""
    if content_type in ("image/webp",):
        return header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    if content_type in ("video/mp4", "video/quicktime"):
        return b"ftyp" in header[:16]
    if content_type in ("video/x-msvideo", "video/avi"):
        return header[:4] == b"RIFF" and header[8:12] == b"AVI "
    sigs = MAGIC_SIGNATURES.get(content_type, [])
    return any(header[: len(sig)] == sig for sig in sigs)


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Pre-loading detection models...")
    ai_detector.load_model()
    print("Ready — all analyzers active.")
    yield


app = FastAPI(
    title="AI Image & Video Detector",
    description="Detect AI-generated images and videos using multi-signal ensemble analysis",
    version="2.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "You've made too many requests. Please wait a while before trying again.",
            "code": "RATE_LIMIT_EXCEEDED",
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback

    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "error": "Something went wrong on our end. Please try again.",
            "detail": str(exc),
            "code": "INTERNAL_ERROR",
        },
    )


app.add_middleware(SecurityHeadersMiddleware)

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)


STATS_FILE = os.path.join(os.path.dirname(__file__), "data", "stats.json")
STATS_LOCK = STATS_FILE + ".lock"


def _update_stats(verdict: str) -> None:
    """Increment analysis counters in stats.json with file locking."""
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with FileLock(STATS_LOCK):
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE) as f:
                stats = json.load(f)
        else:
            stats = {"total_analyses": 0, "ai_detected": 0, "authentic": 0, "uncertain": 0, "last_updated": ""}
        stats["total_analyses"] += 1
        if verdict == "AI-Generated":
            stats["ai_detected"] += 1
        elif verdict == "Real/Authentic":
            stats["authentic"] += 1
        else:
            stats["uncertain"] += 1
        stats["last_updated"] = datetime.utcnow().isoformat() + "Z"
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f)


@app.get("/api/stats")
async def get_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            return json.load(f)
    return {"total_analyses": 0, "ai_detected": 0, "authentic": 0, "uncertain": 0, "last_updated": ""}


WAITLIST_FILE = os.path.join(os.path.dirname(__file__), "data", "waitlist.csv")
WAITLIST_LOCK = WAITLIST_FILE + ".lock"
EMAIL_RE = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"


class WaitlistRequest(BaseModel):
    email: str


@app.post("/api/waitlist")
@limiter.limit("3/hour")
async def join_waitlist(request: Request, body: WaitlistRequest):
    import csv
    import hashlib
    import re

    email = body.email.strip().lower()
    if len(email) > 320 or not re.match(EMAIL_RE, email):
        raise HTTPException(status_code=422, detail="Please enter a valid email address.")

    os.makedirs(os.path.dirname(WAITLIST_FILE), exist_ok=True)
    ip_raw = get_remote_address(request) or "unknown"
    ip_hash = hashlib.sha256(ip_raw.encode()).hexdigest()

    with FileLock(WAITLIST_LOCK):
        existing = set()
        if os.path.exists(WAITLIST_FILE):
            with open(WAITLIST_FILE, newline="") as f:
                for row in csv.reader(f):
                    if row:
                        existing.add(row[0])

        if email in existing:
            return {"status": "already_registered"}

        with open(WAITLIST_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([email, datetime.utcnow().isoformat() + "Z", ip_hash])

    return {"status": "added"}


def _error(status: int, message: str, code: str):
    """Return a structured error response."""
    raise HTTPException(status_code=status, detail={"error": message, "code": code})


def _validate_upload(contents: bytes, content_type: str, filename: str) -> None:
    """Common validation for all uploads: size, magic bytes, type, path traversal."""
    if len(filename or "") > 255 or any(c in (filename or "") for c in ("..", "/", "\\", "\x00")):
        _error(400, "Invalid filename.", "INVALID_FILE_TYPE")

    if len(contents) > MAX_FILE_SIZE:
        _error(
            400,
            "This file is too large. The maximum size is 50 MB. Try compressing the file or trimming the video before uploading.",
            "FILE_TOO_LARGE",
        )

    all_allowed = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES
    if content_type not in all_allowed:
        _error(
            400,
            "This file type isn't supported. Please upload a JPEG, PNG, WebP, MP4, MOV, AVI, or WebM file.",
            "INVALID_FILE_TYPE",
        )

    header = contents[:16]
    if not validate_magic_bytes(header, content_type):
        _error(
            400,
            "This file doesn't appear to be a valid image or video. The file may be corrupted or its extension may not match its actual format.",
            "INVALID_FILE_TYPE",
        )


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": "2.0.0",
        "models_loaded": ai_detector.ml_mode,
        "ml_models": ai_detector.ml_models_loaded,
        "detection_mode": "ml_ensemble" if ai_detector.ml_mode else "heuristic_only",
        "analyzers": [
            "frequency",
            "statistical",
            "texture",
            "srm",
            "color_space",
            "face",
            "metadata",
        ]
        + (["ml_sdxl", "ml_deepfake"] if ai_detector.ml_mode else []),
    }


@app.post("/api/detect/image")
@limiter.limit("10/hour")
async def detect_image(
    request: Request,
    file: UploadFile = File(...),
    heatmap: bool = Query(default=True, description="Generate artifact heatmap"),
):
    contents = await file.read()
    _validate_upload(contents, file.content_type, file.filename or "")

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Please upload an image file for this endpoint.")

    try:
        image = Image.open(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not open image file. It may be corrupted.")

    start_time = time.time()
    result = ai_detector.detect_image(image, raw_bytes=contents)

    heatmap_data = None
    if heatmap:
        try:
            heatmap_data = generate_heatmap(image)
        except Exception as e:
            print(f"Heatmap generation error: {e}")

    elapsed = round(time.time() - start_time, 2)

    response = {
        "filename": file.filename,
        "file_type": "image",
        "file_size_mb": round(len(contents) / (1024 * 1024), 2),
        "processing_time_seconds": elapsed,
        **result,
    }

    if heatmap_data:
        response["heatmap"] = heatmap_data

    _update_stats(result.get("verdict", ""))
    return response


@app.post("/api/detect/video")
@limiter.limit("10/hour")
async def detect_video(request: Request, file: UploadFile = File(...)):
    contents = await file.read()
    _validate_upload(contents, file.content_type, file.filename or "")

    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=400, detail="Please upload a video file for this endpoint.")

    # Save to temp file with UUID name (never use original filename on disk)
    suffix = os.path.splitext(file.filename or ".mp4")[1]
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, contents)
        os.close(fd)

        start_time = time.time()
        processor = get_video_processor(ai_detector)
        print(f"Analyzing video: {file.filename} ({len(contents) / 1024 / 1024:.1f} MB)")
        result = processor.analyze_video(tmp_path)
        elapsed = round(time.time() - start_time, 2)
        print(f"Video analysis complete: {result.get('verdict')} ({elapsed}s)")
    except Exception as e:
        print(f"Video analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    _update_stats(result.get("verdict", ""))
    return {
        "filename": file.filename,
        "file_type": "video",
        "file_size_mb": round(len(contents) / (1024 * 1024), 2),
        "processing_time_seconds": elapsed,
        **result,
    }


@app.post("/api/detect")
@limiter.limit("10/hour")
async def detect_auto(request: Request, file: UploadFile = File(...)):
    """Auto-detect file type and route to the correct handler."""
    if file.content_type in ALLOWED_IMAGE_TYPES:
        return await detect_image(request, file)
    elif file.content_type in ALLOWED_VIDEO_TYPES:
        return await detect_video(request, file)
    else:
        raise HTTPException(
            status_code=400,
            detail="This file type isn't supported. Please upload a JPEG, PNG, WebP, MP4, MOV, AVI, or WebM file.",
        )


class URLRequest(BaseModel):
    url: str


def _is_private_ip(hostname: str) -> bool:
    """Check if hostname resolves to a private/loopback IP (SSRF protection)."""
    try:
        ip = socket.gethostbyname(hostname)
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved
    except (socket.gaierror, ValueError):
        return True  # Can't resolve = reject


CONTENT_TYPE_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
    "video/x-msvideo": ".avi",
    "video/avi": ".avi",
}


@app.post("/api/detect-url")
@limiter.limit("10/hour")
async def detect_url(request: Request, body: URLRequest):
    """Download a file from a URL and run it through the detection pipeline."""
    import requests as http_requests

    parsed = urlparse(body.url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Only http and https URLs are supported.")

    hostname = parsed.hostname or ""
    if not hostname or hostname == "localhost" or _is_private_ip(hostname):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "This link can't be checked for security reasons. Try downloading the file and uploading it directly.",
                "code": "URL_NOT_ALLOWED",
            },
        )

    # Stream download with size limit
    fd, tmp_path = tempfile.mkstemp()
    try:
        resp = http_requests.get(body.url, stream=True, timeout=15, allow_redirects=True)
        resp.raise_for_status()

        # Re-check final URL after redirects to prevent SSRF via open redirect
        final_url = urlparse(resp.url)
        final_host = final_url.hostname or ""
        if not final_host or final_host == "localhost" or _is_private_ip(final_host):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "This link can't be checked for security reasons. Try downloading the file and uploading it directly.",
                    "code": "URL_NOT_ALLOWED",
                },
            )

        content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()
        all_allowed = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES
        if content_type not in all_allowed:
            raise HTTPException(
                status_code=400,
                detail="The URL doesn't appear to point to a supported image or video file.",
            )

        downloaded = 0
        for chunk in resp.iter_content(chunk_size=65536):
            downloaded += len(chunk)
            if downloaded > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail="This file is too large. The maximum size is 50 MB.",
                )
            os.write(fd, chunk)
        os.close(fd)

        contents = open(tmp_path, "rb").read()

        # Determine file type and run analysis
        is_image = content_type in ALLOWED_IMAGE_TYPES
        start_time = time.time()

        if is_image:
            try:
                image = Image.open(io.BytesIO(contents))
            except Exception:
                raise HTTPException(status_code=400, detail="Could not open the image from this URL.")
            result = ai_detector.detect_image(image, raw_bytes=contents)
            heatmap_data = None
            try:
                heatmap_data = generate_heatmap(image)
            except Exception:
                pass
            elapsed = round(time.time() - start_time, 2)
            response = {
                "filename": os.path.basename(parsed.path) or "url_image",
                "file_type": "image",
                "file_size_mb": round(len(contents) / (1024 * 1024), 2),
                "processing_time_seconds": elapsed,
                **result,
            }
            if heatmap_data:
                response["heatmap"] = heatmap_data
            _update_stats(result.get("verdict", ""))
            return response
        else:
            processor = get_video_processor(ai_detector)
            result = processor.analyze_video(tmp_path)
            elapsed = round(time.time() - start_time, 2)
            _update_stats(result.get("verdict", ""))
            return {
                "filename": os.path.basename(parsed.path) or "url_video",
                "file_type": "video",
                "file_size_mb": round(len(contents) / (1024 * 1024), 2),
                "processing_time_seconds": elapsed,
                **result,
            }
    except HTTPException:
        raise
    except http_requests.exceptions.Timeout:
        raise HTTPException(
            status_code=400,
            detail="The URL took too long to respond. Please try again or download the file and upload it directly.",
        )
    except http_requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=400, detail="Could not download the file from this URL. Please check the link and try again."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ── Developer API (v1) ──────────────────────────────────────────────────────────

API_KEYS_FILE = os.path.join(os.path.dirname(__file__), "data", "api_keys.json")


def _get_api_key(request: Request) -> dict:
    """Validate X-API-Key header and enforce daily rate limit."""
    key = request.headers.get("X-API-Key", "")
    if not key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header.")
    if not os.path.exists(API_KEYS_FILE):
        raise HTTPException(status_code=401, detail="Invalid API key.")

    with open(API_KEYS_FILE) as f:
        keys = json.load(f)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    for entry in keys:
        if entry["key"] == key:
            if entry.get("last_reset") != today:
                entry["requests_today"] = 0
                entry["last_reset"] = today
            if entry["requests_today"] >= 100:
                raise HTTPException(status_code=429, detail="Daily API limit of 100 requests exceeded.")
            entry["requests_today"] += 1
            with open(API_KEYS_FILE, "w") as f:
                json.dump(keys, f, indent=2)
            return entry

    raise HTTPException(status_code=401, detail="Invalid API key.")


def _confidence_label(confidence: float, is_ai: bool) -> str:
    subject = "AI-generated" if is_ai else "authentic"
    if confidence >= 85:
        return f"We're very confident this is {subject}"
    if confidence >= 65:
        return f"We're fairly confident this is {subject}"
    if confidence >= 40:
        return "We have some concerns about this content"
    return "We're not certain \u2014 treat with caution"


@app.post("/api/v1/detect")
async def api_v1_detect(request: Request, file: UploadFile = File(...)):
    """Developer API: detect AI-generated content with API key auth."""
    key_entry = _get_api_key(request)

    contents = await file.read()
    _validate_upload(contents, file.content_type, file.filename or "")

    start_time = time.time()

    if file.content_type in ALLOWED_IMAGE_TYPES:
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception:
            raise HTTPException(status_code=400, detail="Could not open image file.")
        result = ai_detector.detect_image(image, raw_bytes=contents)
    elif file.content_type in ALLOWED_VIDEO_TYPES:
        suffix = os.path.splitext(file.filename or ".mp4")[1]
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        try:
            os.write(fd, contents)
            os.close(fd)
            processor = get_video_processor(ai_detector)
            result = processor.analyze_video(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    elapsed_ms = round((time.time() - start_time) * 1000)
    is_ai = result.get("verdict") == "AI-Generated"
    confidence = result.get("confidence", 0)

    verdict_str = "ai_generated" if is_ai else "authentic"
    if confidence < 40:
        verdict_str = "uncertain"

    signals = {}
    d = result.get("details", {})
    for key_name in [
        "ml_model_primary",
        "ml_model_deepfake",
        "frequency_analysis",
        "statistical_analysis",
        "texture_analysis",
        "srm_analysis",
        "color_analysis",
        "face_analysis",
        "metadata_analysis",
    ]:
        if key_name in d:
            short = key_name.replace("_analysis", "").replace("ml_model_", "ml_")
            signals[short] = d[key_name].get("ai_score", 0) / 100.0

    _update_stats(result.get("verdict", ""))

    return {
        "verdict": verdict_str,
        "confidence": round(confidence / 100.0, 2),
        "confidence_label": _confidence_label(confidence, is_ai),
        "explanation": result.get("explanation", ""),
        "signals": signals,
        "processing_time_ms": elapsed_ms,
    }


@app.get("/api/v1/usage")
async def api_v1_usage(request: Request):
    """Return usage stats for the current API key."""
    entry = _get_api_key(request)
    return {
        "name": entry["name"],
        "requests_today": entry["requests_today"],
        "daily_limit": 100,
        "created": entry.get("created", ""),
    }


@app.get("/api/docs")
async def api_docs():
    """Return developer API documentation as HTML."""
    from fastapi.responses import HTMLResponse

    html = """<!DOCTYPE html>
<html><head><title>AI Detector API</title>
<style>body{font-family:system-ui,sans-serif;max-width:800px;margin:40px auto;padding:0 20px;background:#0a0a0a;color:#e0e0e0}
h1{color:#818cf8}h2{color:#a5b4fc;border-bottom:1px solid #333;padding-bottom:8px}
code{background:#1a1a2e;padding:2px 6px;border-radius:4px;font-size:14px}
pre{background:#1a1a2e;padding:16px;border-radius:8px;overflow-x:auto;font-size:13px}
.endpoint{background:#111;border:1px solid #333;border-radius:8px;padding:16px;margin:16px 0}
.method{background:#818cf8;color:#fff;padding:2px 8px;border-radius:4px;font-weight:bold;font-size:12px}
</style></head><body>
<h1>AI Detector API v1</h1>
<p>Detect AI-generated images and videos programmatically.</p>

<h2>Authentication</h2>
<p>All requests require an <code>X-API-Key</code> header. Generate a key with:</p>
<pre>python scripts/generate_api_key.py --name "My App"</pre>

<h2>Endpoints</h2>

<div class="endpoint">
<p><span class="method">POST</span> <code>/api/v1/detect</code></p>
<p>Upload an image or video for analysis.</p>
<pre>curl -X POST \\
  -H "X-API-Key: YOUR_KEY" \\
  -F "file=@photo.jpg" \\
  https://yoursite.com/api/v1/detect</pre>
<p><strong>Response:</strong></p>
<pre>{
  "verdict": "ai_generated",
  "confidence": 0.87,
  "confidence_label": "We're very confident this is AI-generated",
  "explanation": "This image shows patterns consistent with AI generation...",
  "signals": {
    "ml_primary": 0.91,
    "frequency": 0.73,
    "statistical": 0.65,
    "texture": 0.58,
    "srm": 0.72,
    "color": 0.45,
    "metadata": 0.30
  },
  "processing_time_ms": 1240
}</pre>
</div>

<div class="endpoint">
<p><span class="method">GET</span> <code>/api/v1/usage</code></p>
<p>Check your API key usage.</p>
<pre>curl -H "X-API-Key: YOUR_KEY" https://yoursite.com/api/v1/usage</pre>
<p><strong>Response:</strong></p>
<pre>{
  "name": "My App",
  "requests_today": 42,
  "daily_limit": 100,
  "created": "2026-04-01T12:00:00Z"
}</pre>
</div>

<h2>Rate Limits</h2>
<p>100 requests per day per API key. Resets at midnight UTC.</p>

<h2>Supported Formats</h2>
<p>Images: JPEG, PNG, WebP, BMP, TIFF. Videos: MP4, MOV, AVI, WebM. Max 50MB.</p>
</body></html>"""
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.environ.get("HOST", "0.0.0.0"),  # noqa: S104  # nosec B104
        port=int(os.environ.get("PORT", "8000")),
        workers=int(os.environ.get("WORKERS", "2")),
        timeout_keep_alive=120,
    )
