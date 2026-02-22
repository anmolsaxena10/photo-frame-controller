# Overview

E-Ink Photo Frame Controller on RPi 

Photo frame - https://www.waveshare.com/wiki/7.3inch_e-Paper_HAT_(F)_Manual#Working_With_Raspberry_Pi 

Working example - https://github.com/waveshareteam/e-Paper/blob/master/RaspberryPi_JetsonNano/python/examples/epd_7in3f_test.py 

## Goals
1. First time start - Show a default image on the E-Ink display. 
2. First time setup - BLE Beacon so that an external App can connect.
3. First time setup - Get working mode from the App
   1. Offline - App will transfer a few images, store them locally and carousel through the photos. No wifi setup.
   2. Online - App will transfer wifi creds and server url, which will provide a new image everytime we hit it. 
4. Subsequent runs - The RPi should sleep after refrehsing the image, and periodically come online to refresh the image and fetch latest image from server if configured in that mode.
5. Reset - Clicking on the RPi button should reset the state and again beacon for setup. 
6. Eventually, have the setup in this repo that creates an OS image that can be flahsed directly.

# RPI Setup

## Deps
    sudo apt update
    sudo apt install -y python3-venv python3-pip git bluez
    
## BLE
    sudo systemctl enable bluetooth
    sudo systemctl start bluetooth

## Python Env
    cd /opt
    sudo git clone <your_repo> eink-frame
    cd eink-frame

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

## Service Setup
    sudo cp service/photo-frame.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable photo-frame
    sudo systemctl start photo-frame
