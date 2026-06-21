# E-Ink Photo Frame Controller

A local-first, lightweight controller for a Waveshare 7.3" 7-color e-Paper display running on a Raspberry Pi.

**Hardware:**
- **Display**: [Waveshare 7.3inch e-Paper HAT (F)](https://www.waveshare.com/wiki/7.3inch_e-Paper_HAT_(F)_Manual#Working_With_Raspberry_Pi)
- **Controller**: Raspberry Pi Zero 2W (also tested on Pi 5)
- **SPI switch on HAT**: Must be set to **4-line SPI**

## Architecture

```mermaid
graph TD
    Service[photo-frame-controller service] --> FastAPI[FastAPI port 80]
    FastAPI --> WiFiAPI[/api/wifi]
    FastAPI --> PhotosAPI[/api/photos]
    FastAPI --> SettingsAPI[/api/settings]
    Service --> DisplayMgr[Display Manager - SPI/GPIO]
    Service --> WiFiMgr[WiFi Manager - hostapd/dnsmasq/nmcli]
    DisplayMgr --> EPD[7.3 inch E-Ink 800x480 7-color]
```

## User Flow

### First Boot
1. Pi creates WiFi AP: `PhotoFrame-XXXX`
2. E-ink display shows setup screen with WiFi QR code
3. User scans QR (auto-connects phone to AP)
4. Opens `http://192.168.4.1` → WiFi setup page
5. User selects home WiFi network and enters password
6. Pi connects to home WiFi, tears down AP, restarts service

### Normal Operation
- Frame cycles through uploaded photos on a configurable interval
- Access web UI via `http://photo-frame.local` (mDNS) or the Pi's IP
- Upload/crop/preview photos through the web interface
- 7-color Floyd-Steinberg dithering preview before upload

### Factory Reset
- Hold GPIO27 button for 3+ seconds → resets to first-boot state

---

## Local Development

No physical display needed — the app falls back gracefully when hardware is unavailable.

### Prerequisites
- Python 3.10+

### Setup
```bash
git clone <repo> photo-frame-controller
cd photo-frame-controller
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running
```bash
ENV=dev python3 app/main.py
```
Opens at `http://localhost:8000`. Bypasses GPIO, AP mode, and e-ink hardware.

---

## Production (OS Image Build)

The project uses [pi-gen](https://github.com/RPi-Distro/pi-gen) to produce a complete SD card image.

### Building
```bash
cd image-builder
chmod +x build.sh
sudo ./build.sh
```

Or via GitHub Actions: push a tag `v*.*.*` to trigger the build workflow.

### Image contents
- Bookworm Lite base (stages 0-2)
- Custom `photo-frame` stage: installs dependencies, copies app, enables service
- Packages: `hostapd`, `dnsmasq`, `network-manager`, `avahi-daemon`, `bluez`, `python3-gpiozero`, `python3-lgpio`
- Service runs as root (requires GPIO, SPI, network management)

### Key config
| File | Purpose |
|------|---------|
| `image-builder/config` | pi-gen build config |
| `image-builder/stage-photo-frame/` | Custom stage (packages, install script) |
| `service/photo-frame-controller.service` | systemd unit |

---

## Hardware Notes

- **SPI switch**: Must be **4-line SPI** (the waveshare driver uses a separate DC pin)
- **GPIO usage**:
  - GPIO17 — E-ink RST (display reset)
  - GPIO25 — E-ink DC (data/command)
  - GPIO8  — E-ink CS (chip select, SPI CE0)
  - GPIO24 — E-ink BUSY
  - GPIO18 — E-ink PWR
  - GPIO10 — SPI MOSI
  - GPIO11 — SPI SCLK
  - GPIO27 — Physical reset button (pull-up, active low)
- **Power supply**: Pi 5 requires USB-C PD 5V/5A. Underpowered supply causes solid red LED with no boot.
- **WiFi country**: Must be set (`WPA_COUNTRY` in pi-gen config) or WiFi stays RF-killed on boot.

---

## Project Structure

```
├── app/
│   ├── controller/        # Hardware & logic managers
│   │   ├── button_handler.py
│   │   ├── display_manager.py
│   │   ├── layout_engine.py
│   │   ├── ota_updater.py
│   │   ├── scheduler.py
│   │   ├── state_manager.py
│   │   └── wifi_manager.py
│   ├── server/            # FastAPI app & routes
│   │   ├── app.py
│   │   ├── schemas.py
│   │   └── routes/
│   ├── waveshare_epd/     # Display driver library
│   └── main.py            # Entry point
├── web/                   # Frontend (vanilla HTML/JS)
│   ├── index.html         # Main UI (upload/gallery/settings)
│   ├── setup.html         # WiFi setup page (self-contained, no CDN)
│   ├── css/
│   └── js/
├── config/                # Default state
├── data/                  # Runtime data (images, state.json)
├── image-builder/         # pi-gen build scripts
├── service/               # systemd unit file
└── requirements.txt
```
