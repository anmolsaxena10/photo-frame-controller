import sys
import os
import asyncio
import logging
import uvicorn

# Add project root to sys.path so absolute imports like 'from app.controller...' work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add the waveshare EPD library to the Python path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'waveshare_epd', 'lib'))

from app.controller.state_manager import StateManager, FrameState
from app.controller.display_manager import DisplayManager
from app.controller.layout_engine import LayoutEngine
from app.controller.wifi_manager import WiFiManager
from app.controller.scheduler import Scheduler
from app.controller.button_handler import ButtonHandler
from app.server.app import create_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Photo Frame Controller...")
    
    # 1. Initialize core managers
    state = StateManager()
    state.initialize()
    logger.info(f"Initialized with mode: {state.current_mode.value}")
    
    display = DisplayManager()
    layout = LayoutEngine(display)
    wifi = WiFiManager()
    button = ButtonHandler(state)
    scheduler = Scheduler(state, layout)
    
    # 2. Boot Logic
    is_dev = os.environ.get("ENV", "prod").lower() == "dev"
    
    if state.current_mode == FrameState.FIRST_BOOT or state.current_mode == FrameState.AP_SETUP:
        if is_dev:
            logger.info("[DEV MODE] Skipping hardware AP creation.")
            ssid, password = "DEV_AP", "password"
            url = "http://localhost:8000"
        else:
            ssid, password = wifi.start_ap_mode()
            url = f"http://192.168.4.1"
        
        # Start a thread to show the setup screen so we don't block server start
        import threading
        threading.Thread(target=display.show_setup_screen, args=(ssid, password, url)).start()
        
        state.transition_to(FrameState.AP_SETUP)
    else:
        # We are in configured state, start carousel
        await scheduler.start()
    
    # 3. Initialize Server
    server_app = create_app(state)
    server_app.state.display = display
    server_app.state.scheduler = scheduler
    
    # 4. Start uvicorn
    # If not running as root, this might fail to bind to port 80.
    port = 80 if os.geteuid() == 0 else 8000
    config = uvicorn.Config(server_app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)
    
    logger.info(f"Starting FastAPI server on port {port}...")
    await server.serve()
    
    # Cleanup on exit
    await scheduler.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
