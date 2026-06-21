import logging
import time
import threading
try:
    from gpiozero import Button as GpioButton
except Exception as e:
    GpioButton = None
    
logger = logging.getLogger(__name__)

class ButtonHandler:
    RESET_PIN = 27  # GPIO27 — avoid GPIO17 which is used by the e-ink display RST
    DEBOUNCE_S = 0.5
    LONG_PRESS_MS = 3000
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self._press_start_time = 0
        self._button = None
        self._setup_gpio()
        
    def _setup_gpio(self):
        if not GpioButton:
            logger.warning("gpiozero not available. Button handler disabled.")
            return
            
        self._button = GpioButton(
            self.RESET_PIN,
            pull_up=True,
            bounce_time=self.DEBOUNCE_S
        )
        self._button.when_pressed = self._on_press
        self._button.when_released = self._on_release
        logger.info(f"GPIO {self.RESET_PIN} setup for reset button (gpiozero).")
        
    def _on_press(self):
        self._press_start_time = time.time() * 1000
    
    def _on_release(self):
        if self._press_start_time == 0:
            return
        press_duration = (time.time() * 1000) - self._press_start_time
        self._press_start_time = 0
        
        logger.info(f"Button released after {press_duration:.0f}ms")
        if press_duration >= self.LONG_PRESS_MS:
            logger.warning("Long press detected. Triggering factory reset.")
            threading.Thread(target=self._perform_reset).start()
        else:
            logger.info("Short press detected.")
                
    def _perform_reset(self):
        self.state_manager.reset()
        import subprocess
        logger.info("Restarting service after factory reset...")
        subprocess.Popen(["sudo", "systemctl", "restart", "photo-frame-controller"])
