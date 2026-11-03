from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import yt_dlp

app = FastAPI()

# Web Sitesinin HTML Arayüzü (Mobil Uyumlu & Sade Tasarım)
html_content = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sosyal Medya İndirici</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .card { background: #1e293b; border-radius: 16px; padding: 32px; width: 100%; max-width: 480px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); text-align: center; }
        h1 { font-size: 1.5rem; margin-bottom: 24px; color: #38bdf8; }
        input { width: 100%; padding: 14px 16px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: #fff; font-size: 1rem; margin-bottom: 16px; outline: none; }
        input:focus { border-color: #38bdf8; }
        button { width: 100%; padding: 14px; border-radius: 8px; border: none; background: #0284c7; color: #fff; font-weight: bold; font-size: 1rem; cursor: pointer; transition: 0.2s; }
        button:hover { background: #0369a1; }
        #result { margin-top: 24px; text-align: left; }
        .thumbnail { width: 100%; border-radius: 8px; margin-bottom: 12px; }
        .video-title { font-size: 0.95rem; line-height: 1.4; margin-bottom: 16px; color: #cbd5e1; }
        .download-btn { display: block; text-align: center; background: #10b981; color: white; text-decoration: none; padding: 12px; border-radius: 8px; font-weight: bold; }
        .download-btn:hover { background: #059669; }
        .loading { display: none; color: #94a3b8; font-size: 0.9rem; margin-top: 16px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Video İndirici</h1>
        <input type="url" id="videoUrl" placeholder="Video bağlantısını buraya yapıştırın..." required>
        <button onclick="fetchVideo()">Bilgileri Getir</button>
        <div id="loading" class="loading">Video işleniyor, lütfen bekleyin...</div>
        <div id="result"></div>
    </div>

    <script>
        async function fetchVideo() {
            const urlInput = document.getElementById('videoUrl').value.trim();
            const resultDiv = document.getElementById('result');
            const loadingDiv = document.getElementById('loading');
            
            if(!urlInput) {
                alert('Lütfen geçerli bir bağlantı girin.');
                return;
            }

            resultDiv.innerHTML = '';
            loadingDiv.style.display = 'block';

            try {
                const response = await fetch(`/download?url=${encodeURIComponent(urlInput)}`);
                const data = await response.json();
                loadingDiv.style.display = 'none';

                if (data.success && data.download_url) {
                    resultDiv.innerHTML = `
                        <img class="thumbnail" src="${data.thumbnail}" alt="Kapak Resmi">
                        <div class="video-title">${data.title}</div>
                        <a class="download-btn" href="${data.download_url}" target="_blank" download>İndirmeyi Başlat</a>
                    `;
                } else {
                    resultDiv.innerHTML = `<p style="color: #ef4444;">Hata: ${data.detail || 'Video alınamadı.'}</p>`;
                }
            } catch (err) {
                loadingDiv.style.display = 'none';
                resultDiv.innerHTML = `<p style="color: #ef4444;">Sunucuya bağlanırken bir hata oluştu.</p>`;
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return html_content

@app.get("/download")
def get_video_info(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL parametresi gerekli.")
    
    try:
        ydl_opts = {
            'format': 'best',
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_url = info.get('url')
            if not video_url and 'formats' in info:
                video_url = info['formats'][-1].get('url')

            return {
                "success": True,
                "title": info.get('title', 'İsimsiz Video'),
                "thumbnail": info.get('thumbnail', ''),
                "download_url": video_url
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hata oluştu: {str(e)}")
