import subprocess
import logging
import os
import random
import string

logger = logging.getLogger(__name__)

class WiFiManager:
    def __init__(self):
        self.interface = "wlan0"
        self.ap_ip = "192.168.4.1"
        
    def generate_ssid(self) -> str:
        try:
            with open("/sys/class/net/wlan0/address") as f:
                mac = f.read().strip().replace(":", "")
                return f"PhotoFrame-{mac[-4:].upper()}"
        except Exception:
            return f"PhotoFrame-{random.randint(1000, 9999)}"
            
    def generate_password(self, length=8) -> str:
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
        
    def start_ap_mode(self):
        ssid = self.generate_ssid()
        password = self.generate_password()
        
        logger.info(f"Starting AP Mode: {ssid}")
        
        # Stop NetworkManager from managing the interface while hostapd runs
        subprocess.run(["nmcli", "device", "set", self.interface, "managed", "no"], check=False)
        
        # Configure IP address
        subprocess.run(["ip", "link", "set", "dev", self.interface, "up"], check=False)
        subprocess.run(["ip", "addr", "add", f"{self.ap_ip}/24", "dev", self.interface], check=False)
        
        # Write dnsmasq conf
        dnsmasq_conf = f"""
interface={self.interface}
dhcp-range=192.168.4.10,192.168.4.50,255.255.255.0,24h
address=/#/{self.ap_ip}
"""
        with open("/tmp/photoframe_dnsmasq.conf", "w") as f:
            f.write(dnsmasq_conf)
            
        # Write hostapd conf
        hostapd_conf = f"""
interface={self.interface}
driver=nl80211
ssid={ssid}
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
        with open("/tmp/photoframe_hostapd.conf", "w") as f:
            f.write(hostapd_conf)
            
        # Kill existing instances if any
        subprocess.run(["pkill", "dnsmasq"], check=False)
        subprocess.run(["pkill", "hostapd"], check=False)
        
        # Start dnsmasq and hostapd
        subprocess.Popen(["dnsmasq", "-C", "/tmp/photoframe_dnsmasq.conf", "-d"])
        subprocess.Popen(["hostapd", "/tmp/photoframe_hostapd.conf"])
        
        logger.info("AP Mode started.")
        return ssid, password
