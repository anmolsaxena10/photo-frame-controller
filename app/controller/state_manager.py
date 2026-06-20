import os
import json
import shutil
import threading
import logging

from app.server.schemas import AppStateModel, FrameState

# Calculate absolute paths based on this file's location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
DATA_DIR = os.path.join(BASE_DIR, "data")

DEFAULT_STATE_FILE = os.path.join(CONFIG_DIR, "default-state.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")

logger = logging.getLogger(__name__)

class StateManager:
    """
    Manages the persistent application state and current runtime mode.
    Handles thread-safe reading and writing to state.json.
    """
    
    def __init__(self):
        self.state_model: AppStateModel = None
        self.current_mode: FrameState = FrameState.FIRST_BOOT
        self._lock = threading.Lock()
        
    def initialize(self) -> None:
        """Load state from disk or create from default."""
        os.makedirs(DATA_DIR, exist_ok=True)
        
        with self._lock:
            if not os.path.exists(STATE_FILE):
                if os.path.exists(DEFAULT_STATE_FILE):
                    logger.info("Initializing state from default-state.json")
                    shutil.copyfile(DEFAULT_STATE_FILE, STATE_FILE)
                else:
                    logger.warning("default-state.json not found, creating empty state.")
                    self.state_model = AppStateModel()
                    self._write_unlocked()
            
            # Load state
            if self.state_model is None:
                try:
                    with open(STATE_FILE, "r") as f:
                        data = json.load(f)
                        self.state_model = AppStateModel(**data)
                except Exception as e:
                    logger.error(f"Failed to load state.json: {e}. Reverting to default.")
                    if os.path.exists(DEFAULT_STATE_FILE):
                        shutil.copyfile(DEFAULT_STATE_FILE, STATE_FILE)
                        with open(STATE_FILE, "r") as f:
                            self.state_model = AppStateModel(**json.load(f))
                    else:
                        self.state_model = AppStateModel()
            
            # Determine runtime mode based on state
            if self.state_model.first_boot:
                self.current_mode = FrameState.FIRST_BOOT
            elif self.state_model.wifi_configured:
                self.current_mode = FrameState.CONFIGURED
            else:
                self.current_mode = FrameState.AP_SETUP
                
    def get_state(self) -> AppStateModel:
        """Returns the current state model."""
        with self._lock:
            # We return the object directly. In a high-concurrency 
            # environment we might want to return a copy.
            return self.state_model
            
    def save(self) -> None:
        """Persists the current state model to disk atomically."""
        with self._lock:
            self._write_unlocked()
            
    def _write_unlocked(self) -> None:
        temp_file = STATE_FILE + ".tmp"
        with open(temp_file, "w") as f:
            f.write(self.state_model.model_dump_json(indent=2))
        os.replace(temp_file, STATE_FILE)
        
    def transition_to(self, mode: FrameState) -> None:
        """Change the current runtime mode."""
        logger.info(f"Transitioning from {self.current_mode.value} to {mode.value}")
        self.current_mode = mode
        
    def reset(self) -> None:
        """Factory reset: clear data and revert state to default."""
        logger.warning("Performing factory reset...")
        with self._lock:
            if os.path.exists(DEFAULT_STATE_FILE):
                shutil.copyfile(DEFAULT_STATE_FILE, STATE_FILE)
            else:
                self.state_model = AppStateModel()
                self._write_unlocked()
                
            self.state_model = None
            
        # Clean up images
        img_dir = os.path.join(DATA_DIR, "images")
        proc_dir = os.path.join(DATA_DIR, "processed")
        thumb_dir = os.path.join(DATA_DIR, "thumbnails")
        
        for d in [img_dir, proc_dir, thumb_dir]:
            if os.path.exists(d):
                for f in os.listdir(d):
                    try:
                        os.remove(os.path.join(d, f))
                    except Exception as e:
                        logger.error(f"Failed to remove {f} during reset: {e}")
                        
        self.initialize()
