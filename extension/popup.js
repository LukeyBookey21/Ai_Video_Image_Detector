// Populate popup with last result
chrome.storage.local.get('lastResult', ({ lastResult }) => {
  const content = document.getElementById('content');

  if (!lastResult) return;

  if (lastResult.error) {
    content.innerHTML = `
      <div class="result error">
        <div class="verdict" style="color:#f59e0b">Could not check</div>
        <div class="confidence">${lastResult.error}</div>
        <div class="url">${lastResult.url || ''}</div>
      </div>
    `;
    return;
  }

  const isAI = lastResult.verdict === 'AI-Generated';
  content.innerHTML = `
    <div class="result ${isAI ? 'ai' : 'real'}">
      <div class="verdict ${isAI ? 'ai' : 'real'}">${
        isAI ? '⚠️ Likely AI-Generated' : '✓ Looks Authentic'
      }</div>
      <div class="confidence">${lastResult.confidence}% confidence — ${lastResult.ai_probability}% AI probability</div>
      ${lastResult.explanation ? `<div class="explanation">${lastResult.explanation}</div>` : ''}
      <div class="url">${lastResult.url || ''}</div>
    </div>
  `;
});
