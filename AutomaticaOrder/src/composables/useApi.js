export function getApiBase() {
  try {
    return (window.API_BASE_URL || 'https://api.wen-xc.site').replace(/\/$/, '');
  } catch {
    return 'https://api.wen-xc.site';
  }
}

export async function apiGet(path) {
  const base = getApiBase();
  const resp = await fetch(`${base}${path}`, { credentials: 'include' });
  if (!resp.ok) {
    let t = `请求失败 ${resp.status}`;
    try { const j = await resp.json(); if (j && j.detail) t = j.detail; } catch {}
    throw new Error(t);
  }
  return resp.json();
}

