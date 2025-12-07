import os
import time
import json
import logging
from google import genai
from google.genai import types

#TODO: change to logging using lazy formatting
logger = logging.getLogger(__name__)

def upload_video(client, video_path):
    """
    Checks if video is already uploaded before uploading.
    Reuses existing file reference if available (within 48-hour window file api limits).
    """
    # Extract filename to use as identifier
    video_filename = os.path.basename(video_path)
    
    # Check existing files on Gemini
    logger.info("🔍 Checking if '%s' is already uploaded...", video_filename)
    try:
        for file in client.files.list():
            if file.display_name == video_filename and file.state == "ACTIVE":
                logger.info("✅ Found existing upload: %s (reusing cached file)", file.name)
                return file
    except Exception as e:
        logger.warning("⚠️  Could not check existing files: %s. Proceeding with upload.", e)
    
    # Not found or error, proceed with upload
    logger.info("☁️  Uploading '%s' to Gemini...", video_path)
    try:
        video_file = client.files.upload(
            file=video_path,
            config={'display_name': video_filename}
        )
        logger.info("   Upload complete: %s", video_file.name)
    except Exception as e:
        logger.error("❌ Upload failed: %s", e)
        return None

    # Poll for processing
    logger.info("   Waiting for processing...")
    while True:
        file_status = client.files.get(name=video_file.name)
        if file_status.state == "ACTIVE":
            logger.info("✅ Video is ready!")
            return video_file
        elif file_status.state == "FAILED":
            logger.error("❌ Processing failed.")
            return None
        
        print(".", end="", flush=True)
        time.sleep(3)

def search_video_for_timestamps(api_key, video_path, user_query):
    """
    1. Uploads video.
    2. Asks Gemini to find events matching the query.
    3. Enforces a JSON output containing timestamps.
    """
    client = genai.Client(api_key=api_key)
    
    video_file = upload_video(client, video_path)
    if not video_file:
        return []

    logger.info("🔎 Asking Gemini 2.5 Flash to find: '%s'...", user_query)

    # --- THE MAGIC: Structured Output Schema ---
    # We force the model to respond ONLY in this JSON format.
    # This guarantees we get fields we can parse programmatically.
    schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "timestamp": {"type": "STRING", "description": "The timestamp of the event in MM:SS format"},
                "description": {"type": "STRING", "description": "A short description of what is visible"}
            },
            "required": ["timestamp", "description"]
        }
    }

    prompt = f"""
    Look for scenes in the video that match this search: "{user_query}".
    Return a list of exact timestamps (MM:SS) where these events happen.
    Be precise.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # Using the model you requested
            contents=[video_file, prompt],
            config={
                "response_mime_type": "application/json",
                "response_schema": schema
            }
        )
        
        # Parse the JSON string result into a Python list
        events = json.loads(response.text)
        logger.info("✅ Found %s matching events.", len(events))
        return events

    except Exception as e:
        logger.error("❌ Gemini Error: %s", e)
        return []