from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Sosyal Medya İndirici API çalışıyor!"}

@app.get("/download")
def get_video_info(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL parametresi gerekli.")
    
    try:
        # yt-dlp ayarları (videoyu indirmeden sadece linki ve bilgileri çekmek için)
        ydl_opts = {
            'format': 'best',
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Doğrudan video veya format bağlantısını alıyoruz
            video_url = info.get('url')
            if not video_url and 'formats' in info:
                # Eğer doğrudan url yoksa en iyi formatın linkini seç
                video_url = info['formats'][-1].get('url')

            return {
                "success": True,
                "title": info.get('title', 'İsimsiz Video'),
                "thumbnail": info.get('thumbnail', ''),
                "download_url": video_url
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hata oluştu: {str(e)}")