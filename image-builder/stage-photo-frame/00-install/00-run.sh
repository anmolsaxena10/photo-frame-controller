#!/bin/bash
set -e

echo "Installing photo-frame-controller..."

# Copy application files into the image
mkdir -p "${ROOTFS_DIR}/opt"
cp -r files/photo-frame-controller "${ROOTFS_DIR}/opt/"
chown -R 1000:1000 "${ROOTFS_DIR}/opt/photo-frame-controller"

# Install systemd service
install -m 644 \
  files/photo-frame-controller.service \
  "${ROOTFS_DIR}/etc/systemd/system/photo-frame-controller.service"

# Enable SPI for the Waveshare E-Ink display HAT
echo "dtparam=spi=on" >> "${ROOTFS_DIR}/boot/firmware/config.txt"

on_chroot << EOF
cd /opt/photo-frame-controller
python3 -m venv venv
/opt/photo-frame-controller/venv/bin/pip install -r requirements.txt
systemctl enable bluetooth
systemctl daemon-reload
systemctl enable photo-frame-controller
EOF
