"""
WhatsApp Bot for AI Image/Video Detection

Uses the Twilio WhatsApp API to receive media messages,
analyse them through the detection pipeline, and reply with verdicts.

Setup:
1. Create a Twilio account at twilio.com
2. Enable the WhatsApp sandbox
3. Set environment variables:
   - TWILIO_ACCOUNT_SID
   - TWILIO_AUTH_TOKEN
   - TWILIO_WHATSAPP_NUMBER (e.g., whatsapp:+14155238886)
   - DETECTOR_API_URL (e.g., http://localhost:8000)
4. Run: python bot.py
5. Configure Twilio webhook to point to: https://your-server.com/webhook
"""

import io
import os
import logging

from flask import Flask, request as flask_request
from twilio.twiml.messaging_response import MessagingResponse

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("whatsapp-bot")

app = Flask(__name__)

DETECTOR_API = os.environ.get("DETECTOR_API_URL", "http://localhost:8000")
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")


def get_confidence_phrase(confidence, is_ai):
    subject = "AI-generated" if is_ai else "authentic"
    if confidence >= 85:
        return f"We're very confident this is {subject}"
    elif confidence >= 65:
        return f"We're fairly confident this is {subject}"
    elif confidence >= 40:
        return "We have some concerns about this content"
    return "We're not certain — treat with caution"


def analyse_media(media_url, content_type):
    """Download media from Twilio and send to detector API."""
    try:
        # Download from Twilio (requires auth)
        auth = (TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID else None
        resp = requests.get(media_url, auth=auth, timeout=30)
        resp.raise_for_status()

        # Send to detector
        files = {"file": ("media", io.BytesIO(resp.content), content_type)}
        result = requests.post(f"{DETECTOR_API}/api/detect", files=files, timeout=120)
        result.raise_for_status()
        return result.json()
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return None


@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming WhatsApp messages."""
    resp = MessagingResponse()

    num_media = int(flask_request.values.get("NumMedia", 0))
    from_number = flask_request.values.get("From", "unknown")
    body = flask_request.values.get("Body", "").strip().lower()

    logger.info(f"Message from {from_number}: {num_media} media, body='{body}'")

    # Handle text-only messages
    if num_media == 0:
        if body in ("help", "hi", "hello", "start"):
            resp.message(
                "Hi! I'm the AI Detector bot. 🔍\n\n"
                "Send me an image or video and I'll check if it's AI-generated.\n\n"
                "Just forward a suspicious photo or video to this chat."
            )
        else:
            resp.message(
                "Send me an image or video to check.\n"
                "I'll tell you if it looks AI-generated."
            )
        return str(resp)

    # Process each media attachment
    for i in range(num_media):
        media_url = flask_request.values.get(f"MediaUrl{i}")
        content_type = flask_request.values.get(f"MediaContentType{i}", "")

        if not media_url:
            continue

        logger.info(f"Analysing media: {content_type}")

        result = analyse_media(media_url, content_type)

        if not result:
            resp.message("Sorry, I couldn't analyse that file. Try sending a clear photo or short video.")
            continue

        verdict = result.get("verdict", "Unknown")
        confidence = result.get("confidence", 0)
        ai_prob = result.get("ai_probability", 0)
        explanation = result.get("explanation", "")
        is_ai = verdict == "AI-Generated"

        phrase = get_confidence_phrase(confidence, is_ai)

        if is_ai:
            msg = (
                f"⚠️ *Likely AI-Generated*\n\n"
                f"{phrase}.\n\n"
                f"{explanation[:200] if explanation else ''}\n\n"
                f"*What to do:*\n"
                f"• Don't share this content\n"
                f"• Don't send money or personal info based on it\n"
                f"• Report scams to Action Fraud: actionfraud.police.uk"
            )
        else:
            msg = (
                f"✓ *Looks Authentic*\n\n"
                f"{phrase}.\n\n"
                f"{explanation[:200] if explanation else ''}\n\n"
                f"This appears genuine, but always verify important claims through official sources."
            )

        resp.message(msg)

    return str(resp)


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "whatsapp-bot"}


if __name__ == "__main__":
    port = int(os.environ.get("BOT_PORT", 5001))
    logger.info(f"WhatsApp bot starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
