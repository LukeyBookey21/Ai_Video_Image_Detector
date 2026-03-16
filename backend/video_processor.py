"""
Video Processing Module — Enhanced

Frame extraction + per-frame analysis + temporal consistency checks.
AI videos often have frame-to-frame inconsistencies that real videos don't.
"""

import tempfile
import os
from PIL import Image
import cv2
import numpy as np
from detector import AIImageDetector


class VideoProcessor:
    def __init__(self, detector: AIImageDetector, max_frames: int = 15):
        self.detector = detector
        self.max_frames = max_frames

    def extract_frames(self, video_path: str) -> tuple:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0

        num_frames = min(self.max_frames, total_frames)
        if num_frames <= 0:
            cap.release()
            raise ValueError("Video has no frames")

        frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

        frames = []
        raw_frames = []  # Keep numpy arrays for temporal analysis
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                raw_frames.append(frame_rgb)
                pil_image = Image.fromarray(frame_rgb)
                frames.append(pil_image)

        cap.release()
        return frames, raw_frames, {
            "total_frames": total_frames,
            "fps": round(fps, 2),
            "duration_seconds": round(duration, 2),
            "resolution": f"{width}x{height}",
            "frames_analyzed": len(frames),
        }

    def analyze_temporal_consistency(self, raw_frames: list) -> dict:
        """Analyze frame-to-frame consistency. AI videos have different temporal patterns."""
        if len(raw_frames) < 3:
            return {"temporal_score": 0.0}

        scores = []

        # ── Optical flow consistency ──
        # Real video has smooth, physically plausible motion
        # AI video can have sudden jumps or unrealistic motion
        flow_magnitudes = []
        for i in range(len(raw_frames) - 1):
            prev_gray = cv2.cvtColor(raw_frames[i], cv2.COLOR_RGB2GRAY)
            next_gray = cv2.cvtColor(raw_frames[i + 1], cv2.COLOR_RGB2GRAY)

            # Resize for speed
            h, w = prev_gray.shape
            scale = min(256 / h, 256 / w, 1.0)
            if scale < 1.0:
                new_h, new_w = int(h * scale), int(w * scale)
                prev_gray = cv2.resize(prev_gray, (new_w, new_h))
                next_gray = cv2.resize(next_gray, (new_w, new_h))

            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, next_gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0,
            )
            mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
            flow_magnitudes.append(np.mean(mag))

        if flow_magnitudes:
            flow_std = np.std(flow_magnitudes)
            flow_mean = np.mean(flow_magnitudes)

            # Very uniform motion (AI tends to have smoother, more uniform flow)
            if flow_std < 0.5 and flow_mean > 0.1:
                scores.append(0.15)

            # Sudden large jumps
            flow_diffs = np.abs(np.diff(flow_magnitudes))
            if np.max(flow_diffs) > 3 * (np.mean(flow_diffs) + 1e-10):
                scores.append(0.12)

        # ── Frame-to-frame noise consistency ──
        noise_levels = []
        for frame in raw_frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float64)
            h, w = gray.shape
            scale = min(256 / h, 256 / w, 1.0)
            if scale < 1.0:
                gray = cv2.resize(gray, (int(w * scale), int(h * scale))).astype(np.float64)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            noise = gray - blurred
            noise_levels.append(np.std(noise))

        noise_variation = np.std(noise_levels) / (np.mean(noise_levels) + 1e-10)

        # AI videos have very consistent noise across frames
        if noise_variation < 0.05:
            scores.append(0.18)
        elif noise_variation < 0.12:
            scores.append(0.10)

        # ── Flickering detection ──
        # AI videos sometimes have subtle brightness flickering
        brightness_values = [np.mean(f) for f in raw_frames]
        brightness_diffs = np.abs(np.diff(brightness_values))
        if len(brightness_diffs) > 2:
            flicker_score = np.std(brightness_diffs) / (np.mean(brightness_diffs) + 1e-10)
            if flicker_score > 2.0:
                scores.append(0.10)

        temporal_ai_score = min(sum(scores), 1.0)

        return {
            "temporal_score": round(temporal_ai_score, 4),
            "flow_consistency": round(float(np.std(flow_magnitudes)) if flow_magnitudes else 0, 4),
            "noise_consistency": round(float(noise_variation), 4),
        }

    def analyze_video(self, video_path: str) -> dict:
        frames, raw_frames, video_info = self.extract_frames(video_path)

        if not frames:
            return {
                "verdict": "Error",
                "confidence": 0,
                "error": "Could not extract frames from video",
            }

        # Per-frame analysis
        frame_results = []
        ai_scores = []
        for i, frame in enumerate(frames):
            result = self.detector.detect_image(frame)
            frame_results.append({
                "frame_index": i,
                "ai_probability": result["ai_probability"],
                "verdict": result["verdict"],
            })
            ai_scores.append(result["ai_probability"])

        # Temporal consistency analysis
        temporal = self.analyze_temporal_consistency(raw_frames)

        avg_ai_score = np.mean(ai_scores)
        max_ai_score = np.max(ai_scores)
        min_ai_score = np.min(ai_scores)

        # Weighted combination: frames (50%) + max frame (25%) + temporal (25%)
        combined_score = (
            0.50 * avg_ai_score
            + 0.25 * max_ai_score
            + 0.25 * (temporal["temporal_score"] * 100)
        )

        verdict = "AI-Generated" if combined_score > 42.0 else "Real/Authentic"
        confidence = combined_score if combined_score > 42.0 else (100.0 - combined_score)

        return {
            "verdict": verdict,
            "confidence": round(confidence, 1),
            "ai_probability": round(combined_score, 1),
            "detection_mode": self.detector.ml_mode and "ml_ensemble" or "heuristic_only",
            "video_info": video_info,
            "frame_analysis": {
                "average_ai_score": round(avg_ai_score, 1),
                "max_ai_score": round(max_ai_score, 1),
                "min_ai_score": round(min_ai_score, 1),
                "per_frame": frame_results,
            },
            "temporal_analysis": {
                "temporal_ai_score": round(temporal["temporal_score"] * 100, 1),
                "flow_consistency": temporal.get("flow_consistency", 0),
                "noise_consistency": temporal.get("noise_consistency", 0),
            },
        }


video_processor = None


def get_video_processor(detector: AIImageDetector) -> VideoProcessor:
    global video_processor
    if video_processor is None:
        video_processor = VideoProcessor(detector)
    return video_processor
