"""
Handles all video processing tasks
"""
import logging
import os
import json
import torch
from PIL import Image
from tqdm import tqdm
from transformers import AutoModelForCausalLM
from scenedetect import open_video, SceneManager, save_images
from scenedetect.detectors import ContentDetector

logger = logging.getLogger(__name__)

# Global model instance (loaded once, reused)
_moondream_model = None


def _get_moondream_model():
    """
    Lazily loads and returns the Moondream2 model.
    Uses MPS on Apple Silicon, CUDA on NVIDIA GPUs, or CPU as fallback.
    """
    global _moondream_model


    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        _moondream_model = AutoModelForCausalLM.from_pretrained(
                "vikhyatk/moondream2",
                revision="2025-06-21",
                trust_remote_code=True,
                device_map={"": "mps"}
            )
        
    logger.info("Moondream2 model loaded successfully.")
    
    return _moondream_model

def extract_scenes(video_path, output_dir, threshold=20.0):
    """
    Detects scenes in the video and saves frames from each scene as images.
    Uses PySceneDetect's built-in save_images for efficient extraction.
    Skips if the output directory already contains images.
    """
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Caching Check
    # If the folder has files, we assume extraction is done.
    existing_files = [f for f in os.listdir(output_dir) if f.endswith('.jpg')]
    if len(existing_files) > 10:  # Simple heuristic: if >10 images exist, we probably ran this already
        logger.info("Scenes already extracted in '%s'. Skipping.", output_dir)
        return

    logger.info("Detecting scenes in %s (Threshold: %s)...", video_path, threshold)

    # 2. Setup PySceneDetect
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=15))

    # 3. Detect Scenes
    scene_manager.detect_scenes(video, show_progress=True)
    scene_list = scene_manager.get_scene_list()
    
    logger.info("Found %d scenes. Saving images...", len(scene_list))

    # 4. Save Images using PySceneDetect's built-in function
    # num_images=1 saves the middle frame of each scene (most representative)
    # num_images=3 would save start, middle, and end frames
    save_images(
        scene_list=scene_list,
        video=video,
        num_images=1,
        output_dir=output_dir,
        image_name_template="scene_$SCENE_NUMBER",
        show_progress=True,
    )

    # 5. Resize images to max 512px and convert to JPEG to save compute
    logger.info("Resizing images to max 512px...")
    max_size = 512
    for img_file in os.listdir(output_dir):
        if not img_file.endswith('.jpg'):
            continue
        img_path = os.path.join(output_dir, img_file)
        with Image.open(img_path) as img:
            # Calculate new size maintaining aspect ratio
            width, height = img.size
            if max(width, height) > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * max_size / width)
                else:
                    new_height = max_size
                    new_width = int(width * max_size / height)
                img = img.resize((new_width, new_height), Image.LANCZOS)
            # Save as JPEG with quality=75 for smaller file size
            img.convert("RGB").save(img_path, "JPEG", quality=75)

    logger.info("Saved %d scene images to '%s'", len(scene_list), output_dir)



def generate_captions(scenes_dir, json_path):
    """
    Iterates over images in scenes_dir, generates captions using Moondream2,
    and saves a JSON mapping filename -> caption.
    """
    
    # 1. Caching Check
    if os.path.exists(json_path):
        logger.info("Captions file found at '%s'. Skipping AI generation.", json_path)
        return

    # Ensure scenes directory exists
    if not os.path.exists(scenes_dir):
        logger.error("Scenes directory '%s' does not exist. Run extract_scenes() first.", scenes_dir)
        raise FileNotFoundError(f"Scenes directory '{scenes_dir}' does not exist. Run extract_scenes() first.")

    # Get list of images
    image_files = sorted([f for f in os.listdir(scenes_dir) if f.endswith('.jpg')])

    # Load Moondream2 model
    model = _get_moondream_model()

    captions = {}
    logger.info("Generating captions for %d scenes using Moondream2...", len(image_files))

    
    # 2. Process with Progress Bar
    for img_file in tqdm(image_files, desc="AI Captioning"):
        img_full_path = os.path.join(scenes_dir, img_file)

        try:
            # Load image using PIL
            image = Image.open(img_full_path).convert("RGB")
            
            # Generate caption using Moondream2's built-in caption method
            result = model.caption(image, length="short")
            description = result["caption"].strip()
            captions[img_file] = description
            
        except Exception as e:
            logger.error("Error processing %s: %s", img_file, e)
            captions[img_file] = "Error generating caption."

    # 3. Save to JSON
    # Ensure parent directory exists
    json_dir = os.path.dirname(json_path)
    if json_dir and not os.path.exists(json_dir):
        os.makedirs(json_dir)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(captions, f, indent=4)
    
    logger.info("Captions saved to '%s'", json_path)