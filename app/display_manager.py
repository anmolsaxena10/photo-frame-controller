# app/display_manager.py

import os
import logging
from PIL import Image

from waveshare_epd import epd7in3f


class DisplayManager:
    def __init__(self):
        self.epd = None
        self.initialized = False

    def initialize(self):
        """Initialize the E-Ink display"""
        if self.initialized:
            return

        logging.info("Initializing E-Ink display...")
        self.epd = epd7in3f.EPD()
        self.epd.init()
        self.initialized = True

    def show_image(self, image_path: str):
        """
        Display an image on the e-paper screen.
        Automatically resizes to 800x480.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        self.initialize()

        logging.info(f"Displaying image: {image_path}")

        image = Image.open(image_path)

        # Ensure correct size
        image = image.resize((self.epd.width, self.epd.height))

        # Convert to required mode
        image = image.convert("RGB")

        self.epd.display(self.epd.getbuffer(image))
        self.epd.sleep()

        logging.info("Image displayed and display put to sleep.")

    def show_default(self):
        """Show default bundled image"""
        default_path = "/opt/photo-frame-controller/config/default.jpg"
        self.show_image(default_path)

    def clear(self):
        """Clear the display (white screen)"""
        self.initialize()
        self.epd.Clear()
        self.epd.sleep()

    def shutdown(self):
        """Release hardware resources"""
        if self.epd:
            logging.info("Putting display to sleep...")
            self.epd.sleep()
