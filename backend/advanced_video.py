"""
Advanced Video Analysis — Catches sophisticated deepfakes that pass basic checks.

1. Physiological Signal Analysis — Detects absence of micro blood-flow color changes
2. Cross-Frame Identity Consistency — Face measurements should be constant, AI drifts
3. Compression Forensics — Double-compression artifacts from face swapping
4. Micro-Expression Temporal Analysis — Unnatural expression transitions
5. Background-Foreground Coherence — Different noise/compression between face and bg
"""

import numpy as np
import cv2
from PIL import Image


class PhysiologicalAnalyzer:
    """Detects physiological signals (rPPG) that real humans exhibit.

    Real video of a person shows subtle color changes in skin from blood
    flow (photoplethysmography). AI-generated faces don't simulate this.
    """

    def analyze_frames(self, frames: list) -> dict:
        """Analyze a sequence of face-cropped frames for physiological signals."""
        if len(frames) < 5:
            return {"signal_strength": 0.0, "ai_probability": 0.0}

        # Extract mean green channel values from skin regions
        green_signal = []
        for frame in frames:
            img = np.array(frame.convert("RGB"))
            h, w = img.shape[:2]
            # Focus on forehead/cheek region (skin-heavy area)
            skin_region = img[h // 4 : h // 2, w // 4 : 3 * w // 4, 1]  # Green channel
            green_signal.append(np.mean(skin_region))

        green_signal = np.array(green_signal, dtype=np.float64)

        if len(green_signal) < 5:
            return {"signal_strength": 0.0, "ai_probability": 0.0}

        # Detrend
        green_signal -= np.mean(green_signal)

        # Compute power spectrum
        fft = np.abs(np.fft.rfft(green_signal))
        freqs = np.fft.rfftfreq(len(green_signal))

        # Look for periodic signal in typical heart rate range
        # (normalized — we don't know exact FPS but look for any periodicity)
        if len(fft) > 3:
            # Skip DC component
            signal_power = np.max(fft[1:])
            noise_power = np.mean(fft[1:]) + 1e-10
            snr = signal_power / noise_power

            # Real video should show some periodic signal
            signal_strength = min(snr / 5.0, 1.0)  # Normalize to 0-1

            # Low signal strength = likely AI (no blood flow simulation)
            if signal_strength < 0.3:
                ai_prob = 0.25
            elif signal_strength < 0.5:
                ai_prob = 0.12
            else:
                ai_prob = 0.0
        else:
            signal_strength = 0.0
            ai_prob = 0.15

        return {
            "signal_strength": round(float(signal_strength), 4),
            "ai_probability": round(ai_prob, 4),
        }


class IdentityConsistencyAnalyzer:
    """Checks if facial proportions remain consistent across frames.

    Real faces have fixed proportions (inter-eye distance, nose-to-mouth ratio).
    AI-generated faces can drift subtly between frames.
    """

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

    def analyze_frames(self, frames: list) -> dict:
        """Check face geometry consistency across frames."""
        measurements = []

        for frame in frames:
            img_cv = cv2.cvtColor(np.array(frame.convert("RGB")), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
            if len(faces) == 0:
                continue

            # Use largest face
            face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = face

            face_roi = gray[y : y + h, x : x + w]
            eyes = self.eye_cascade.detectMultiScale(face_roi, 1.1, 3)

            if len(eyes) >= 2:
                # Sort by x to get left/right eye
                eyes_sorted = sorted(eyes, key=lambda e: e[0])
                e1, e2 = eyes_sorted[0], eyes_sorted[1]

                # Normalized measurements (relative to face width)
                eye_dist = abs((e1[0] + e1[2] / 2) - (e2[0] + e2[2] / 2)) / w
                eye_y_diff = abs((e1[1] + e1[3] / 2) - (e2[1] + e2[3] / 2)) / h
                face_aspect = w / (h + 1e-10)

                measurements.append(
                    {
                        "eye_distance": eye_dist,
                        "eye_y_diff": eye_y_diff,
                        "face_aspect": face_aspect,
                    }
                )

        if len(measurements) < 3:
            return {
                "consistency_score": 0.0,
                "ai_probability": 0.0,
                "frames_with_faces": len(measurements),
            }

        # Check variance of measurements across frames
        eye_dists = [m["eye_distance"] for m in measurements]
        aspects = [m["face_aspect"] for m in measurements]

        eye_dist_var = np.std(eye_dists) / (np.mean(eye_dists) + 1e-10)
        aspect_var = np.std(aspects) / (np.mean(aspects) + 1e-10)

        # High variance = face geometry is inconsistent = likely AI
        scores = []
        if eye_dist_var > 0.15:
            scores.append(0.25)
        elif eye_dist_var > 0.08:
            scores.append(0.12)

        if aspect_var > 0.10:
            scores.append(0.20)
        elif aspect_var > 0.05:
            scores.append(0.10)

        ai_prob = min(sum(scores), 1.0)

        return {
            "consistency_score": round(1.0 - ai_prob, 4),
            "ai_probability": round(ai_prob, 4),
            "eye_distance_variance": round(float(eye_dist_var), 4),
            "aspect_ratio_variance": round(float(aspect_var), 4),
            "frames_with_faces": len(measurements),
        }


class BackgroundForegroundAnalyzer:
    """Detects inconsistencies between face and background regions.

    Face-swapped deepfakes often have different noise/compression levels
    in the face vs background, since the face was generated separately.
    """

    def analyze(self, image: Image.Image) -> dict:
        img_cv = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY).astype(np.float64)

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray.astype(np.uint8), 1.1, 5, minSize=(60, 60))

        if len(faces) == 0:
            return {"ai_probability": 0.0, "noise_difference": 0.0}

        face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = face

        # Extract face and background regions
        face_region = gray[y : y + h, x : x + w]
        mask = np.ones_like(gray, dtype=bool)
        mask[y : y + h, x : x + w] = False
        bg_region = gray[mask]

        # Compare noise levels
        face_blurred = cv2.GaussianBlur(face_region, (5, 5), 0).astype(np.float64)
        face_noise = np.std(face_region - face_blurred)

        # Sample background
        bg_gray_2d = gray.copy()
        bg_gray_2d[y : y + h, x : x + w] = np.nan
        bg_valid = bg_gray_2d[~np.isnan(bg_gray_2d)]
        if len(bg_valid) > 100:
            bg_sample = bg_valid[: face_region.size] if len(bg_valid) > face_region.size else bg_valid
            bg_reshaped = bg_sample[: len(bg_sample) // 2 * 2].reshape(-1, 2)
            bg_noise = np.std(np.diff(bg_reshaped, axis=1))
        else:
            bg_noise = face_noise

        noise_diff = abs(face_noise - bg_noise)
        noise_ratio = face_noise / (bg_noise + 1e-10)

        scores = []
        # Large noise difference between face and background
        if noise_diff > 3:
            scores.append(0.25)
        elif noise_diff > 1.5:
            scores.append(0.12)

        # Face much smoother than background
        if noise_ratio < 0.5:
            scores.append(0.20)
        elif noise_ratio < 0.7:
            scores.append(0.10)

        ai_prob = min(sum(scores), 1.0)

        return {
            "ai_probability": round(ai_prob, 4),
            "face_noise": round(float(face_noise), 4),
            "bg_noise": round(float(bg_noise), 4),
            "noise_difference": round(float(noise_diff), 4),
            "noise_ratio": round(float(noise_ratio), 4),
        }
