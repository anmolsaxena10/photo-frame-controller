# Photo Frame — Implementation Tasks & Testing Plan

This document breaks down the technical design into actionable implementation tasks, organized by component and phased delivery. It also includes the testing strategy for each major feature.

---

## 1. Phase 1: Core (MVP) + OTA + Editor
*Goal: A working photo frame with OTA capabilities, WiFi setup, and a robust PWA editor for cropping/previewing images.*

### 1.1 Foundation & State Management
- [x] Define Pydantic models for the extended `state.json` schema (including `ota` and `widgets`).
- [x] Implement `StateManager` class to handle loading/saving `data/state.json`.
- [x] Implement default state copy mechanism.
- [x] Update `requirements.txt` with new dependencies (`fastapi`, `uvicorn`, `python-multipart`, `aiofiles`, `qrcode`, `httpx`).
- [x] Refactor `main.py` entry point to load state and initialize core classes.

### 1.2 Setup Screen Generation & AP Mode
- [x] Implement `WiFiManager.start_ap_mode()` (hostapd, dnsmasq, routing).
- [x] Implement `DisplayManager.show_setup_screen(ssid, password, url)`.
- [x] Use `Pillow` to generate the 800x480 setup layout and `qrcode`.

### 1.3 OTA Updater (Mandatory First-Boot)
- [x] Implement `OTAUpdater.check_for_updates()` hitting GitHub API.
- [x] Implement download, extract, and replace logic.
- [x] Create `/api/system/ota` endpoints in FastAPI.
- [x] Ensure systemd service has permissions to restart itself (`sudo systemctl restart photo-frame-controller`).

### 1.4 Web App (PWA) Editor & Upload
- [x] Set up basic HTML/CSS shell with mobile-first bottom navigation.
- [x] Integrate Cropper.js (or similar) in the PWA for strict 800:480 cropping and rotation.
- [x] Implement `dither-worker.js` to process cropped image into the 7-color palette (Floyd-Steinberg algorithm).
- [x] Build the Preview UI to show the dithered result before upload.
- [x] Implement `/api/photos/upload` in FastAPI (accept multipart, save to disk, queue processing).

### 1.5 Layout Engine & Display
- [x] Implement `LayoutEngine` class. For Phase 1, it just composites the base image onto the canvas (preparation for widgets).
- [x] Implement `DisplayManager` to accept composited images from `LayoutEngine` and interface with Waveshare EPD.
- [x] Enforce 180-second minimum interval in `DisplayManager`.

### 1.6 Carousel & Reset
- [x] Implement `Scheduler._carousel_loop()` reading `refresh_interval` and `mode`.
- [x] Enhance `ButtonHandler` with debouncing and long-press detection (factory reset).

---

## 2. Phase 2: Advanced Editing & Integrations
*Goal: Home network connection, advanced editor variations, and Immich sync.*

### 2.1 Home WiFi & Auto-OTA
- [ ] Implement `WiFiManager.scan_networks()` and `connect_to_network()`.
- [ ] Implement background OTA polling in `Scheduler` based on user preferences.
- [ ] Setup mDNS (`avahi-daemon`).

### 2.2 Advanced Editor Variations
- [ ] Add Dithering Algorithm selection (Floyd-Steinberg, Atkinson) to PWA Web Worker.
- [ ] Add Contrast/Brightness sliders to PWA before dithering step.
- [ ] Implement `/api/photos` listing and deletion.

### 2.3 Immich Client Integration
- [ ] Implement `ImmichClient` using `httpx`.
- [ ] Implement server-side image processing for Immich downloads.
- [ ] Implement `Scheduler._immich_sync_loop()`.

### 2.4 Security
- [ ] Implement `OptionalAuthMiddleware` in FastAPI.
- [ ] Add PIN lock settings UI to PWA.

---

## 3. Phase 3: Widgets & Polish
*Goal: Display widgets, OS image bundling, and final polish.*

### 3.1 Widgets Integration
- [ ] Implement `clock.py` and `weather.py` widgets.
- [ ] Update `LayoutEngine` to render widgets on top of the base image.
- [ ] Build PWA UI for enabling/positioning widgets.

### 3.2 Pi-Gen Image Builder
- [ ] Update scripts for OS image generation (`00-packages` and `00-run.sh`).
- [ ] Test end-to-end flash of the `.img` file onto a fresh SD card.

---

## 4. Testing Strategy

### 4.1 Unit Testing (pytest)
- **State Manager:** Test default state creation, invalid state transitions, read/write to mock JSON.
- **Image Processor / Web Worker:** Provide sample RGB images, assert output size is exactly 800x480, assert color palette contains only the 7 allowed colors.
- **FastAPI Routes:** Use `TestClient` to test API responses, upload mocking, and settings validation.

### 4.2 Integration Testing
- **WiFi Manager:** Test AP mode creation (verify `hostapd` config generation).
- **OTA Updater:** Mock GitHub API responses, test the zip extraction and replace logic in a temporary directory.
- **Immich Client:** Use `httpx` mocking to simulate Immich API responses.

### 4.3 Hardware-in-the-Loop (HIL) Testing
These tests require the physical Raspberry Pi Zero 2W and Waveshare display:
- **Display Refresh Constraints:** Verify the `DisplayManager` successfully blocks/delays updates faster than 180s.
- **Button Reset:** Manually press the GPIO 17 button for 3 seconds. Verify logs show the reset sequence.

### 4.4 User Acceptance Testing (UX)
- **Zero-App Setup:** Connect via an iPhone and an Android phone to the AP. Ensure the captive portal automatically opens.
- **PWA Upload Performance:** Test Cropper and Web Worker with 10 high-resolution photos (e.g., 5MB each) to ensure the mobile browser tab doesn't crash.
- **OTA Flow:** Trigger the initial mandatory OTA flow and verify the device reboots and comes back online.
