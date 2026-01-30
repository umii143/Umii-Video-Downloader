from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from yt_dlp import YoutubeDL
import requests
import urllib.parse
import os

app = FastAPI()

# Vercel handles CORS at the edge usually, but we keep this for safety
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_video_info(url: str):
    # Important: Vercel file system is read-only. 
    # We must set cache_dir to /tmp or disable it.
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'outtmpl': '%(title)s.%(ext)s',
        'cache_dir': '/tmp/yt-dlp-cache',
        'noplaylist': True,
    }
    
    try:
        # Create cache dir if it doesn't exist (Vercel /tmp is writable)
        os.makedirs('/tmp/yt-dlp-cache', exist_ok=True)
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return {
                "id": info.get('id'),
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "platform": info.get('extractor_key'),
                "download_url": info.get('url'),
                "ext": info.get('ext', 'mp4')
            }
    except Exception as e:
        print(f"Error extracting info: {e}")
        return None

@app.get("/api/info")
async def info(url: str = Query(..., description="The URL of the video to process")):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    data = get_video_info(url)
    if not data:
        raise HTTPException(status_code=400, detail="Could not extract video info. Link might be private or invalid.")
    
    return data

@app.get("/api/download")
async def download(
    url: str = Query(..., description="The direct video URL from yt-dlp"), 
    title: str = Query("video", description="Filename for the download"),
    ext: str = Query("mp4", description="File extension")
):
    try:
        # Note: Vercel Serverless functions have a 10s timeout on the free tier.
        # Large downloads might fail. A redirect (302) is often better for Vercel,
        # but CORS might block it on the client side. 
        # For this MVP, we attempt a stream.
        r = requests.get(url, stream=True)
        r.raise_for_status()
        
        safe_filename = urllib.parse.quote(f"{title}.{ext}")
        
        return StreamingResponse(
            r.iter_content(chunk_size=8192),
            media_type=r.headers.get("Content-Type", "video/mp4"),
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
