import os
import logging
import time
import threading
from PIL import Image, ImageDraw, ImageFont
import qrcode

try:
    from waveshare_epd import epd7in3f
except Exception as e:
    epd7in3f = None
    logging.warning(f"waveshare_epd could not be loaded ({e}), using dummy display driver.")

logger = logging.getLogger(__name__)

class DisplayManager:
    def __init__(self):
        self.epd = None
        self.initialized = False
        self.last_refresh_time = 0
        self.min_refresh_interval = 180  # seconds
        self._lock = threading.Lock()
        
    def initialize(self):
        if self.initialized:
            return
            
        logger.info("Initializing E-Ink display...")
        if epd7in3f:
            self.epd = epd7in3f.EPD()
            self.epd.init()
        self.initialized = True
        
    def _enforce_refresh_interval(self):
        now = time.time()
        elapsed = now - self.last_refresh_time
        if elapsed < self.min_refresh_interval:
            sleep_time = self.min_refresh_interval - elapsed
            logger.info(f"Enforcing minimum refresh interval. Sleeping for {sleep_time:.1f}s")
            time.sleep(sleep_time)

    def show_image(self, image: Image.Image):
        """Display a PIL Image object."""
        with self._lock:
            self._enforce_refresh_interval()
            self.initialize()
            
            logger.info("Displaying image on e-paper...")
            if self.epd:
                # Ensure correct size
                if image.size != (self.epd.width, self.epd.height):
                    image = image.resize((self.epd.width, self.epd.height))
                
                # Convert to RGB
                if image.mode != "RGB":
                    image = image.convert("RGB")
                    
                buffer = self.epd.getbuffer(image)
                self.epd.display(buffer)
                self.epd.sleep()
                
            self.last_refresh_time = time.time()
            self.initialized = False  # Sleep means we need to re-init next time
            logger.info("Image displayed and display put to sleep.")
            
    def show_setup_screen(self, ssid: str, password: str, url: str):
        """Generate and display the first-boot setup screen using PIL."""
        width = 800
        height = 480
        
        # Create white background
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Try to load a font
        try:
            # Bookworm typical paths
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
            font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
            font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
        except Exception:
            # Fallback to default
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
            font_bold = ImageFont.load_default()
            font_small = ImageFont.load_default()
            
        # Draw title
        draw.text((40, 30), "Photo Frame Setup", fill=(0, 0, 0), font=font_title)
        
        # Draw setup instructions
        draw.text((40, 110), "1. Scan QR to connect to WiFi", fill=(0, 0, 0), font=font_text)
        
        draw.text((60, 155), f"Network:  {ssid}", fill=(200, 0, 0), font=font_bold)
        draw.text((60, 195), f"Password: {password}", fill=(200, 0, 0), font=font_bold)
        
        draw.text((40, 260), "2. Open in browser:", fill=(0, 0, 0), font=font_text)
        draw.text((60, 300), url, fill=(0, 0, 128), font=font_bold)
        
        draw.text((40, 365), "3. Enter your home WiFi details", fill=(0, 0, 0), font=font_text)
        
        draw.text((40, 430), "Then your frame will connect & restart.", fill=(100, 100, 100), font=font_small)
        
        # Generate WiFi QR Code (standard format for auto-connecting)
        wifi_qr_data = f"WIFI:T:WPA;S:{ssid};P:{password};;"
        qr = qrcode.QRCode(version=1, box_size=7, border=2)
        qr.add_data(wifi_qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        
        # Paste QR code on the right side
        qr_x = width - qr_img.width - 40
        qr_y = (height - qr_img.height) // 2
        img.paste(qr_img, (qr_x, qr_y))
        
        # Label below QR
        qr_label = "Scan to connect"
        label_bbox = draw.textbbox((0, 0), qr_label, font=font_small)
        label_w = label_bbox[2] - label_bbox[0]
        label_x = qr_x + (qr_img.width - label_w) // 2
        draw.text((label_x, qr_y + qr_img.height + 5), qr_label, fill=(80, 80, 80), font=font_small)
        
        # Display it
        self.show_image(img)
