// Set your backend API base URL here. For GitHub Pages, this must be the public domain of your API server
// Example: https://api.example.com
window.API_BASE_URL = "https://47.108.186.39"; // Tornado backend base URL (using IP)

// Status definitions must align with backend
window.STATUSES = [
  "打包发出",
  "在我国海岸等待检查",
  "已发往俄罗斯",
  "等待俄罗斯关口检查",
  "转运到彼得堡（1-3天）",
  "已到达彼得堡",
  "已结算",
];

// Enforce HTTPS for API when page is served over HTTPS
try {
  if (location.protocol === 'https:' && /^http:\/\//i.test(window.API_BASE_URL)) {
    // Auto-upgrade protocol to https for the same host, or if backend supports https
    const api = new URL(window.API_BASE_URL, location.href);
    api.protocol = 'https:';
    window.API_BASE_URL = api.toString().replace(/\/$/, '');
    console.warn('[config] API_BASE_URL auto-upgraded to HTTPS:', window.API_BASE_URL);
  }
} catch (_) {}
