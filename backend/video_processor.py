"""
Video Processing Module
Extracts frames from uploaded videos and runs detection on each frame.
"""

import tempfile
import os
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
from detector import AIImageDetector


class VideoProcessor:
    def __init__(self, detector: AIImageDetector, max_frames: int = 10):
        self.detector = detector
        self.max_frames = max_frames

    def extract_frames(self, video_path: str) -> list[Image.Image]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0

        # Pick evenly spaced frames
        num_frames = min(self.max_frames, total_frames)
        if num_frames <= 0:
            cap.release()
            raise ValueError("Video has no frames")

        frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

        frames = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                frames.append(pil_image)

        cap.release()
        return frames, {
            "total_frames": total_frames,
            "fps": round(fps, 2),
            "duration_seconds": round(duration, 2),
            "frames_analyzed": len(frames),
        }

    def analyze_video(self, video_path: str) -> dict:
        frames, video_info = self.extract_frames(video_path)

        if not frames:
            return {
                "verdict": "Error",
                "confidence": 0,
                "error": "Could not extract frames from video",
            }

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

        avg_ai_score = np.mean(ai_scores)
        max_ai_score = np.max(ai_scores)
        min_ai_score = np.min(ai_scores)

        # Use weighted average: mean (60%) + max (40%) to catch partial deepfakes
        combined_score = 0.6 * avg_ai_score + 0.4 * max_ai_score

        verdict = "AI-Generated" if combined_score > 50.0 else "Real/Authentic"
        confidence = combined_score if combined_score > 50.0 else (100.0 - combined_score)

        return {
            "verdict": verdict,
            "confidence": round(confidence, 1),
            "ai_probability": round(combined_score, 1),
            "video_info": video_info,
            "frame_analysis": {
                "average_ai_score": round(avg_ai_score, 1),
                "max_ai_score": round(max_ai_score, 1),
                "min_ai_score": round(min_ai_score, 1),
                "per_frame": frame_results,
            },
        }


video_processor = None


def get_video_processor(detector: AIImageDetector) -> VideoProcessor:
    global video_processor
    if video_processor is None:
        video_processor = VideoProcessor(detector)
    return video_processor
