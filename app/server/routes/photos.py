from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
import os
import time
import shutil
import logging
from PIL import Image

logger = logging.getLogger(__name__)

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
THUMBS_DIR = os.path.join(DATA_DIR, "thumbnails")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(THUMBS_DIR, exist_ok=True)

@router.post("/upload")
async def upload_photos(
    request: Request,
    files: list[UploadFile] = File(...),
    pre_processed: bool = Form(False)
):
    results = []
    
    for file in files:
        if not file.filename:
            continue
            
        timestamp = int(time.time() * 1000)
        # Ensure safe extension
        ext = os.path.splitext(file.filename)[1]
        safe_filename = f"{timestamp}{ext}"
        
        target_dir = PROCESSED_DIR if pre_processed else IMAGES_DIR
        file_path = os.path.join(target_dir, safe_filename)
        
        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
                
            # Generate thumbnail
            img = Image.open(file_path)
            img.thumbnail((200, 120))
            thumb_filename = f"thumb_{timestamp}.png"
            thumb_path = os.path.join(THUMBS_DIR, thumb_filename)
            # Make sure it's RGB for JPEG save or save as PNG
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(thumb_path, "PNG")
            
            results.append({
                "id": str(timestamp),
                "filename": safe_filename,
                "thumbnail_url": f"/api/photos/{thumb_filename}/thumbnail"
            })
            
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {e}")
            results.append({"filename": file.filename, "error": str(e)})

    return {"photos": results}
