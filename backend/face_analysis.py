"""
Face Detection + Deepfake-Specific Analysis

Uses OpenCV's face detector to find faces, then applies face-specific
forensic analysis: symmetry checks, skin texture analysis, eye/mouth
region consistency, and boundary artifact detection.
"""

import numpy as np
from PIL import Image, ImageFilter
import cv2
from scipy.stats import kurtosis


class FaceAnalyzer:
    """Detects faces and runs deepfake-specific forensic analysis."""

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

    def analyze(self, image: Image.Image) -> dict:
        img_cv = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

        if len(faces) == 0:
            return {
                "faces_found": 0,
                "ai_probability": 0.0,
                "face_details": [],
            }

        face_results = []
        all_scores = []

        for x, y, w, h in faces:
            # Extract face region with margin
            margin = int(0.15 * max(w, h))
            fx1 = max(0, x - margin)
            fy1 = max(0, y - margin)
            fx2 = min(img_cv.shape[1], x + w + margin)
            fy2 = min(img_cv.shape[0], y + h + margin)

            face_rgb = img_cv[fy1:fy2, fx1:fx2]
            face_gray = gray[fy1:fy2, fx1:fx2]

            score, details = self._analyze_face(face_rgb, face_gray, w, h)
            face_results.append(
                {
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "ai_score": round(score, 4),
                    **details,
                }
            )
            all_scores.append(score)

        avg_score = float(np.mean(all_scores)) if all_scores else 0.0

        return {
            "faces_found": len(faces),
            "ai_probability": round(avg_score, 4),
            "face_details": face_results,
        }

    def _analyze_face(self, face_bgr, face_gray, face_w, face_h) -> tuple:
        """Analyze a single face region for deepfake indicators."""
        scores = []
        details = {}

        h, w = face_gray.shape

        # ── 1. Symmetry Analysis ──
        # Real faces have slight natural asymmetry; AI can be too symmetric or too asymmetric
        if w > 20:
            half_w = w // 2
            left = face_gray[:, :half_w]
            right = np.fliplr(face_gray[:, w - half_w :])
            min_h = min(left.shape[0], right.shape[0])
            min_w = min(left.shape[1], right.shape[1])
            left = left[:min_h, :min_w].astype(np.float64)
            right = right[:min_h, :min_w].astype(np.float64)

            symmetry_diff = np.mean(np.abs(left - right))
            details["symmetry_diff"] = round(float(symmetry_diff), 2)

            # Too symmetric
            if symmetry_diff < 5:
                scores.append(0.20)
            elif symmetry_diff < 10:
                scores.append(0.08)

        # ── 2. Skin Texture Analysis ──
        # AI skin tends to be unrealistically smooth
        skin_region = face_gray[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]  # Center of face
        if skin_region.size > 100:
            skin_noise = np.std(
                skin_region.astype(np.float64) - cv2.GaussianBlur(skin_region, (5, 5), 0).astype(np.float64)
            )
            details["skin_noise"] = round(float(skin_noise), 2)

            if skin_noise < 2.0:
                scores.append(0.22)
            elif skin_noise < 4.0:
                scores.append(0.12)

        # ── 3. Boundary Analysis ──
        # Deepfakes often have artifacts at the face/background boundary
        # Check the edges of the face region
        edge_ring_top = face_gray[: max(3, h // 10), :]
        edge_ring_bot = face_gray[-(max(3, h // 10)) :, :]
        edge_ring_left = face_gray[:, : max(3, w // 10)]
        edge_ring_right = face_gray[:, -(max(3, w // 10)) :]

        boundary_regions = [edge_ring_top, edge_ring_bot, edge_ring_left, edge_ring_right]
        boundary_gradients = []
        for region in boundary_regions:
            if region.size > 0:
                g = np.mean(np.abs(np.diff(region.astype(np.float64), axis=0))) if region.shape[0] > 1 else 0
                boundary_gradients.append(g)

        avg_boundary = np.mean(boundary_gradients) if boundary_gradients else 0
        details["boundary_gradient"] = round(float(avg_boundary), 2)

        # Sharp boundaries = possible face swap
        if avg_boundary > 20:
            scores.append(0.15)

        # ── 4. Color consistency ──
        if face_bgr.shape[0] > 10 and face_bgr.shape[1] > 10:
            face_lab = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2LAB).astype(np.float64)
            center = face_lab[h // 3 : 2 * h // 3, w // 3 : 2 * w // 3]
            border = np.concatenate(
                [
                    face_lab[: h // 6, :].reshape(-1, 3),
                    face_lab[-(h // 6) :, :].reshape(-1, 3),
                ]
            )

            if center.size > 0 and border.size > 0:
                center_mean = np.mean(center.reshape(-1, 3), axis=0)
                border_mean = np.mean(border, axis=0)
                color_diff = np.linalg.norm(center_mean - border_mean)
                details["face_color_diff"] = round(float(color_diff), 2)

                # Large color difference between face center and boundary
                if color_diff > 30:
                    scores.append(0.12)

        # ── 5. Eye detection quality ──
        eyes = self.eye_cascade.detectMultiScale(face_gray, scaleFactor=1.1, minNeighbors=3)
        details["eyes_detected"] = len(eyes)

        # Deepfakes sometimes have eye issues
        if len(eyes) == 0:
            scores.append(0.10)  # No eyes detected in face
        elif len(eyes) == 1:
            scores.append(0.08)  # Asymmetric eye detection

        total_score = min(sum(scores), 1.0)
        return total_score, details
