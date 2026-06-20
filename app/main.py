import sys
import os
import asyncio
import logging
import uvicorn

# Add the waveshare EPD library to the Python path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'waveshare_epd', 'lib'))

from app.controller.state_manager import StateManager, FrameState
from app.server.app import create_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Photo Frame Controller...")
    
    # 1. Initialize state
    state = StateManager()
    state.initialize()
    logger.info(f"Initialized with mode: {state.current_mode.value}")
    
    # Placeholder for hardware initialization
    # display = DisplayManager()
    # processor = ImageProcessor()
    # wifi = WiFiManager()
    
    # 2. Initialize Server
    server_app = create_app(state)
    
    # 3. Start uvicorn
    # Using port 8000 for local development. Will bind to 80 in production.
    config = uvicorn.Config(server_app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    
    logger.info("Starting FastAPI server...")
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
