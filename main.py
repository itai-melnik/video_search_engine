import logging
import os
from src.downloader import download_video
from src.processor import extract_scenes


logger = logging.getLogger(__name__)

def main():

    #logger config:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("--- Video Search Engine ---")
    
    # Phase 1: Ingestion
    video_path = download_video("super mario movie trailer", "video.mp4")
    
    if not video_path:
        logger.error("Critical Error: Could not obtain video. Exiting.")
        return

    # Phase 2: Scene Detection
    # We save scenes to assets/scenes
    scenes_dir = os.path.join("assets", "scenes")
    extract_scenes(video_path, scenes_dir, threshold=26.0)

   

if __name__ == "__main__":
    main()