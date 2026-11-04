from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from urllib.parse import quote
from urllib.request import Request, urlopen
import os
import re
import shutil
import time
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

html_content = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#14171c">
<title>Video İndirici</title>
<style>
  :root {
    --bg: #14171c;
    --surface: #1d2229;
    --line: #2d343e;
    --text: #eceff3;
    --muted: #9aa4b2;
    --accent: #ffc83d;
    --accent-ink: #1a1400;
    --error: #ff7a7a;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    padding: 40px 16px;
  }
  main { width: 100%; max-width: 460px; }
  h1 { font-size: 2rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; }
  .sub { color: var(--muted); margin: 10px 0 28px; line-height: 1.5; }

  .field { display: flex; gap: 8px; }
  input {
    flex: 1; min-width: 0;
    padding: 15px 16px;
    border-radius: 12px;
    border: 1px solid var(--line);
    background: var(--surface);
    color: var(--text);
    font-size: 1rem;
    outline: none;
  }
  input:focus-visible { border-color: var(--accent); }
  button { font: inherit; cursor: pointer; border: none; }
  button:focus-visible, a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .ghost {
    padding: 0 16px; border-radius: 12px;
    background: var(--surface); color: var(--text);
    border: 1px solid var(--line); font-weight: 600;
  }
  .primary {
    width: 100%; margin-top: 12px; padding: 15px;
    border-radius: 12px; background: var(--accent); color: var(--accent-ink);
    font-weight: 700; font-size: 1rem;
  }
  .primary:disabled { opacity: .6; cursor: wait; }

  .platforms { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 18px; }
  .platforms span {
    font-size: .8rem; color: var(--muted);
    border: 1px solid var(--line); border-radius: 999px; padding: 5px 11px;
  }

  #status { margin-top: 24px; }
  .loading { display: flex; align-items: center; gap: 10px; color: var(--muted); }
  .spinner {
    width: 18px; height: 18px; border-radius: 50%;
    border: 2px solid var(--line); border-top-color: var(--accent);
    animation: spin .8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  @media (prefers-reduced-motion: reduce) { .spinner { animation-duration: 2s; } }

  .error { color: var(--error); line-height: 1.5; word-break: break-word; }

  .result { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }
  .result img { display: block; width: 100%; max-height: 260px; object-fit: cover; background: #000; }
  .result .body { padding: 16px; }
  .title { font-size: .95rem; line-height: 1.45; color: var(--text); margin-bottom: 14px; word-break: break-word; }
  .download {
    display: block; text-align: center; text-decoration: none;
    background: var(--accent); color: var(--accent-ink);
    padding: 14px; border-radius: 10px; font-weight: 700;
  }
  .hint { margin-top: 10px; font-size: .8rem; color: var(--muted); line-height: 1.5; }
</style>
</head>
<body>
<main>
  <h1>Video İndirici</h1>
  <p class="sub">Bağlantıyı yapıştır, videoyu MP4 olarak indir.</p>

  <div class="field">
    <input type="url" id="videoUrl" placeholder="https://..." inputmode="url" autocomplete="off" autocapitalize="off" spellcheck="false">
    <button class="ghost" id="pasteBtn" type="button">Yapıştır</button>
  </div>
  <button class="primary" id="goBtn" type="button">Bilgileri Getir</button>

  <div class="platforms">
    <span>TikTok</span><span>YouTube</span><span>Instagram</span><span>X</span>
    <span>Facebook</span><span>Reddit</span><span>Pinterest</span><span>Vimeo</span>
  </div>

  <div id="status" aria-live="polite"></div>
</main>

<script>
  const input = document.getElementById('videoUrl');
  const goBtn = document.getElementById('goBtn');
  const pasteBtn = document.getElementById('pasteBtn');
  const status = document.getElementById('status');

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  pasteBtn.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) { input.value = text.trim(); input.focus(); }
    } catch (e) {
      input.focus();
      status.innerHTML = '<p class="error">Panoya erişilemedi. Bağlantıyı kutuya elle yapıştır.</p>';
    }
  });

  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') fetchVideo(); });
  goBtn.addEventListener('click', fetchVideo);

  async function fetchVideo() {
    const url = input.value.trim();
    if (!url) {
      status.innerHTML = '<p class="error">Önce bir video bağlantısı gir.</p>';
      return;
    }
    goBtn.disabled = true;
    status.innerHTML = '<div class="loading"><div class="spinner"></div><span>Video işleniyor, lütfen bekle...</span></div>';

    try {
      const res = await fetch('/download?url=' + encodeURIComponent(url));
      const data = await res.json();

      if (data.success && data.download_url) {
        const thumb = data.thumbnail
          ? '<img src="' + esc(data.thumbnail) + '" alt="" referrerpolicy="no-referrer" onerror="this.remove()">'
          : '';
        status.innerHTML =
          '<div class="result">' + thumb +
          '<div class="body">' +
          '<div class="title">' + esc(data.title) + '</div>' +
          '<a class="download" href="' + esc(data.download_url) + '" download>Videoyu İndir</a>' +
          '<p class="hint">Butona basınca video doğrudan cihazına iner.</p>' +
          '</div></div>';
      } else {
        status.innerHTML = '<p class="error">' + esc(data.detail || 'Video alınamadı. Bağlantıyı kontrol edip tekrar dene.') + '</p>';
      }
    } catch (err) {
      status.innerHTML = '<p class="error">Sunucuya bağlanılamadı. Birkaç saniye sonra tekrar dene.</p>';
    } finally {
      goBtn.disabled = false;
    }
  }
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def read_root():
    return html_content


_cache = {}
CACHE_TTL = 600  # saniye

YDL_OPTS = {
    "format": "b[ext=mp4]/b/bv*",
    "skip_download": True,
}

# Render "Secret Files" ile eklenen cookies.txt varsa kullan.
# Dosya salt okunur klasörde durduğu için önce /tmp'ye kopyalanır.
for _src in ("/etc/secrets/cookies.txt", "cookies.txt"):
    if os.path.exists(_src):
        shutil.copy(_src, "/tmp/cookies.txt")
        YDL_OPTS["cookiefile"] = "/tmp/cookies.txt"
        break


def extract(url: str):
    now = time.time()
    for k in [k for k, (t, _) in _cache.items() if now - t > CACHE_TTL]:
        _cache.pop(k, None)
    if url in _cache:
        return _cache[url][1]

    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)

    # Bazi baglantilar (coklu gonderi vb.) "entries" icinde gelir
    if "entries" in info and info["entries"]:
        info = info["entries"][0]

    video_url = info.get("url")
    if not video_url and info.get("formats"):
        video_url = info["formats"][-1].get("url")
    if not video_url:
        raise HTTPException(status_code=404, detail="Bu bağlantıdan indirilebilir video bulunamadı.")

    headers = {
        k: v for k, v in (info.get("http_headers") or {}).items()
        if k.lower() != "accept-encoding"
    }
    data = {
        "title": info.get("title", "İsimsiz Video"),
        "thumbnail": info.get("thumbnail", ""),
        "video_url": video_url,
        "headers": headers,
        "ext": info.get("ext") or "mp4",
    }
    _cache[url] = (now, data)
    return data


@app.get("/download")
def get_video_info(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL parametresi gerekli.")
    try:
        data = extract(url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hata oluştu: {str(e)}")

    return {
        "success": True,
        "title": data["title"],
        "thumbnail": data["thumbnail"],
        "download_url": "/file?url=" + quote(url, safe=""),
    }


@app.get("/file")
def download_file(url: str):
    try:
        data = extract(url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hata oluştu: {str(e)}")

    try:
        upstream = urlopen(Request(data["video_url"], headers=data["headers"]), timeout=30)
    except Exception:
        # Sunucu videoyu çekemezse eski yönteme dön: doğrudan video bağlantısını aç
        return RedirectResponse(data["video_url"], status_code=307)

    ext = data["ext"]
    safe_title = re.sub(r'[\\/:*?"<>|\r\n]+', " ", data["title"]).strip()[:80] or "video"
    filename = f"{safe_title}.{ext}"
    headers = {
        "Content-Disposition": f"attachment; filename=\"video.{ext}\"; filename*=UTF-8''{quote(filename)}"
    }
    length = upstream.headers.get("Content-Length")
    if length:
        headers["Content-Length"] = length

    def stream():
        try:
            while True:
                chunk = upstream.read(65536)
                if not chunk:
                    break
                yield chunk
        finally:
            upstream.close()

    return StreamingResponse(stream(), media_type=f"video/{ext}", headers=headers)
