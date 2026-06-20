from PIL import Image
import logging
import os

logger = logging.getLogger(__name__)

class LayoutEngine:
    def __init__(self, display_manager):
        self.display = display_manager
        
    def render(self, base_image_path: str, widgets_config: dict = None):
        """
        Loads the base image and overlays any configured widgets.
        For Phase 1, we just pass the image through.
        """
        if not os.path.exists(base_image_path):
            logger.error(f"Image not found: {base_image_path}")
            return False
            
        try:
            base_image = Image.open(base_image_path)
            
            # Future phases:
            # if widgets_config and widgets_config.get("clock_enabled"):
            #     base_image = apply_clock_widget(base_image)
            # if widgets_config and widgets_config.get("weather_enabled"):
            #     base_image = apply_weather_widget(base_image)
            
            self.display.show_image(base_image)
            return True
        except Exception as e:
            logger.error(f"Failed to render layout for {base_image_path}: {e}")
            return False
