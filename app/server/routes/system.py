from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging

from app.controller.ota_updater import OTAUpdater

logger = logging.getLogger(__name__)

router = APIRouter()

class OtaUpdateSettings(BaseModel):
    auto_update: bool

@router.get("/ota")
async def get_ota_status(request: Request):
    state_manager = request.app.state.state_manager
    state = state_manager.get_state()
    return {
        "current_version": state.ota.current_version,
        "auto_update": state.ota.auto_update,
        "last_check": state.ota.last_check,
        "mandatory_initial_done": state.ota.mandatory_initial_done
    }

@router.put("/ota")
async def update_ota_settings(settings: OtaUpdateSettings, request: Request):
    state_manager = request.app.state.state_manager
    state = state_manager.get_state()
    state.ota.auto_update = settings.auto_update
    state_manager.save()
    return {"success": True, "auto_update": state.ota.auto_update}

@router.post("/ota/check")
async def check_for_updates(request: Request):
    state_manager = request.app.state.state_manager
    updater = OTAUpdater(state_manager=state_manager)
    
    result = await updater.check_for_updates()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result

@router.post("/ota/update")
async def trigger_update(request: Request, background_tasks: BackgroundTasks):
    state_manager = request.app.state.state_manager
    updater = OTAUpdater(state_manager=state_manager)
    
    result = await updater.check_for_updates()
    if not result.get("update_available"):
        # For initial boot, if no update is available, we still want to mark it as done
        state = state_manager.get_state()
        if not state.ota.mandatory_initial_done:
            state.ota.mandatory_initial_done = True
            state_manager.save()
        return {"success": False, "message": "No update available."}
        
    download_url = result.get("download_url")
    new_version = result.get("latest_version")
    
    if not download_url:
        raise HTTPException(status_code=500, detail="No download URL found for update.")
        
    # Run update in background as it will restart the service
    background_tasks.add_task(updater.download_and_apply, download_url, new_version)
    
    return {"success": True, "message": "Update started. System will restart shortly."}
