import os
import json
import math
import logging
import re
import cv2 
from rapidfuzz import process, fuzz
from PIL import Image

logger = logging.getLogger(__name__)

def load_captions(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_words_from_captions(captions):
    """
    Extracts all unique words from captions for auto-complete.
    Returns a sorted list of unique words (lowercased).
    """
    words = set()
    for caption in captions.values():
        # Extract words (letters only, ignore punctuation)
        caption_words = re.findall(r'\b[a-zA-Z]+\b', caption.lower())
        words.update(caption_words)
    
    # Filter out very short words
    words = {w for w in words if len(w) > 2}
    
    return sorted(words)

def search_scenes(query, captions, threshold=60):
    """
    Searches for the query in the captions using RapidFuzz.
    Returns a list of matching filenames.
    """
    results = []
    
    logger.info("🔎 Searching for '%s' (Threshold: %s)...", query, threshold)
    
    # Iterate over every scene and its caption
    for filename, caption in captions.items():

        score = fuzz.partial_ratio(query.lower(), caption.lower())
        #TODO: play with threshold to see if it can be improved
        if score >= threshold:
            results.append(filename)

            
    return results

def create_collage(image_filenames, scenes_dir, output_path):
    """
    Takes a list of image filenames, opens them, and stitches them into a single grid collage.
    """
    if not image_filenames:
        logger.warning("⚠️ No images found for collage.")
        return

    # 1. Open all images
    images = []
    for fname in image_filenames:
        path = os.path.join(scenes_dir, fname)
        try:
            img = Image.open(path)
            # Resize for consistency (optional but recommended for clean grids)
            img = img.resize((300, 200)) 
            images.append(img)
        except Exception as e:
            print(f"Error loading {fname}: {e}")

    if not images:
        return

    # 2. Calculate Grid Dimensions
    count = len(images)
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)
    
    w, h = images[0].size
    collage_w = cols * w
    collage_h = rows * h
    
    # 3. Create Canvas
    collage = Image.new('RGB', (collage_w, collage_h), 'white')
    
    # 4. Paste Images
    for i, img in enumerate(images):
        x = (i % cols) * w
        y = (i // cols) * h
        collage.paste(img, (x, y))
    
    # 5. Save and Show
    collage.save(output_path)
    print(f"🖼️  Collage saved to {output_path}")
    
    # Open the image automatically (works on Mac)
    try:
        os.system(f"open {output_path}") 
    except Exception as e:
        logger.error("Error opening collage: %s", e)


def extract_frames_from_timestamps(video_path, events, output_dir):
    """
    Takes a list of event dicts [{'timestamp': '01:23', ...}],
    extracts the specific frame from the video, and saves it.
    Returns list of saved filenames for the collage.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    saved_files = []
 
    # pylint: disable=no-member
    cap = cv2.VideoCapture(video_path)
    
    # Get Frames Per Second (FPS) to calculate frame number
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    logger.info("📸 Extracting frames based on Gemini timestamps...")
    
    for i, event in enumerate(events):
        ts_str = event['timestamp']
        
        try:
            # Convert "MM:SS" -> Seconds -> Frame Number
            parts = ts_str.split(':')
            if len(parts) == 2:
                seconds = int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3: # HH:MM:SS
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                seconds = int(parts[0]) # Assume raw seconds if no colon

            frame_num = int(seconds * fps)
            
            # Jump to frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if ret:
                filename = f"gemini_match_{i}.jpg"
                path = os.path.join(output_dir, filename)
                cv2.imwrite(path, frame)
                saved_files.append(filename)
                
        except ValueError:
            print(f"   Skipping invalid timestamp: {ts_str}")

    cap.release()
    return saved_files

