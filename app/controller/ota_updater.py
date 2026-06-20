import httpx
import os
import zipfile
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)

class OTAUpdater:
    def __init__(self, repo="saxanmol/photo-frame-controller", state_manager=None):
        self.repo = repo
        self.state_manager = state_manager
        # GitHub API URL for latest release
        self.api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"
        
    async def check_for_updates(self) -> dict:
        """Query GitHub API for latest release. Return version info."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.api_url)
                response.raise_for_status()
                data = response.json()
                
                latest_version = data.get("tag_name", "1.0.0").lstrip("v")
                current_version = "1.0.0"
                if self.state_manager:
                    current_version = self.state_manager.get_state().ota.current_version
                    
                update_available = latest_version != current_version
                
                # Find the zip asset
                assets = data.get("assets", [])
                zip_url = None
                for asset in assets:
                    if asset.get("name", "").endswith(".zip"):
                        zip_url = asset.get("browser_download_url")
                        break
                        
                # If no specific asset, fallback to the zipball_url
                if not zip_url:
                    zip_url = data.get("zipball_url")
                
                return {
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "update_available": update_available,
                    "download_url": zip_url
                }
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return {"error": str(e), "update_available": False}
            
    async def download_and_apply(self, artifact_url: str, new_version: str = None) -> bool:
        """Download zip, extract, copy over /opt/photo-frame-controller, and restart."""
        if not artifact_url:
            logger.error("No download URL provided for update.")
            return False
            
        logger.info(f"Downloading update from {artifact_url}")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, "update.zip")
                extract_path = os.path.join(temp_dir, "extracted")
                os.makedirs(extract_path, exist_ok=True)
                
                # Download
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    async with client.stream('GET', artifact_url) as response:
                        response.raise_for_status()
                        with open(zip_path, 'wb') as f:
                            async for chunk in response.aiter_bytes():
                                f.write(chunk)
                                
                # Extract
                logger.info("Extracting update...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                    
                # Find the root of the extracted project
                extracted_dirs = os.listdir(extract_path)
                source_dir = extract_path
                if len(extracted_dirs) == 1 and os.path.isdir(os.path.join(extract_path, extracted_dirs[0])):
                    source_dir = os.path.join(extract_path, extracted_dirs[0])
                
                # Replace logic
                logger.info("Applying update...")
                target_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                
                # Make sure rsync is available on the system
                # Exclude data, config overrides, and venv
                subprocess.run([
                    "rsync", "-a", 
                    "--exclude=data/", 
                    "--exclude=config/default-state.json", 
                    "--exclude=venv/", 
                    "--exclude=.git/",
                    f"{source_dir}/", 
                    f"{target_dir}/"
                ], check=True)
                
                logger.info("Update applied successfully.")
                
                if self.state_manager:
                    state = self.state_manager.get_state()
                    state.ota.mandatory_initial_done = True
                    if new_version:
                        state.ota.current_version = new_version
                    self.state_manager.save()
                
                # Restart the systemd service
                # Note: The service name in the user's README is 'photo-frame'
                logger.info("Restarting service...")
                subprocess.Popen(["sudo", "systemctl", "restart", "photo-frame"])
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to apply update: {e}")
            return False
