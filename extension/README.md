# AI Detector Chrome Extension

Right-click any image on a webpage to check if it's AI-generated.

## Install (Development)

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked"
4. Select this `extension/` folder
5. The AI Detector icon appears in your toolbar

## Configure

Edit `background.js` line 3 to point to your backend:
```js
const API_BASE = 'https://your-deployed-backend.com';
```

## Usage

1. Right-click any image on a webpage
2. Click "Check if AI-generated"
3. The badge shows:
   - **AI** (red) — likely AI-generated
   - **OK** (green) — looks authentic
   - **ERR** (yellow) — could not check
4. Click the extension icon to see full details
