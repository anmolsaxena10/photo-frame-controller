#!/bin/bash
set -e

echo "Building photo-frame-controller OS image..."

if [ ! -d "pi-gen" ]; then
  # Pin to bookworm branch — master now defaults to Trixie which requires
  # qemu-user-binfmt (conflicts with qemu-user-static on Ubuntu 22.04 CI).
  git clone --branch bookworm https://github.com/RPi-Distro/pi-gen.git
fi

cd pi-gen

rm -rf photo-frame
cp -r ../stage-photo-frame photo-frame
cp ../config config

# PI-GEN PATTERN: Put files at the stage root, so any substage can access them via ${STAGE_DIR}/files/
mkdir -p photo-frame/files/photo-frame-controller
cp -r ../../app photo-frame/files/photo-frame-controller/
cp ../../requirements.txt photo-frame/files/photo-frame-controller/
cp -r ../../config photo-frame/files/photo-frame-controller/
cp -r ../../data photo-frame/files/photo-frame-controller/

# Copy the systemd service file to the stage root files/ directory
cp ../../service/photo-frame-controller.service photo-frame/files/

# CONTINUE=1 allows pi-gen to resume from the last completed stage if the work dir is preserved
CONTINUE=1 ./build.sh

