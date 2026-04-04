#!/bin/bash
set -e

echo "Building photo-frame-controller OS image..."

if [ ! -d "pi-gen" ]; then
  git clone https://github.com/RPi-Distro/pi-gen.git
fi

cd pi-gen

rm -rf photo-frame
cp -r ../stage-photo-frame photo-frame
cp ../config config

# Bundle application files into the substage's files directory
mkdir -p photo-frame/00-install/files/photo-frame-controller
cp -r ../../app photo-frame/00-install/files/photo-frame-controller/
cp ../../requirements.txt photo-frame/00-install/files/photo-frame-controller/
cp -r ../../config photo-frame/00-install/files/photo-frame-controller/
cp -r ../../data photo-frame/00-install/files/photo-frame-controller/

# Copy the systemd service file directly into files/ for easy reference
cp ../../service/photo-frame-controller.service photo-frame/00-install/files/

./build.sh
