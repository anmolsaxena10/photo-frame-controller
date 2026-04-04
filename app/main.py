import sys
import os

# Add the waveshare EPD library to the Python path.
# The package lives at waveshare_epd/lib/waveshare_epd/ (vendor structure).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'waveshare_epd', 'lib'))

from state_manager import StateManager
from display_manager import DisplayManager
from ble_manager import BLEManager
from image_manager import ImageManager
from wifi_manager import WifiManager
from button_handler import ButtonHandler
import time

def main():
    # state = StateManager()
    display = DisplayManager()
    display.show_default()
    # button = ButtonHandler(state)

    # if state.is_first_boot():
    #     display.show_default()
    #     BLEManager(state).start_setup_mode()
    #     return

    # if state.mode == "offline":
    #     ImageManager(state).show_next_image()

    # elif state.mode == "online":
    #     WifiManager(state).ensure_connected()
    #     ImageManager(state).fetch_and_show()

    # state.schedule_sleep()

if __name__ == "__main__":
    main()
