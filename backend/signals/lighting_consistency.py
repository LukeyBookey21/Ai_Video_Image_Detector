"""
Lighting Consistency

AI-generated or composited images often have inconsistent lighting between
faces or regions. This signal detects faces with a Haar cascade and, for each
face, estimates the dominant light direction using a simplified
shape-from-shading approach (intensity-weighted image gradient azimuth plus a
brightness-centroid offset). With 2+ faces, large disagreement in estimated
light direction is a strong indicator of compositing/AI generation. With a
single face, contradictory left/right shading is a weak indicator.
"""

import numpy as np
from PIL import Image
import cv2


def _estimate_light_azimuth(face_gray: np.ndarray) -> float:
    """Estimate dominant light azimuth (radians) for a grayscale face patch.

    Combines an intensity-weighted gradient direction (shape-from-shading
    proxy) with the brightness-centroid offset relative to the face center.
    """
    g = face_gray.astype(np.float64)
    g_norm = g / (g.max() + 1e-10)

    # Image gradients (Sobel). Surfaces facing the light are brighter, so the
    # intensity-weighted mean gradient points roughly along the light azimuth.
    gx = cv2.Sobel(g, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_64F, 0, 1, ksize=3)

    weight = g_norm
    wsum = weight.sum() + 1e-10
    mean_gx = float((gx * weight).sum() / wsum)
    mean_gy = float((gy * weight).sum() / wsum)
    grad_azimuth = float(np.arctan2(mean_gy, mean_gx))

    # Brightness centroid offset relative to face center — points toward the
    # brightest region, another proxy for light direction.
    h, w = g.shape
    ys, xs = np.mgrid[0:h, 0:w]
    bw = g_norm
    bsum = bw.sum() + 1e-10
    cx = float((xs * bw).sum() / bsum)
    cy = float((ys * bw).sum() / bsum)
    off_x = cx - (w / 2.0)
    off_y = cy - (h / 2.0)
    centroid_azimuth = float(np.arctan2(off_y, off_x))

    # Combine the two unit-vector estimates and take the resulting azimuth.
    vx = np.cos(grad_azimuth) + np.cos(centroid_azimuth)
    vy = np.sin(grad_azimuth) + np.sin(centroid_azimuth)
    return float(np.arctan2(vy, vx))


def _angular_diff_deg(a: float, b: float) -> float:
    """Smallest absolute angular difference (degrees) between two radian angles."""
    d = a - b
    d = (d + np.pi) % (2.0 * np.pi) - np.pi
    return float(abs(np.degrees(d)))


def analyze(image: Image.Image) -> dict:
    """Detect lighting inconsistency between faces / within a single face."""
    try:
        img = np.array(image.convert("RGB"))
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        num_faces = int(len(faces))

        if num_faces == 0:
            return {
                "signal_name": "lighting_consistency",
                "score": 0.0,
                "confidence": 0.0,
                "details": {"faces": 0},
            }

        # Estimate light azimuth per face.
        azimuths = []
        for (x, y, w, h) in faces:
            patch = gray[y:y + h, x:x + w]
            if patch.size == 0 or patch.shape[0] < 8 or patch.shape[1] < 8:
                continue
            azimuths.append(_estimate_light_azimuth(patch))

        score = 0.0
        max_angle_diff = 0.0

        if len(azimuths) >= 2:
            # Strong signal: compare estimated light directions across faces.
            for i in range(len(azimuths)):
                for j in range(i + 1, len(azimuths)):
                    diff = _angular_diff_deg(azimuths[i], azimuths[j])
                    if diff > max_angle_diff:
                        max_angle_diff = diff

            # Map the max pairwise disagreement to a score (up to 0.4).
            # Disagreement above ~60 degrees is suspicious; scale toward 180.
            if max_angle_diff > 60.0:
                frac = (max_angle_diff - 60.0) / (180.0 - 60.0)
                frac = max(0.0, min(frac, 1.0))
                score = 0.1 + 0.3 * frac
            else:
                # Mild contribution even below threshold, proportional to spread.
                score = 0.1 * (max_angle_diff / 60.0)

        elif len(azimuths) == 1:
            # Weak signal: internal left/right lighting consistency.
            (x, y, w, h) = faces[0]
            patch = gray[y:y + h, x:x + w].astype(np.float64)
            half = patch.shape[1] // 2
            left = patch[:, :half]
            right = patch[:, half:]

            left_mean = float(left.mean()) if left.size else 0.0
            right_mean = float(right.mean()) if right.size else 0.0

            # Horizontal brightness gradient within each half.
            left_grad = float(left[:, -1].mean() - left[:, 0].mean()) if left.shape[1] >= 2 else 0.0
            right_grad = float(right[:, -1].mean() - right[:, 0].mean()) if right.shape[1] >= 2 else 0.0

            mean_brightness = (left_mean + right_mean) / 2.0 + 1e-10
            asymmetry = abs(left_mean - right_mean) / mean_brightness

            single_score = 0.0
            # Contradictory shading: halves brighten in opposite directions
            # (one lit from the left, the other from the right) -> inconsistent.
            if left_grad * right_grad < 0 and (abs(left_grad) + abs(right_grad)) > 5.0:
                single_score += 0.05
            # Unnaturally perfect symmetry (too little brightness asymmetry)
            # can indicate synthetic, evenly-lit faces.
            if asymmetry < 0.02:
                single_score += 0.05
            # Extreme asymmetry can also indicate odd compositing.
            elif asymmetry > 0.6:
                single_score += 0.03

            score = min(single_score, 0.1)
            max_angle_diff = 0.0

        score = float(min(max(score, 0.0), 1.0))
        confidence = float(min(score * 1.5, 1.0))

        return {
            "signal_name": "lighting_consistency",
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "details": {
                "faces": num_faces,
                "max_angle_diff": round(float(max_angle_diff), 4),
            },
        }
    except Exception:
        return {"signal_name": "lighting_consistency", "score": 0.0, "confidence": 0.0, "details": {}}
