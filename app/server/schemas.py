from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class FrameState(str, Enum):
    FIRST_BOOT = "first_boot"
    AP_SETUP = "ap_setup"
    OTA_UPDATE = "ota_update"
    CONFIGURED = "configured"
    DISPLAYING = "displaying"

class OtaConfig(BaseModel):
    auto_update: bool = True
    last_check: Optional[str] = None
    current_version: str = "1.0.0"
    mandatory_initial_done: bool = False

class CarouselConfig(BaseModel):
    mode: str = "sequential"
    refresh_interval_minutes: int = 240
    current_index: int = 0
    enabled: bool = True

class ImmichConfig(BaseModel):
    enabled: bool = False
    server_url: Optional[str] = None
    api_key: Optional[str] = None
    album_id: Optional[str] = None
    sync_interval_minutes: int = 360
    last_sync: Optional[str] = None
    last_sync_status: Optional[str] = None

class WidgetsConfig(BaseModel):
    clock_enabled: bool = False
    weather_enabled: bool = False

class AuthConfig(BaseModel):
    enabled: bool = False
    pin_hash: Optional[str] = None

class SystemConfig(BaseModel):
    reserved_space_mb: int = 500
    ap_password: Optional[str] = None

class AppStateModel(BaseModel):
    first_boot: bool = True
    wifi_configured: bool = False
    wifi_ssid: Optional[str] = None
    hostname: str = "photoframe"
    display_name: str = "My Photo Frame"
    ota: OtaConfig = Field(default_factory=OtaConfig)
    carousel: CarouselConfig = Field(default_factory=CarouselConfig)
    immich: ImmichConfig = Field(default_factory=ImmichConfig)
    widgets: WidgetsConfig = Field(default_factory=WidgetsConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
