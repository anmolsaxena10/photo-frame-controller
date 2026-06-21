from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
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


@router.get("")
async def list_photos():
    """List all uploaded photos with their thumbnails."""
    photos = []
    
    if os.path.exists(PROCESSED_DIR):
        files = sorted(os.listdir(PROCESSED_DIR), reverse=True)
        for filename in files:
            if not filename.endswith(('.png', '.jpg', '.jpeg')):
                continue
            # Extract timestamp ID from filename
            photo_id = os.path.splitext(filename)[0]
            thumb_filename = f"thumb_{photo_id}.png"
            thumb_exists = os.path.exists(os.path.join(THUMBS_DIR, thumb_filename))
            
            photos.append({
                "id": photo_id,
                "filename": filename,
                "thumbnail_url": f"/api/photos/{photo_id}/thumbnail" if thumb_exists else None,
                "full_url": f"/api/photos/{photo_id}/full",
            })
    
    return {"photos": photos}


@router.get("/{photo_id}/thumbnail")
async def get_thumbnail(photo_id: str):
    """Serve a photo thumbnail."""
    thumb_path = os.path.join(THUMBS_DIR, f"thumb_{photo_id}.png")
    if not os.path.exists(thumb_path):
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(thumb_path, media_type="image/png")


@router.get("/{photo_id}/full")
async def get_full_photo(photo_id: str):
    """Serve the full processed photo."""
    # Look for the file with the photo_id as prefix
    if os.path.exists(PROCESSED_DIR):
        for filename in os.listdir(PROCESSED_DIR):
            if filename.startswith(photo_id):
                return FileResponse(
                    os.path.join(PROCESSED_DIR, filename),
                    media_type="image/png"
                )
    raise HTTPException(status_code=404, detail="Photo not found")


@router.delete("/{photo_id}")
async def delete_photo(photo_id: str):
    """Delete a photo and its thumbnail."""
    deleted = False
    
    # Delete from processed
    if os.path.exists(PROCESSED_DIR):
        for filename in os.listdir(PROCESSED_DIR):
            if filename.startswith(photo_id):
                os.remove(os.path.join(PROCESSED_DIR, filename))
                deleted = True
                break
    
    # Delete thumbnail
    thumb_path = os.path.join(THUMBS_DIR, f"thumb_{photo_id}.png")
    if os.path.exists(thumb_path):
        os.remove(thumb_path)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    return {"success": True, "id": photo_id}


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
                "thumbnail_url": f"/api/photos/{timestamp}/thumbnail"
            })
            
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {e}")
            results.append({"filename": file.filename, "error": str(e)})

    return {"photos": results}
