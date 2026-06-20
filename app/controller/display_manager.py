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
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
            font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except Exception:
            # Fallback to default
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
            font_bold = ImageFont.load_default()
            
        # Draw text
        draw.text((40, 40), "Welcome to Photo Frame!", fill=(0, 0, 0), font=font_title)
        
        draw.text((40, 140), "To get started:", fill=(0, 0, 0), font=font_text)
        
        draw.text((40, 200), "1. Connect to WiFi:", fill=(0, 0, 0), font=font_text)
        draw.text((80, 250), f"Network:  {ssid}", fill=(200, 0, 0), font=font_bold)
        draw.text((80, 300), f"Password: {password}", fill=(200, 0, 0), font=font_bold)
        
        draw.text((40, 380), "2. Open browser:", fill=(0, 0, 0), font=font_text)
        draw.text((320, 380), url, fill=(0, 0, 128), font=font_bold)
        
        # Generate QR Code
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        
        # Paste QR code on the right side
        qr_x = width - qr_img.width - 60
        qr_y = (height - qr_img.height) // 2
        img.paste(qr_img, (qr_x, qr_y))
        
        # Display it
        self.show_image(img)
