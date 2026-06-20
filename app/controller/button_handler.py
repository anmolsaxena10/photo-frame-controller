import logging
import time
import threading
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None
    
logger = logging.getLogger(__name__)

class ButtonHandler:
    RESET_PIN = 17
    DEBOUNCE_MS = 500
    LONG_PRESS_MS = 3000
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self._last_press_time = 0
        self._setup_gpio()
        
    def _setup_gpio(self):
        if not GPIO:
            logger.warning("RPi.GPIO not available. Button handler disabled.")
            return
            
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.RESET_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            self.RESET_PIN, 
            GPIO.BOTH, # Detect both falling and rising edges to measure press duration
            callback=self._on_button_event,
            bouncetime=100
        )
        logger.info(f"GPIO {self.RESET_PIN} setup for reset button.")
        
    def _on_button_event(self, channel):
        current_time = time.time() * 1000
        
        is_pressed = not GPIO.input(channel)
        
        if is_pressed:
            if current_time - self._last_press_time > self.DEBOUNCE_MS:
                self._last_press_time = current_time
        else:
            press_duration = current_time - self._last_press_time
            if self._last_press_time > 0 and press_duration > self.DEBOUNCE_MS:
                logger.info(f"Button released after {press_duration:.0f}ms")
                if press_duration >= self.LONG_PRESS_MS:
                    logger.warning("Long press detected. Triggering factory reset.")
                    threading.Thread(target=self._perform_reset).start()
                else:
                    logger.info("Short press detected.")
                self._last_press_time = 0
                
    def _perform_reset(self):
        self.state_manager.reset()
        import subprocess
        logger.info("Restarting service after factory reset...")
        subprocess.Popen(["sudo", "systemctl", "restart", "photo-frame"])
