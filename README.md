# E-Ink Photo Frame Controller

A local-first, lightweight controller for a Waveshare 7.3" 7-color e-Paper display running on a Raspberry Pi Zero 2W.

**Hardware Details:**
- **Photo frame**: [7.3inch e-Paper HAT (F) Manual](https://www.waveshare.com/wiki/7.3inch_e-Paper_HAT_(F)_Manual#Working_With_Raspberry_Pi)
- **Controller**: Raspberry Pi Zero 2W

## Goals
1. **First time start**: Show a default setup image and spin up a local WiFi Hotspot (`PhotoFrame-XXXX`).
2. **Setup via PWA**: Connect to the AP and open the captive portal (Web UI) to crop, dither, and upload photos.
3. **Subsequent runs**: The RPi cycles through uploaded photos locally, adhering to the strict hardware refresh limits (180s minimum).
4. **OTA Updates**: Automatically checks GitHub releases to download and extract updates to keep the frame logic fresh.
5. **Reset**: Holding the physical button (GPIO 17) for 3 seconds triggers a factory reset.

---

## 🛠 Local Development & Testing

You do not need the physical E-Ink display to test the web interface and API locally. The application gracefully falls back when the hardware driver is not detected.

### Prerequisites
- Python 3.10+
- Node/NPM (Optional, if you wish to use local web development tools, but the Web UI is currently Vanilla HTML/JS)

### Dev Setup
1. Clone the repository:
   ```bash
   git clone <your_repo> eink-frame
   cd eink-frame
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running Locally
To test the backend and the Web UX without triggering hardware errors:
```bash
# This starts the FastAPI server locally on port 8000
python3 app/main.py
```

- **Open Web UX:** Open your browser and navigate to `http://localhost:8000`. 
- **Test Cropper & Dithering:** You can upload an image, test the Cropper.js interface, and view the Floyd-Steinberg 7-color Web Worker preview right in your browser.
- **Data Storage:** Uploaded photos and state will be saved in the local `data/` directory inside the project root.

---

## 🚀 Raspberry Pi Setup (Production)

### 1. Dependencies
```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git dnsmasq hostapd
```

### 2. Python Environment
```bash
cd /opt
sudo git clone <your_repo> eink-frame
cd eink-frame

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Service Setup
```bash
sudo cp service/photo-frame.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable photo-frame
sudo systemctl start photo-frame
```
*(Note: Ensure the service user has privileges to run hostapd/dnsmasq and interact with GPIO).*
