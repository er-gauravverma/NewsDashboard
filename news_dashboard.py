"""
News Dashboard - Web app with thumbnail cards for news articles.

Usage:
    python news_dashboard.py
    Then open http://localhost:5050 in your browser.

Requirements:
    pip install flask requests beautifulsoup4 duckduckgo_search
"""

import re
import traceback
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_og_image(url: str) -> str | None:
    """Try to fetch the Open Graph image (thumbnail) from an article URL."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Try og:image first
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        # Try twitter:image
        tw = soup.find("meta", attrs={"name": "twitter:image"})
        if tw and tw.get("content"):
            return tw["content"]

        # Try first large image in the page
        for img in soup.find_all("img", src=True):
            src = img["src"]
            width = img.get("width", "")
            if (width and int(width) >= 200) or "hero" in src or "thumbnail" in src or "featured" in src:
                return urljoin(url, src)

    except Exception:
        pass
    return None


def search_news(keyword: str, source: str | None, limit: int) -> list[dict]:
    """Search news via DuckDuckGo."""
    query = keyword
    if source:
        query = f"{keyword} site:{source}"

    results = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.news(query, max_results=limit):
                results.append({
                    "title": item.get("title", "(no title)"),
                    "url": item.get("url", ""),
                    "date": item.get("date", ""),
                    "source": item.get("source", ""),
                    "body": item.get("body", ""),
                    "image": item.get("image", ""),
                })
    except Exception as e:
        print(f"News search error: {e}")
        traceback.print_exc()

    if not results:
        try:
            with DDGS() as ddgs:
                for item in ddgs.text(query + " latest news", max_results=limit):
                    results.append({
                        "title": item.get("title", "(no title)"),
                        "url": item.get("href", ""),
                        "date": "",
                        "source": "",
                        "body": item.get("body", ""),
                        "image": "",
                    })
        except Exception as e:
            print(f"Web search error: {e}")

    return results


# ── API endpoint ──────────────────────────────────────────────────────────────

@app.route("/api/search")
def api_search():
    keyword = request.args.get("keyword", "").strip()
    source = request.args.get("source", "").strip() or None
    limit = min(int(request.args.get("limit", 20)), 40)
    fetch_thumbs = request.args.get("thumbs", "0") == "1"

    if not keyword:
        return jsonify({"error": "keyword is required"}), 400

    results = search_news(keyword, source, limit)

    # For articles missing images, try fetching og:image from first few
    if fetch_thumbs:
        for item in results[:6]:
            if not item["image"]:
                img = fetch_og_image(item["url"])
                if img:
                    item["image"] = img

    return jsonify({"keyword": keyword, "source": source, "count": len(results), "results": results})


# ── Dashboard HTML ────────────────────────────────────────────────────────────

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>News Dashboard</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #242735;
    --border: #2e3247;
    --text: #e4e6f0;
    --text2: #9195a5;
    --accent: #6c8cff;
    --accent2: #4a6aef;
    --red: #ff6b6b;
    --green: #51cf66;
    --orange: #ffa94d;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }

  /* ── Header ── */
  .header {
    background: linear-gradient(135deg, #1a1d27 0%, #242735 100%);
    border-bottom: 1px solid var(--border);
    padding: 20px 0;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(10px);
  }

  .header-inner {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .header-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .header h1 {
    font-size: 22px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .header h1 .icon {
    width: 32px; height: 32px;
    background: var(--accent);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
  }

  .settings-btn {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px 16px;
    color: var(--text2);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .settings-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
  }

  /* ── Search Bar ── */
  .search-row {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  .search-row input, .search-row select {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 16px;
    color: var(--text);
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
  }

  .search-row input:focus, .search-row select:focus {
    border-color: var(--accent);
  }

  #keyword-input {
    flex: 1;
    min-width: 200px;
  }

  #source-select {
    width: 220px;
    cursor: pointer;
  }

  #limit-select {
    width: 90px;
    cursor: pointer;
  }

  .search-row select option {
    background: var(--surface);
  }

  .btn {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
    border: none;
    border-radius: 10px;
    padding: 12px 28px;
    color: #fff;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s;
    white-space: nowrap;
  }

  .btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(108, 140, 255, 0.3);
  }

  .btn:active { transform: scale(0.97); }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .btn-thumbs {
    background: linear-gradient(135deg, #444 0%, #555 100%);
    padding: 12px 16px;
    font-size: 13px;
  }

  .btn-thumbs.active {
    background: linear-gradient(135deg, var(--green) 0%, #3aaa55 100%);
  }

  /* ── Quick tags ── */
  .quick-tags {
    display: flex;
    gap: 8px;
    margin-top: 12px;
    flex-wrap: wrap;
  }

  .tag {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 12px;
    color: var(--text2);
    cursor: pointer;
    transition: all 0.2s;
  }

  .tag:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: rgba(108, 140, 255, 0.08);
  }

  /* ── Status ── */
  .status-bar {
    max-width: 1400px;
    margin: 16px auto 0;
    padding: 0 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 30px;
  }

  .status-text {
    font-size: 13px;
    color: var(--text2);
  }

  .spinner {
    width: 18px; height: 18px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Cards Grid ── */
  .grid {
    max-width: 1400px;
    margin: 8px auto 40px;
    padding: 0 24px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    cursor: pointer;
    display: flex;
    flex-direction: column;
  }

  .card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.4);
    border-color: var(--accent);
  }

  .card-img-wrap {
    width: 100%;
    height: 190px;
    background: var(--surface2);
    overflow: hidden;
    position: relative;
  }

  .card-img-wrap img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
  }

  .card:hover .card-img-wrap img {
    transform: scale(1.05);
  }

  .card-img-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 48px;
    color: var(--border);
    background: linear-gradient(135deg, var(--surface2) 0%, var(--surface) 100%);
  }

  .card-body {
    padding: 16px;
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .card-source {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--accent);
    margin-bottom: 8px;
  }

  .card-title {
    font-size: 15px;
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: 8px;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .card-snippet {
    font-size: 13px;
    color: var(--text2);
    line-height: 1.5;
    flex: 1;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .card-footer {
    padding: 12px 16px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: var(--text2);
  }

  .card-date {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .card-link {
    color: var(--accent);
    font-weight: 500;
    text-decoration: none;
  }

  /* ── Empty State ── */
  .empty-state {
    max-width: 1400px;
    margin: 80px auto;
    text-align: center;
    padding: 0 24px;
  }

  .empty-state .icon { font-size: 64px; margin-bottom: 16px; }
  .empty-state h2 { font-size: 20px; margin-bottom: 8px; color: var(--text); }
  .empty-state p { color: var(--text2); font-size: 14px; }

  /* ── Settings Modal ── */
  .modal-overlay {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    z-index: 1000;
    backdrop-filter: blur(4px);
    align-items: center;
    justify-content: center;
  }

  .modal-overlay.open {
    display: flex;
  }

  .modal {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    width: 520px;
    max-width: 90vw;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border);
  }

  .modal-header h2 {
    font-size: 18px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .modal-close {
    background: none;
    border: none;
    color: var(--text2);
    font-size: 24px;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 8px;
    transition: all 0.2s;
  }

  .modal-close:hover {
    background: var(--surface2);
    color: var(--text);
  }

  .modal-body {
    padding: 24px;
  }

  .modal-section {
    margin-bottom: 24px;
  }

  .modal-section:last-child {
    margin-bottom: 0;
  }

  .modal-section h3 {
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text2);
    margin-bottom: 12px;
  }

  .source-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .source-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
  }

  .source-item .source-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .source-item .source-name {
    font-size: 14px;
    font-weight: 500;
  }

  .source-item .source-domain {
    font-size: 12px;
    color: var(--text2);
  }

  .source-item .source-badge {
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 10px;
    background: var(--accent);
    color: #fff;
    font-weight: 600;
  }

  .source-item .source-badge.custom {
    background: var(--orange);
  }

  .source-item .remove-btn {
    background: none;
    border: none;
    color: var(--text2);
    font-size: 18px;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 6px;
    transition: all 0.2s;
  }

  .source-item .remove-btn:hover {
    background: rgba(255, 107, 107, 0.15);
    color: var(--red);
  }

  .add-source-row {
    display: flex;
    gap: 8px;
    margin-top: 12px;
  }

  .add-source-row input {
    flex: 1;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    color: var(--text);
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
  }

  .add-source-row input:focus {
    border-color: var(--accent);
  }

  .btn-add {
    background: linear-gradient(135deg, var(--green) 0%, #3aaa55 100%);
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    color: #fff;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.15s;
    white-space: nowrap;
  }

  .btn-add:hover {
    transform: translateY(-1px);
  }

  .modal-footer {
    padding: 16px 24px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }

  .btn-secondary {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 20px;
    color: var(--text);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-secondary:hover {
    border-color: var(--accent);
  }

  /* ── Responsive ── */
  @media (max-width: 600px) {
    .grid { grid-template-columns: 1fr; }
    .search-row { flex-direction: column; }
    #source-select, #limit-select { width: 100%; }
  }
</style>
</head>
<body>

<div class="header">
  <div class="header-inner">
    <div class="header-top">
      <h1><span class="icon">N</span> News Dashboard</h1>
      <button class="settings-btn" onclick="openSettings()">&#9881; Sources Settings</button>
    </div>
    <form class="search-row" id="search-form" onsubmit="return doSearch(event)">
      <input type="text" id="keyword-input" placeholder="Search keyword... e.g. Crude Oil, Gold, Bitcoin" autofocus>
      <select id="source-select" title="Select news source">
        <!-- Populated by JavaScript -->
      </select>
      <select id="limit-select" title="Number of results">
        <option value="10">10</option>
        <option value="20" selected>20</option>
        <option value="30">30</option>
        <option value="40">40</option>
      </select>
      <button class="btn btn-thumbs" id="thumb-btn" type="button" onclick="toggleThumbs()" title="Fetch thumbnails (slower)">Thumbnails</button>
      <button class="btn" type="submit" id="search-btn">Search</button>
    </form>
    <div class="quick-tags">
      <span class="tag" onclick="quickSearch('Crude Oil')">Crude Oil</span>
      <span class="tag" onclick="quickSearch('Gold Price')">Gold Price</span>
      <span class="tag" onclick="quickSearch('Bitcoin')">Bitcoin</span>
      <span class="tag" onclick="quickSearch('Nifty 50')">Nifty 50</span>
      <span class="tag" onclick="quickSearch('S&P 500')">S&P 500</span>
      <span class="tag" onclick="quickSearch('Forex EUR USD')">EUR/USD</span>
      <span class="tag" onclick="quickSearch('Natural Gas')">Natural Gas</span>
      <span class="tag" onclick="quickSearch('Silver Price')">Silver</span>
    </div>
  </div>
</div>

<div class="status-bar" id="status-bar"></div>

<div id="content">
  <div class="empty-state">
    <div class="icon">&#9201;</div>
    <h2>Loading Business News...</h2>
    <p>Fetching the latest headlines for you.</p>
  </div>
</div>

<!-- ── Settings Modal ── -->
<div class="modal-overlay" id="settings-modal">
  <div class="modal">
    <div class="modal-header">
      <h2>&#9881; News Sources</h2>
      <button class="modal-close" onclick="closeSettings()">&times;</button>
    </div>
    <div class="modal-body">
      <div class="modal-section">
        <h3>Configured Sources</h3>
        <div class="source-list" id="source-list">
          <!-- Populated by JavaScript -->
        </div>
      </div>
      <div class="modal-section">
        <h3>Add Custom Source</h3>
        <div class="add-source-row">
          <input type="text" id="new-source-name" placeholder="Display name (e.g. Bloomberg)">
          <input type="text" id="new-source-domain" placeholder="Domain (e.g. bloomberg.com)">
          <button class="btn-add" onclick="addCustomSource()">+ Add</button>
        </div>
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn-secondary" onclick="resetSources()">Reset to Defaults</button>
      <button class="btn" onclick="closeSettings()">Done</button>
    </div>
  </div>
</div>

<script>
// ── Default preset sources ──
const DEFAULT_SOURCES = [
  { name: 'All Sources',      domain: '',                  preset: true },
  { name: 'Yahoo Finance',    domain: 'finance.yahoo.com', preset: true },
  { name: 'Investing.com',    domain: 'investing.com',     preset: true },
  { name: 'MarketWatch',      domain: 'marketwatch.com',   preset: true },
  { name: 'Reuters',          domain: 'reuters.com',       preset: true },
  { name: 'CNBC',             domain: 'cnbc.com',          preset: true },
  { name: 'Bloomberg',        domain: 'bloomberg.com',     preset: true },
  { name: 'Economic Times',   domain: 'economictimes.indiatimes.com', preset: true },
  { name: 'Moneycontrol',     domain: 'moneycontrol.com',  preset: true },
];

const STORAGE_KEY = 'newsDashboard_sources';

// ── Source management ──
function loadSources() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try { return JSON.parse(saved); } catch {}
  }
  return [...DEFAULT_SOURCES];
}

function saveSources(sources) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sources));
}

function getSources() {
  return loadSources();
}

function populateSourceDropdown() {
  const select = document.getElementById('source-select');
  const currentVal = select.value;
  select.innerHTML = '';
  const sources = getSources();
  sources.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.domain;
    opt.textContent = s.name + (s.domain ? ' (' + s.domain + ')' : '');
    select.appendChild(opt);
  });
  // Restore previous selection if it still exists
  if (currentVal && [...select.options].some(o => o.value === currentVal)) {
    select.value = currentVal;
  }
}

// ── Settings modal ──
function openSettings() {
  document.getElementById('settings-modal').classList.add('open');
  renderSourceList();
}

function closeSettings() {
  document.getElementById('settings-modal').classList.remove('open');
  populateSourceDropdown();
}

function renderSourceList() {
  const list = document.getElementById('source-list');
  const sources = getSources();
  list.innerHTML = '';

  sources.forEach((s, idx) => {
    if (!s.domain) return; // Skip "All Sources" from the list

    const item = document.createElement('div');
    item.className = 'source-item';

    const badgeClass = s.preset ? 'source-badge' : 'source-badge custom';
    const badgeText = s.preset ? 'Preset' : 'Custom';
    const removeHtml = !s.preset
      ? '<button class="remove-btn" onclick="removeSource(' + idx + ')" title="Remove source">&times;</button>'
      : '';

    item.innerHTML =
      '<div class="source-info">' +
        '<span class="source-name">' + escHtml(s.name) + '</span>' +
        '<span class="source-domain">' + escHtml(s.domain) + '</span>' +
      '</div>' +
      '<div style="display:flex;align-items:center;gap:8px">' +
        '<span class="' + badgeClass + '">' + badgeText + '</span>' +
        removeHtml +
      '</div>';

    list.appendChild(item);
  });
}

function addCustomSource() {
  const nameEl = document.getElementById('new-source-name');
  const domainEl = document.getElementById('new-source-domain');
  const name = nameEl.value.trim();
  let domain = domainEl.value.trim().toLowerCase();

  if (!name || !domain) {
    alert('Please enter both a name and a domain.');
    return;
  }

  // Clean domain
  domain = domain.replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/.*$/, '');

  const sources = getSources();

  // Check for duplicates
  if (sources.some(s => s.domain === domain)) {
    alert('This source already exists.');
    return;
  }

  sources.push({ name, domain, preset: false });
  saveSources(sources);
  renderSourceList();

  nameEl.value = '';
  domainEl.value = '';
}

function removeSource(idx) {
  const sources = getSources();
  if (idx >= 0 && idx < sources.length && !sources[idx].preset) {
    sources.splice(idx, 1);
    saveSources(sources);
    renderSourceList();
  }
}

function resetSources() {
  if (confirm('Reset all sources back to defaults? Custom sources will be removed.')) {
    saveSources([...DEFAULT_SOURCES]);
    renderSourceList();
    populateSourceDropdown();
  }
}

// ── Search ──
let fetchThumbs = false;

function toggleThumbs() {
  fetchThumbs = !fetchThumbs;
  const btn = document.getElementById('thumb-btn');
  btn.classList.toggle('active', fetchThumbs);
}

function quickSearch(kw) {
  document.getElementById('keyword-input').value = kw;
  doSearch();
}

function doSearch(e) {
  if (e) e.preventDefault();

  const keyword = document.getElementById('keyword-input').value.trim();
  if (!keyword) return false;

  const source = document.getElementById('source-select').value;
  const limit = document.getElementById('limit-select').value;
  const btn = document.getElementById('search-btn');

  btn.disabled = true;
  btn.textContent = 'Searching...';

  const sourceLabel = source ? document.getElementById('source-select').selectedOptions[0].textContent : '';
  document.getElementById('status-bar').innerHTML = '<div class="spinner"></div><span class="status-text">Searching for "' + escHtml(keyword) + '"' + (source ? ' on ' + escHtml(sourceLabel) : '') + '...</span>';
  document.getElementById('content').innerHTML = '';

  const params = new URLSearchParams({ keyword, limit });
  if (source) params.set('source', source);
  if (fetchThumbs) params.set('thumbs', '1');

  fetch('/api/search?' + params)
    .then(r => r.json())
    .then(data => {
      btn.disabled = false;
      btn.textContent = 'Search';

      if (data.error) {
        document.getElementById('status-bar').innerHTML = '<span class="status-text" style="color:var(--red)">' + escHtml(data.error) + '</span>';
        return;
      }

      const n = data.count;
      const srcTxt = data.source ? ' from <strong>' + escHtml(data.source) + '</strong>' : '';
      document.getElementById('status-bar').innerHTML =
        '<span class="status-text">' + n + ' result' + (n !== 1 ? 's' : '') + ' for "<strong>' + escHtml(data.keyword) + '</strong>"' + srcTxt + '</span>';

      if (n === 0) {
        document.getElementById('content').innerHTML =
          '<div class="empty-state"><div class="icon">&#128533;</div><h2>No Results</h2><p>Try a different keyword or change the source filter.</p></div>';
        return;
      }

      renderCards(data.results);
    })
    .catch(err => {
      btn.disabled = false;
      btn.textContent = 'Search';
      document.getElementById('status-bar').innerHTML = '<span class="status-text" style="color:var(--red)">Error: ' + escHtml(err.message) + '</span>';
    });

  return false;
}

const NEWS_ICONS = ['&#128240;', '&#128200;', '&#127758;', '&#128202;', '&#128176;', '&#128184;'];

function renderCards(results) {
  const grid = document.createElement('div');
  grid.className = 'grid';

  results.forEach((item, idx) => {
    const card = document.createElement('div');
    card.className = 'card';
    card.onclick = () => window.open(item.url, '_blank');

    const imgHtml = item.image
      ? '<img src="' + escAttr(item.image) + '" alt="" loading="lazy" onerror="this.parentElement.innerHTML=\'<div class=card-img-placeholder>' + NEWS_ICONS[idx % NEWS_ICONS.length] + '</div>\'">'
      : '<div class="card-img-placeholder">' + NEWS_ICONS[idx % NEWS_ICONS.length] + '</div>';

    const dateStr = item.date ? formatDate(item.date) : '';
    const domain = item.source || extractDomain(item.url);

    card.innerHTML =
      '<div class="card-img-wrap">' + imgHtml + '</div>' +
      '<div class="card-body">' +
        '<div class="card-source">' + escHtml(domain) + '</div>' +
        '<div class="card-title">' + escHtml(item.title) + '</div>' +
        '<div class="card-snippet">' + escHtml(item.body || '') + '</div>' +
      '</div>' +
      '<div class="card-footer">' +
        '<span class="card-date">' + escHtml(dateStr) + '</span>' +
        '<a class="card-link" href="' + escAttr(item.url) + '" target="_blank" onclick="event.stopPropagation()">Read more &rarr;</a>' +
      '</div>';

    grid.appendChild(card);
  });

  document.getElementById('content').innerHTML = '';
  document.getElementById('content').appendChild(grid);
}

function formatDate(d) {
  try {
    const dt = new Date(d);
    if (isNaN(dt)) return d.slice(0, 16);
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) +
           ' ' + dt.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  } catch { return d.slice(0, 16); }
}

function extractDomain(url) {
  try { return new URL(url).hostname.replace('www.', ''); }
  catch { return ''; }
}

function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function escAttr(s) {
  return s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ── Close modal on outside click ──
document.getElementById('settings-modal').addEventListener('click', function(e) {
  if (e.target === this) closeSettings();
});

// ── Close modal on Escape key ──
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeSettings();
});

// ── Initialize on load ──
window.addEventListener('DOMContentLoaded', function() {
  populateSourceDropdown();

  // Auto-search "Business News" on startup
  document.getElementById('keyword-input').value = 'Business News';
  doSearch();
});
</script>

</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5050))
    print(f"\n  News Dashboard running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("DEBUG", "false").lower() == "true")
