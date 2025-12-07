import logging
import os
from dotenv import load_dotenv
from src.downloader import download_video
from src.processor import extract_scenes, generate_captions
from src.search_engine import load_captions, search_scenes, create_collage, extract_words_from_captions, extract_frames_from_timestamps
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from src.cloud_search import search_video_for_timestamps

load_dotenv()  

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
    if not os.path.exists(video_path):
        video_path = download_video("super mario movie trailer", "video.mp4")
    
    if not video_path:
        logger.error("Critical Error: Could not obtain video. Exiting.")
        return

    # Ensure output directory exists
    if not os.path.exists("output"): 
        os.makedirs("output")


    while True:
        print("\nChoose Mode:")
        print("1. 🖼️  Local Visual Search (Moondream + RapidFuzz)")
        print("2. 🤖 Cloud Video Understanding (Gemini 2.5 Flash)")
        print("3. Exit")

        choice = input("Select: ").strip()

        if choice == '1':
            # Run the local pipeline if data is missing

            # Phase 1: Ingestion
            extract_scenes(video_path, scenes_dir, threshold=20.0)

            # Phase 2: Captioning
            generate_captions(scenes_dir, json_path)

            captions = load_captions(json_path)

            # Phase 3: Search Loop
            print("\n✅ System Ready.")
            search_loop(captions, scenes_dir, collage_path)

        elif choice == '2':
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                api_key = input("Enter your Gemini API Key: ").strip()

            query = input("What do you want to find in the video? ")

            # Phase 1: Get Timestamps from Cloud
            events = search_video_for_timestamps(api_key, video_path, query)

            if events:
                # 2. Extract Frames locally
                gemini_scenes_dir = os.path.join(assets_dir, "gemini_results")
                images = extract_frames_from_timestamps(video_path, events, gemini_scenes_dir)


            # 3. Create Collage
                if images:
                    create_collage(images, gemini_scenes_dir, collage_path)

        elif choice == '3':
            print("Goodbye!")
            break



    
  

   

if __name__ == "__main__":
    main()