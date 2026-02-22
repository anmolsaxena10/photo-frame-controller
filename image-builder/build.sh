#!/bin/bash
set -e

echo "Building photo-frame-controller OS image..."

# Clone pi-gen if not present
if [ ! -d "pi-gen" ]; then
  git clone https://github.com/RPi-Distro/pi-gen.git
fi

cd pi-gen

# Remove previous custom stage
rm -rf photo-frame

# Copy our stage
cp -r ../stage-photo-frame photo-frame

# Copy config
cp ../config config

# Copy application source into stage
mkdir -p photo-frame/files/photo-frame-controller
cp -r ../../app photo-frame/files/photo-frame-controller/
cp ../../requirements.txt photo-frame/files/photo-frame-controller/
cp -r ../../config photo-frame/files/photo-frame-controller/
cp -r ../../service photo-frame/files/photo-frame-controller/

# Build image
sudo ./build.sh

echo "Build complete."
