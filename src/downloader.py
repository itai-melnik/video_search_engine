"""
yt-dlp wrapper for downloading videos from YouTube.
"""
import logging
import os

import yt_dlp

logger = logging.getLogger(__name__)

def download_video(search_query, output_filename):
    """
    Searches for a video on YouTube and downloads it (video only, no audio).
    Skips download if the file already exists.
    """
    
    # Ensure assets directory exists
    assets_dir = "assets"
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)

    output_path = os.path.join(assets_dir, output_filename)

    # 1. Caching Check
    if os.path.exists(output_path):
        logger.info("Video found at '%s'. Skipping download.", output_path)
        return output_path

    logger.info("Downloading '%s'...", search_query)

    # 2. yt-dlp Configuration
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]',  # Video only, MP4 format
        'outtmpl': output_path,          # Save to specific path
        'noplaylist': True,              # Download single video, not playlist
        'default_search': 'ytsearch',    # Allow searching by string
        'quiet': True,                   # Reduce terminal noise
        'no_warnings': True
    }

    # 3. Execute Download
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # The 'ytsearch1:' prefix tells it to pick the first result for the query
            ydl.download([f"ytsearch1:{search_query}"])
        logger.info("Download complete: %s", output_path)
        return output_path
    except Exception as e:
        logger.error("Error downloading video: %s", e)
        return None