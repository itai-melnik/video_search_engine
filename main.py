import logging
from src.downloader import download_video


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

   

if __name__ == "__main__":
    main()