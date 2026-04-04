// AI Detector Chrome Extension — background service worker

// Configure this to point to your deployed backend
// For local development: http://localhost:8000
// For production: https://your-backend.railway.app
const API_BASE = 'http://localhost:8000';

// Create right-click context menu
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'check-ai-image',
    title: 'Check if AI-generated',
    contexts: ['image'],
  });
});

// Handle right-click on image
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== 'check-ai-image') return;

  const imageUrl = info.srcUrl;
  if (!imageUrl) return;

  // Show loading notification
  chrome.action.setBadgeText({ text: '...', tabId: tab.id });
  chrome.action.setBadgeBackgroundColor({ color: '#6366f1' });

  try {
    // Download image and convert to base64
    const response = await fetch(imageUrl);
    const blob = await response.blob();
    const reader = new FileReader();
    const base64 = await new Promise((resolve) => {
      reader.onloadend = () => resolve(reader.result.split(',')[1]);
      reader.readAsDataURL(blob);
    });

    // Send to detector API via base64 endpoint
    const result = await fetch(`${API_BASE}/api/detect/base64`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: base64, filename: imageUrl.split('/').pop() || 'image.jpg' }),
    });

    const data = await result.json();

    // Update badge with result
    const isAI = data.verdict === 'AI-Generated';
    chrome.action.setBadgeText({
      text: isAI ? 'AI' : 'OK',
      tabId: tab.id,
    });
    chrome.action.setBadgeBackgroundColor({
      color: isAI ? '#ef4444' : '#22c55e',
    });

    // Store result for popup
    chrome.storage.local.set({
      lastResult: {
        url: imageUrl,
        verdict: data.verdict,
        confidence: data.confidence,
        ai_probability: data.ai_probability,
        explanation: data.explanation || '',
        timestamp: new Date().toISOString(),
      },
    });

    // Clear badge after 10 seconds
    setTimeout(() => {
      chrome.action.setBadgeText({ text: '', tabId: tab.id });
    }, 10000);
  } catch (error) {
    chrome.action.setBadgeText({ text: 'ERR', tabId: tab.id });
    chrome.action.setBadgeBackgroundColor({ color: '#f59e0b' });

    chrome.storage.local.set({
      lastResult: {
        url: imageUrl,
        error: error.message,
        timestamp: new Date().toISOString(),
      },
    });
  }
});
