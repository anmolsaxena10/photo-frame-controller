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

mkdir -p photo-frame/files/photo-frame-controller
cp -r ../../app photo-frame/files/photo-frame-controller/
cp ../../requirements.txt photo-frame/files/photo-frame-controller/
cp -r ../../config photo-frame/files/photo-frame-controller/
cp -r ../../service photo-frame/files/photo-frame-controller/

echo "Starting pi-gen Docker build..."

sudo ./build-docker.sh
