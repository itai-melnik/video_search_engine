import os
import json
import math
import logging
from rapidfuzz import process, fuzz
from PIL import Image

logger = logging.getLogger(__name__)

def load_captions(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

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
    except:
        pass

