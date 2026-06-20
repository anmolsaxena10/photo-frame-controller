# Photo Frame — Technical Design Document

## 1. System Architecture Overview

```mermaid
graph TB
    subgraph "RPi Zero 2W"
        subgraph "Controller Layer"
            SM["StateManager<br/>(state machine)"]
            OTA["OTAUpdater<br/>(GitHub pull/extract)"]
            LE["LayoutEngine<br/>(Widget Compositor)"]
            DM["DisplayManager<br/>(EPD driver wrapper)"]
            IP["ImageProcessor<br/>(dithering pipeline)"]
            WM["WiFiManager<br/>(AP/STA mode switch)"]
            IC["ImmichClient<br/>(album sync)"]
            BH["ButtonHandler<br/>(GPIO 17 reset)"]
            SCH["Scheduler<br/>(carousel timer)"]
        end

        subgraph "Server Layer"
            FA["FastAPI Server<br/>(uvicorn)"]
            PWA["Static PWA Files<br/>(HTML/CSS/JS)"]
        end

        subgraph "Hardware"
            EPD["Waveshare 7.3in EPD<br/>(SPI)"]
            WIFI["WiFi Radio<br/>(wlan0)"]
            GPIO["GPIO 17<br/>(reset button)"]
        end

        subgraph "Storage"
            STATE["data/state.json"]
            IMGS["data/images/<br/>(originals)"]
            PROC["data/processed/<br/>(dithered)"]
            THUMBS["data/thumbnails/"]
        end
    end

    subgraph "User Device"
        BROWSER["Browser (PWA)"]
    end

    subgraph "External (Optional)"
        IMMICH["Immich Server"]
        GITHUB["GitHub API (OTA)"]
    end

    BROWSER -->|"HTTP/REST"| FA
    FA --> SM
    FA --> OTA
    FA --> DM
    FA --> IP
    FA --> WM
    FA --> IC
    SM --> STATE
    OTA -->|"HTTP"| GITHUB
    LE --> DM
    IP --> IMGS
    IP --> PROC
    IC -->|"HTTP"| IMMICH
    IC --> IMGS
    BH --> GPIO
    BH --> SM
    SCH --> LE
    SCH --> SM
    WM --> WIFI
    FA --> PWA
```

---

## 2. Directory Structure

```
/opt/photo-frame-controller/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Entry point — starts FastAPI + controller
│   ├── controller/
│   │   ├── __init__.py
│   │   ├── state_manager.py       # State machine + persistence
│   │   ├── ota_updater.py         # OTA download and installation logic
│   │   ├── layout_engine.py       # Composites images + widgets using PIL
│   │   ├── display_manager.py     # EPD hardware wrapper
│   │   ├── image_processor.py     # Dithering, resize, palette quantization
│   │   ├── wifi_manager.py        # AP mode / STA mode switching
│   │   ├── immich_client.py       # Immich API integration
│   │   ├── button_handler.py      # GPIO reset button
│   │   ├── scheduler.py           # Carousel timer / Immich sync scheduler
│   │   └── widgets/               # Future plugins (clock.py, weather.py)
│   ├── server/
│   │   ├── __init__.py
│   │   ├── app.py                 # FastAPI application factory
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── photos.py          # Photo upload/management endpoints
│   │   │   ├── settings.py        # Frame settings endpoints
│   │   │   ├── wifi.py            # WiFi config endpoints
│   │   │   ├── immich.py          # Immich integration endpoints
│   │   │   ├── system.py          # System status/reset/OTA endpoints
│   │   │   └── display.py         # Display control endpoints
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── auth.py            # Optional PIN authentication
│   │   └── schemas.py             # Pydantic request/response models
│   └── waveshare_epd/             # Vendor driver (existing)
├── web/                            # PWA static files
│   ├── index.html
│   ├── manifest.json
│   ├── sw.js                       # Service worker
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── app.js                  # Main application logic
│   │   ├── api.js                  # API client wrapper
│   │   ├── editor.js               # Crop, rotate, canvas manipulations
│   │   ├── upload.js               # Upload logic + progress
│   │   ├── dither-worker.js        # Web Worker for client-side dithering (Floyd-Steinberg/Atkinson)
│   │   └── components/
│   │       ├── setup-wizard.js
│   │       ├── gallery.js
│   │       ├── settings.js
│   │       └── immich-config.js
│   └── assets/
├── config/
│   ├── default-state.json          # Factory default state template
│   └── default.jpg                 # Default boot image (or generated)
├── data/
│   ├── state.json                  # Runtime state (mutable)
│   ├── images/                     # Original uploaded images
│   ├── processed/                  # Dithered/quantized versions
│   └── thumbnails/                 # Small thumbnails for PWA gallery
├── service/
│   └── photo-frame-controller.service
├── requirements.txt
└── setup.sh
```

---

## 3. Controller Design

### 3.1 State Manager
The `StateManager` is the central coordinator. It owns the state file and provides the canonical view of the system's current mode. Includes persistence and state transition logic.

### 3.2 OTA Updater
Manages checking, downloading, and applying updates from GitHub.

```python
class OTAUpdater:
    def __init__(self, repo="saxanmol/photo-frame-controller"):
        self.repo = repo
        
    async def check_for_updates(self) -> dict:
        """Query GitHub API for latest release/artifact. Return version info."""
        
    async def download_and_apply(self, artifact_url: str) -> bool:
        """
        1. Download zip file to /tmp
        2. Extract contents
        3. Copy over /opt/photo-frame-controller (excluding /data and /config)
        4. Trigger systemd service restart via dbus or sudo command
        """
```

### 3.3 Layout Engine & Widgets
Instead of the `DisplayManager` directly rendering raw images, the `LayoutEngine` acts as an intermediary, treating the display as a canvas.

```python
class LayoutEngine:
    def __init__(self, display_manager):
        self.display = display_manager
        
    def render(self, base_image_path: str, widgets_config: dict) -> Image:
        """
        1. Open base_image (already 800x480)
        2. If widgets_config.clock_enabled: Overlay clock text/graphics
        3. If widgets_config.weather_enabled: Overlay weather icons
        4. Return final composite Image
        """
```

### 3.4 Display Manager
Wraps the E-Ink hardware.
- Enforces the 180s minimum interval via thread locks.
- `show_setup_screen(ssid, password, url)` generates PIL text/QR layouts.

### 3.5 Image Processor
Handles server-side processing for Immich downloads or fallback. Resizes, crops, and dithers images to the 7-color palette (Black, White, Green, Blue, Red, Yellow, Orange).

### 3.6 WiFi Manager
Manages the dual-mode WiFi: Access Point (hostapd+dnsmasq) ↔ Station (nmcli).

### 3.7 Immich Client
Handles communication with an external Immich server (`httpx`). Checks for new assets in an album and queues downloads.

### 3.8 Scheduler & Button Handler
Carousel timer loop, Immich background sync loop, and GPIO 17 reset functionality.

---

## 4. API Server Design

### 4.1 FastAPI Application Structure
REST APIs mounted under `/api/`, PWA served under `/`.

### 4.2 API Endpoints — Detailed Design

**Photos API**
- `POST /api/photos/upload`: Accept multipart files. Supports `pre_processed=true` flag.
- `GET /api/photos`, `DELETE /api/photos/{id}`, `GET /api/photos/{id}/thumbnail`.

**Settings API**
- `GET/PUT /api/settings`: Manage carousel, display name, etc.
- `GET/PUT /api/settings/widgets`: Toggle widgets (clock, weather).

**WiFi API**
- `GET /api/wifi/status`, `GET /api/wifi/scan`, `POST /api/wifi/connect`.

**Immich API**
- `GET/PUT /api/integrations/immich`, `POST /api/integrations/immich/sync`.

**System & OTA API**
- `GET /api/system/status`: Storage, display state.
- `GET /api/system/ota`: Current version, update available, OTA settings.
- `PUT /api/settings/ota`: Configure auto-update preference.
- `POST /api/system/ota/update`: Manually trigger an update.

**Display Control API**
- `POST /api/display/refresh`, `POST /api/display/show/{photo_id}`.

### 4.3 Authentication Middleware
Optional PIN-based authentication (`X-Frame-PIN` header). Exempts `/api/wifi/status`.

---

## 5. PWA Design

### 5.1 Editor Flow (Client-Side Processing)
To reduce CPU load on the RPi Zero 2W and offer a better UX:

```mermaid
sequenceDiagram
    participant User
    participant Cropper
    participant Worker as Dither Worker
    participant API

    User->>Cropper: Select Image
    User->>Cropper: Rotate / Adjust Crop Box (800x480 locked)
    User->>Cropper: Change Dither Algorithm
    Cropper->>Worker: Send cropped pixels
    Worker-->>Cropper: Return 7-color preview
    User->>Cropper: Click "Upload"
    Cropper->>API: POST /api/photos/upload (pre_processed=true)
```

### 5.2 Application Architecture
The PWA is an SPA with vanilla JavaScript.
- Bottom navigation (Mobile-first).
- Dark theme matching the e-ink context.

### 5.3 Setup Wizard Flow
1. Welcome Screen
2. WiFi Config (connect to home network)
3. **OTA Check**: Initial mandatory update check over the internet.
4. Upload Photos (with Editor preview)
5. Carousel Config
6. Done

---

## 6. Networking Design

### 6.1 AP Mode (First-Time Setup)
```mermaid
graph LR
    subgraph "RPi Zero 2W"
        AP["hostapd<br/>SSID: PhotoFrame-XXXX<br/>WPA2"]
        DNS["dnsmasq<br/>DHCP: 192.168.4.10-50<br/>DNS: * → 192.168.4.1"]
        SERVER["FastAPI<br/>:80 on 192.168.4.1"]
        AVAHI["avahi-daemon<br/>photoframe.local"]
    end

    PHONE["User's Phone"] -->|"Connects to WiFi AP"| AP
    AP -->|"DHCP lease"| DNS
    PHONE -->|"Any HTTP request"| DNS
    DNS -->|"Redirects to"| SERVER
    PHONE -->|"http://192.168.4.1"| SERVER
```

### 6.2 Station Mode (Home Network)
```mermaid
graph LR
    subgraph "Home Network"
        ROUTER["WiFi Router"]
    end

    subgraph "RPi Zero 2W"
        WLAN["wlan0<br/>DHCP client"]
        SERVER["FastAPI<br/>:80"]
        AVAHI["avahi-daemon<br/>photoframe.local"]
    end

    subgraph "External"
        IMMICH["Immich Server"]
        GITHUB["GitHub API"]
    end

    PHONE["Any Device"] --> ROUTER
    ROUTER --> WLAN
    PHONE -->|"http://photoframe.local"| SERVER
    WLAN -->|"API calls"| IMMICH
    WLAN -->|"OTA Update"| GITHUB
    AVAHI -->|"mDNS broadcast"| ROUTER
```

---

## 7. Data Flow Diagrams

### 7.1 Image Upload Flow
```mermaid
sequenceDiagram
    participant Browser as PWA (Browser)
    participant Worker as Web Worker
    participant API as FastAPI
    participant Proc as ImageProcessor
    participant Disk as File System

    Browser->>Browser: User selects image files
    Browser->>Worker: Send ImageData to dither-worker
    Worker->>Worker: Crop & Resize to 800×480
    Worker->>Worker: Dither Algorithm
    Worker-->>Browser: Return dithered preview
    Browser->>Browser: Show preview to user

    Browser->>API: POST /api/photos/upload (multipart, pre_processed=true)
    API->>Disk: Save original to data/images/
    API->>Disk: Save processed to data/processed/
    API->>Proc: Generate thumbnail
    Proc->>Disk: Save thumbnail to data/thumbnails/
```

### 7.2 Immich Sync Flow
```mermaid
sequenceDiagram
    participant Sched as Scheduler
    participant IC as ImmichClient
    participant Immich as Immich Server
    participant Proc as ImageProcessor
    participant Disk as File System

    Sched->>IC: sync_album(album_id)
    IC->>Immich: GET /api/albums/{id}
    Immich-->>IC: { assets: [...] }
    IC->>IC: Diff: new assets to download

    loop For each new asset
        IC->>Immich: GET /api/assets/{id}/original
        Immich-->>IC: Image bytes
        IC->>Disk: Save to data/images/
        IC->>Proc: process_image()
        Proc->>Disk: Save to data/processed/
        Proc->>Disk: Save thumbnail
    end
```

---

## 8. Systemd & Process Design

```ini
[Unit]
Description=E-Ink Photo Frame Controller & Web Server
After=network.target bluetooth.target
Wants=avahi-daemon.service

[Service]
User=root
WorkingDirectory=/opt/photo-frame-controller
ExecStart=/opt/photo-frame-controller/venv/bin/python -m app.main
Restart=always
RestartSec=5
Environment=PYTHONPATH=/opt/photo-frame-controller

# Resource limits for RPi Zero 2W
MemoryMax=256M
CPUQuota=90%

[Install]
WantedBy=multi-user.target
```

---

## 9. Error Handling & Recovery

| Scenario | Handling |
|----------|----------|
| Display refresh fails | Log error, retry after 180s, max 3 retries |
| WiFi AP creation fails | Log error, retry with different channel |
| Home WiFi connect fails | Revert to AP mode, show error on display |
| Immich server unreachable | Exponential backoff (5min → 15min → 1hr → 4hr) |
| OTA download fails | Revert to current version, log error |
| Disk full during upload | Return 507 error, warn user in PWA |
| State file corrupted | Reset to default-state.json |

---

## 10. Dependencies (Updated requirements.txt)

```
# Hardware
RPi.GPIO
pillow
spidev

# Web server
fastapi
uvicorn[standard]

# HTTP client (for Immich, OTA)
httpx

# QR code generation (for setup screen)
qrcode[pil]

# Utilities
python-multipart    # For FastAPI file uploads
aiofiles            # Async file operations
pydantic            # Data validation
```
