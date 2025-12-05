"""
Handles all video processing tasks
"""
import logging
import os
from scenedetect import open_video, SceneManager, save_images
from scenedetect.detectors import ContentDetector

logger = logging.getLogger(__name__)

def extract_scenes(video_path, output_dir, threshold=27.0):
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
    scene_manager.add_detector(ContentDetector(threshold=threshold))

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

    logger.info("Saved %d scene images to '%s'", len(scene_list), output_dir)