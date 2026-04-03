# WhatsApp Bot — AI Detector

A WhatsApp bot that analyses forwarded images and videos for AI generation.

## How it works

1. User forwards a suspicious image/video to the WhatsApp bot number
2. Bot downloads the media, sends it to the AI Detector API
3. Bot replies with the verdict in plain English

## Setup

### 1. Twilio Account

1. Sign up at [twilio.com](https://www.twilio.com)
2. Go to **Messaging > Try it out > Send a WhatsApp message**
3. Follow the sandbox setup instructions
4. Note your Account SID, Auth Token, and WhatsApp number

### 2. Environment Variables

```bash
export TWILIO_ACCOUNT_SID=your_sid_here
export TWILIO_AUTH_TOKEN=your_token_here
export TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
export DETECTOR_API_URL=http://localhost:8000
```

### 3. Run the Bot

```bash
pip install -r requirements.txt
python bot.py
```

### 4. Configure Webhook

In the Twilio console, set the webhook URL to:
```
https://your-server.com/webhook
```

For local development, use [ngrok](https://ngrok.com):
```bash
ngrok http 5001
```
Then set the Twilio webhook to the ngrok HTTPS URL + `/webhook`.

## Usage

Send a message to the WhatsApp sandbox number:
- **"help"** — Get instructions
- **Send an image** — Get AI detection verdict
- **Send a video** — Get deepfake detection verdict

## Example Response

```
⚠️ *Likely AI-Generated*

We're fairly confident this is AI-generated.

This is a PNG file with no camera data at all — a very common format
for AI-generated images.

*What to do:*
• Don't share this content
• Don't send money or personal info based on it
• Report scams to Action Fraud: actionfraud.police.uk
```
