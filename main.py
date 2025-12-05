import logging
import os
from src.downloader import download_video
from src.processor import extract_scenes, generate_captions
from src.search_engine import load_captions, search_scenes, create_collage, extract_words_from_captions
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

logger = logging.getLogger(__name__)


def search_loop(captions, scenes_dir, collage_path):
    """
    Interactive search loop with auto-complete suggestions from captions.
    """
    # Build word list for auto-complete from captions
    words = extract_words_from_captions(captions)
    completer = WordCompleter(words, ignore_case=True)
    
    while True:
        try:
            query = prompt("\nSearch the video using a word (or 'exit'): ", completer=completer).strip()
            
            if query.lower() == 'exit':
                print("Goodbye!")
                break
            
            if not query:
                continue

            # 1. Search
            matches = search_scenes(query, captions, threshold=65)
            print(f"Found {len(matches)} scenes matching '{query}'.")

            # 2. Collage
            if matches:
                create_collage(matches, scenes_dir, collage_path)
            else:
                print("Try a different word.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break


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
    collage_path = os.path.join(assets_dir, "collage.png")


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


    # Phase 4: Search Loop
    print("\n✅ System Ready.")
    captions = load_captions(json_path)
    search_loop(captions, scenes_dir, collage_path)

   

if __name__ == "__main__":
    main()