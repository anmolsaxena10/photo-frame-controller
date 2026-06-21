from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()


class CarouselSettingsRequest(BaseModel):
    mode: Optional[str] = None  # "sequential" or "random"
    refresh_interval_minutes: Optional[int] = Field(None, ge=3, le=1440)
    enabled: Optional[bool] = None


class SettingsResponse(BaseModel):
    display_name: str
    carousel_mode: str
    carousel_enabled: bool
    refresh_interval_minutes: int
    widgets_clock: bool
    widgets_weather: bool


@router.get("")
async def get_settings(request: Request):
    """Get all frame settings."""
    state_manager = request.app.state.state_manager
    state = state_manager.get_state()
    
    return {
        "display_name": state.display_name,
        "carousel": {
            "mode": state.carousel.mode,
            "enabled": state.carousel.enabled,
            "refresh_interval_minutes": state.carousel.refresh_interval_minutes,
        },
        "widgets": {
            "clock_enabled": state.widgets.clock_enabled,
            "weather_enabled": state.widgets.weather_enabled,
        },
        "ota": {
            "auto_update": state.ota.auto_update,
            "current_version": state.ota.current_version,
        }
    }


@router.put("/carousel")
async def update_carousel_settings(settings: CarouselSettingsRequest, request: Request):
    """Update carousel/slideshow settings."""
    state_manager = request.app.state.state_manager
    state = state_manager.get_state()
    
    if settings.mode is not None:
        state.carousel.mode = settings.mode
    if settings.refresh_interval_minutes is not None:
        state.carousel.refresh_interval_minutes = settings.refresh_interval_minutes
    if settings.enabled is not None:
        state.carousel.enabled = settings.enabled
    
    state_manager.save()
    
    return {
        "success": True,
        "carousel": {
            "mode": state.carousel.mode,
            "enabled": state.carousel.enabled,
            "refresh_interval_minutes": state.carousel.refresh_interval_minutes,
        }
    }


class DisplayNameRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=32)


@router.put("/display-name")
async def update_display_name(body: DisplayNameRequest, request: Request):
    """Update the frame display name."""
    state_manager = request.app.state.state_manager
    state = state_manager.get_state()
    state.display_name = body.display_name
    state_manager.save()
    return {"success": True, "display_name": state.display_name}
