import logging
import os
from src.downloader import download_video
from src.processor import extract_scenes, generate_captions


logger = logging.getLogger(__name__)

def main():

    #logger config:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


    # Paths
    assets_dir = "assets"
    scenes_dir = os.path.join(assets_dir, "scenes") 
    video_path = os.path.join(assets_dir, "video.mp4")
    json_path = os.path.join(assets_dir, "scene_captions.json")

    print("--- Video Search Engine ---")
    
    # Phase 1: Ingestion
    video_path = download_video("super mario movie trailer", "video.mp4")
    
    if not video_path:
        logger.error("Critical Error: Could not obtain video. Exiting.")
        return

    # Phase 2: Scene Detection
    extract_scenes(video_path, scenes_dir, threshold=20.0)


    # Phase 3: AI Captioning (Moondream)
    generate_captions(scenes_dir, json_path)

   

if __name__ == "__main__":
    main()