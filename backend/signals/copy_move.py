"""
Copy-Move Forgery Detection

Uses ORB keypoints (fast, no patent issues) to detect duplicated regions
within an image. Many matched keypoints with a consistent geometric
transform indicate a copy-move forgery (cloned/duplicated region).
"""

import numpy as np
from PIL import Image
import cv2


def analyze(image: Image.Image) -> dict:
    """Detect copy-move forgery (duplicated regions)."""
    try:
        img = np.array(image.convert("RGB"))
        h, w = img.shape[:2]

        # Skip tiny images — not enough features
        if h < 256 or w < 256:
            return {"signal_name": "copy_move", "score": 0.0, "confidence": 0.0, "details": {"skipped": True}}

        # Resize for speed
        scale = min(512 / max(h, w), 1.0)
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)))

        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        orb = cv2.ORB_create(nfeatures=1000)
        kps, descs = orb.detectAndCompute(gray, None)

        if descs is None or len(kps) < 20:
            return {
                "signal_name": "copy_move",
                "score": 0.0,
                "confidence": 0.0,
                "details": {"keypoints": len(kps) if kps else 0},
            }

        # Self-match descriptors
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(descs, descs, k=2)

        good_matches = []
        for pair in matches:
            if len(pair) < 2:
                continue
            m, n = pair
            if m.queryIdx == m.trainIdx:
                continue
            p1 = np.array(kps[m.queryIdx].pt)
            p2 = np.array(kps[m.trainIdx].pt)
            dist = np.linalg.norm(p1 - p2)
            # Spatially separated but visually matching = potential clone
            if dist > 30 and m.distance < 40:
                good_matches.append(m)

        num_matches = len(good_matches)

        forgery_detected = False
        inlier_count = 0
        if num_matches >= 10:
            src_pts = np.float32([kps[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kps[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            _, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            if mask is not None:
                inlier_count = int(np.sum(mask))
                forgery_detected = inlier_count > 15

        scores = []
        if forgery_detected:
            scores.append(0.30)
        elif num_matches > 50:
            scores.append(0.10)

        score = min(sum(scores), 1.0)
        confidence = min(score * 1.5, 1.0)

        return {
            "signal_name": "copy_move",
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "details": {
                "keypoints": len(kps),
                "matches": num_matches,
                "inliers": inlier_count,
                "forgery_detected": forgery_detected,
            },
        }
    except Exception:
        return {"signal_name": "copy_move", "score": 0.0, "confidence": 0.0, "details": {}}
