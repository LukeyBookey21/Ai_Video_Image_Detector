"""
PDF Forensic Report Generator

Produces a professional, downloadable forensic report for an analysis result
using reportlab. Includes verdict banner, confidence, per-signal bar chart,
file metadata, timestamp and analysis ID.
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def _draw_bar(c, x, y, width, value, label, max_value=100):
    """Draw a horizontal labelled bar."""
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#444444"))
    c.drawString(x, y, label)

    bar_x = x + 110
    bar_w = width - 110
    # Background
    c.setFillColor(colors.HexColor("#e8e8e8"))
    c.roundRect(bar_x, y - 1, bar_w, 7, 2, fill=1, stroke=0)
    # Fill
    frac = max(0.0, min(value / max_value, 1.0))
    if value > 60:
        col = colors.HexColor("#e03131")
    elif value > 33:
        col = colors.HexColor("#f59f00")
    else:
        col = colors.HexColor("#2f9e44")
    c.setFillColor(col)
    if frac > 0:
        c.roundRect(bar_x, y - 1, bar_w * frac, 7, 2, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#444444"))
    c.drawRightString(x + width + 18, y, f"{value:.0f}%")


def generate_report(result: dict) -> bytes:
    """Generate a PDF forensic report. Returns PDF bytes."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    margin = 20 * mm

    verdict = result.get("verdict", "Unknown")
    is_ai = verdict == "AI-Generated"
    ai_prob = result.get("ai_probability", 0)
    confidence = result.get("confidence", 0)
    filename = result.get("filename", "unknown")
    analysis_id = result.get("analysis_id", datetime.utcnow().strftime("%Y%m%d%H%M%S"))
    model_version = result.get("model_version", "v2.1")

    # ── Header ──
    c.setFillColor(colors.HexColor("#4f46e5"))
    c.rect(0, h - 28 * mm, w, 28 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, h - 18 * mm, "AI Detector — Forensic Report")
    c.setFont("Helvetica", 9)
    c.drawString(margin, h - 24 * mm, f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    y = h - 42 * mm

    # ── Verdict banner ──
    banner_col = colors.HexColor("#e03131") if is_ai else colors.HexColor("#2f9e44")
    c.setFillColor(banner_col)
    c.roundRect(margin, y - 18 * mm, w - 2 * margin, 18 * mm, 4, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    label = "LIKELY AI-GENERATED" if is_ai else "LIKELY AUTHENTIC"
    c.drawString(margin + 8 * mm, y - 8 * mm, label)
    c.setFont("Helvetica", 10)
    c.drawString(margin + 8 * mm, y - 14 * mm, f"AI probability: {ai_prob:.1f}%   |   Confidence: {confidence:.1f}%")

    y -= 28 * mm

    # ── File info ──
    c.setFillColor(colors.HexColor("#222222"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "File Information")
    y -= 6 * mm
    c.setFont("Helvetica", 9)
    info = [
        ("Filename", str(filename)),
        ("File type", str(result.get("file_type", "image"))),
        ("Size", f"{result.get('file_size_mb', '?')} MB"),
        ("Detection mode", str(result.get("detection_mode", "heuristic_only"))),
        ("Model version", str(model_version)),
        ("Analysis ID", str(analysis_id)),
    ]
    for k, v in info:
        c.setFillColor(colors.HexColor("#666666"))
        c.drawString(margin, y, f"{k}:")
        c.setFillColor(colors.HexColor("#222222"))
        c.drawString(margin + 35 * mm, y, v[:60])
        y -= 5 * mm

    y -= 4 * mm

    # ── Explanation ──
    explanation = result.get("explanation", "")
    if explanation:
        c.setFillColor(colors.HexColor("#222222"))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "Summary")
        y -= 6 * mm
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#444444"))
        # Word wrap
        words = explanation.split()
        line = ""
        for word in words:
            if len(line) + len(word) > 95:
                c.drawString(margin, y, line)
                y -= 4.5 * mm
                line = ""
            line += word + " "
        if line.strip():
            c.drawString(margin, y, line)
            y -= 4.5 * mm

    y -= 4 * mm

    # ── Signal breakdown bar chart ──
    c.setFillColor(colors.HexColor("#222222"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Signal Breakdown")
    y -= 7 * mm

    details = result.get("details", {})
    signal_map = [
        ("Metadata / EXIF", "metadata_analysis"),
        ("Frequency (DCT/FFT)", "frequency_analysis"),
        ("Statistical noise", "statistical_analysis"),
        ("Texture", "texture_analysis"),
        ("SRM fingerprint", "srm_analysis"),
        ("Colour space", "color_analysis"),
        ("Face analysis", "face_analysis"),
    ]
    for label, key in signal_map:
        if key in details:
            score = details[key].get("ai_score", 0)
            _draw_bar(c, margin, y, w - 2 * margin - 20, score, label)
            y -= 7 * mm

    # Modular signals (score is 0-1, convert to %)
    mod_map = [
        ("GAN fingerprint", "gan_fingerprint"),
        ("Diffusion artifacts", "diffusion_artifacts"),
        ("Noise map", "noise_map"),
        ("PRNU sensor", "prnu"),
        ("Copy-move", "copy_move"),
    ]
    for label, key in mod_map:
        if key in details and "score" in details[key]:
            score = details[key]["score"] * 100
            _draw_bar(c, margin, y, w - 2 * margin - 20, score, label)
            y -= 7 * mm

    # ── Footer ──
    c.setFillColor(colors.HexColor("#999999"))
    c.setFont("Helvetica", 7)
    c.drawString(margin, 12 * mm, f"Analysis ID: {analysis_id}   |   Model {model_version}")
    c.drawRightString(
        w - margin,
        12 * mm,
        "This report is an automated forensic estimate, not a definitive verdict.",
    )

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
