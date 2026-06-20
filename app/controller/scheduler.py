import asyncio
import logging
import os
import random

from app.controller.state_manager import StateManager, FrameState
from app.controller.layout_engine import LayoutEngine

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, state_manager: StateManager, layout_engine: LayoutEngine):
        self.state = state_manager
        self.layout = layout_engine
        self._carousel_task = None
        
    async def start(self):
        if self._carousel_task is None or self._carousel_task.done():
            self._carousel_task = asyncio.create_task(self._carousel_loop())
            
    async def stop(self):
        if self._carousel_task and not self._carousel_task.done():
            self._carousel_task.cancel()
            try:
                await self._carousel_task
            except asyncio.CancelledError:
                pass
                
    async def _carousel_loop(self):
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        processed_dir = os.path.join(data_dir, "processed")
        
        while True:
            try:
                state_model = self.state.get_state()
                current_mode = self.state.current_mode
                
                # Only run carousel if configured and displaying
                if current_mode == FrameState.CONFIGURED or current_mode == FrameState.DISPLAYING:
                    if state_model.carousel.enabled:
                        images = []
                        if os.path.exists(processed_dir):
                            images = sorted([f for f in os.listdir(processed_dir) if f.endswith('.png')])
                            
                        if images:
                            if state_model.carousel.mode == "random":
                                next_img = random.choice(images)
                            else: # sequential
                                idx = state_model.carousel.current_index
                                if idx >= len(images):
                                    idx = 0
                                next_img = images[idx]
                                state_model.carousel.current_index = (idx + 1) % len(images)
                                self.state.save()
                                
                            img_path = os.path.join(processed_dir, next_img)
                            logger.info(f"Carousel: Showing {next_img}")
                            
                            widgets_config = state_model.widgets.model_dump()
                            self.layout.render(img_path, widgets_config)
                            
                            if current_mode == FrameState.CONFIGURED:
                                self.state.transition_to(FrameState.DISPLAYING)
                                
                # Sleep for refresh interval
                interval_minutes = state_model.carousel.refresh_interval_minutes
                # Enforce minimum 180s at the scheduler level
                interval_seconds = max(interval_minutes * 60, 180)
                
                # Sleep in chunks so we can check for cancellations or state changes
                for _ in range(int(interval_seconds)):
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                logger.info("Carousel loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in carousel loop: {e}")
                await asyncio.sleep(60) # Wait a bit before retrying
