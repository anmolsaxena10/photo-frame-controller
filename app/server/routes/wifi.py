from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import logging
import subprocess
import time
import threading

logger = logging.getLogger(__name__)
router = APIRouter()


class WifiCredentials(BaseModel):
    ssid: str
    password: str


class WifiScanResult(BaseModel):
    ssid: str
    signal: int
    security: str


@router.get("/scan")
async def scan_networks():
    """Scan for available WiFi networks using iw (works even in AP mode)."""
    try:
        # iw can scan while hostapd is running (triggers an off-channel scan)
        # First try with iw
        result = subprocess.run(
            ["iw", "dev", "wlan0", "scan", "ap-force"],
            capture_output=True, text=True, timeout=20
        )
        
        if result.returncode != 0:
            # Fallback: try a scan dump (use cached results)
            result = subprocess.run(
                ["iw", "dev", "wlan0", "scan", "dump"],
                capture_output=True, text=True, timeout=10
            )
        
        networks = []
        seen = set()
        current_ssid = None
        current_signal = 0
        current_security = "Open"
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith("BSS "):
                # Save previous entry
                if current_ssid and current_ssid not in seen:
                    seen.add(current_ssid)
                    networks.append({
                        "ssid": current_ssid,
                        "signal": current_signal,
                        "security": current_security
                    })
                current_ssid = None
                current_signal = 0
                current_security = "Open"
            elif line.startswith("SSID:"):
                current_ssid = line[5:].strip()
            elif line.startswith("signal:"):
                # Convert dBm to percentage (rough approximation)
                try:
                    dbm = float(line.split()[1])
                    current_signal = max(0, min(100, int(2 * (dbm + 100))))
                except (ValueError, IndexError):
                    current_signal = 0
            elif "WPA" in line or "RSN" in line:
                current_security = "WPA"
        
        # Don't forget the last entry
        if current_ssid and current_ssid not in seen:
            seen.add(current_ssid)
            networks.append({
                "ssid": current_ssid,
                "signal": current_signal,
                "security": current_security
            })
        
        # Sort by signal strength
        networks.sort(key=lambda x: x["signal"], reverse=True)
        return {"networks": networks}
    except Exception as e:
        logger.error(f"WiFi scan failed: {e}")
        return {"networks": []}


@router.post("/connect")
async def connect_wifi(creds: WifiCredentials, request: Request):
    """Connect to a WiFi network: stop AP, connect via nmcli, update state."""
    state_manager = request.app.state.state_manager

    logger.info(f"Attempting to connect to WiFi: {creds.ssid}")

    try:
        # 1. Stop AP mode (hostapd and dnsmasq)
        subprocess.run(["pkill", "hostapd"], check=False)
        subprocess.run(["pkill", "-f", "dnsmasq.*photoframe"], check=False)
        time.sleep(1)
        
        # 2. Remove the static AP IP
        subprocess.run(["ip", "addr", "flush", "dev", "wlan0"], check=False)
        subprocess.run(["ip", "link", "set", "dev", "wlan0", "down"], check=False)
        time.sleep(0.5)
        subprocess.run(["ip", "link", "set", "dev", "wlan0", "up"], check=False)
        
        # 3. Hand the interface back to NetworkManager
        subprocess.run(["nmcli", "device", "set", "wlan0", "managed", "yes"], check=False)
        time.sleep(2)
        
        # 4. Trigger a rescan and wait for results
        subprocess.run(["nmcli", "device", "wifi", "rescan", "ifname", "wlan0"], check=False)
        time.sleep(5)  # Give NM time to scan and find networks
        
        # 5. Connect to the specified network
        result = subprocess.run(
            ["nmcli", "dev", "wifi", "connect", creds.ssid, "password", creds.password, "ifname", "wlan0"],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            logger.error(f"WiFi connection failed: {error_msg}")
            
            # Restart AP since connection failed
            threading.Thread(target=_restart_ap_on_failure, daemon=True).start()
            raise HTTPException(status_code=400, detail=f"Connection failed: {error_msg}")

        # 6. Update state
        state = state_manager.get_state()
        state.first_boot = False
        state.wifi_configured = True
        state.wifi_ssid = creds.ssid
        state_manager.save()

        # 7. Schedule service restart in background (gives time for response to reach client)
        def delayed_restart():
            time.sleep(5)
            logger.info("WiFi configured. Restarting service...")
            subprocess.run(["systemctl", "restart", "photo-frame-controller"], check=False)

        threading.Thread(target=delayed_restart, daemon=True).start()

        return {"success": True, "message": f"Connected to {creds.ssid}. The frame will restart shortly."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WiFi connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _restart_ap_on_failure():
    """If WiFi connection fails, restart the service to bring AP back up."""
    time.sleep(2)
    subprocess.run(["systemctl", "restart", "photo-frame-controller"], check=False)


@router.get("/status")
async def wifi_status(request: Request):
    """Get current WiFi connection status."""
    state_manager = request.app.state.state_manager
    state = state_manager.get_state()

    connected_ssid = None
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split('\n'):
            if line.startswith("yes:"):
                connected_ssid = line.split(":", 1)[1]
                break
    except Exception:
        pass

    return {
        "configured": state.wifi_configured,
        "ssid": state.wifi_ssid,
        "connected_ssid": connected_ssid,
        "mode": state_manager.current_mode.value
    }
