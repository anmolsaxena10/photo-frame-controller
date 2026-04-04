#!/bin/bash
set -e

echo "Installing photo-frame-controller..."

# Copy application files into the image
mkdir -p "${ROOTFS_DIR}/opt"
cp -r "${STAGE_DIR}/files/photo-frame-controller" "${ROOTFS_DIR}/opt/"
chown -R 1000:1000 "${ROOTFS_DIR}/opt/photo-frame-controller"

# Ensure systemd directory exists before installing the service
mkdir -p "${ROOTFS_DIR}/etc/systemd/system"

# Use the STAGE_DIR variable to access the service file from the stage's root files/
install -m 644 \
  "${STAGE_DIR}/files/photo-frame-controller.service" \
  "${ROOTFS_DIR}/etc/systemd/system/photo-frame-controller.service"

# Handle SPI for the Waveshare display HAT.
# For Bookworm, the boot directory is mounted at /boot/firmware.
if [ -d "${ROOTFS_DIR}/boot/firmware" ]; then
  CONFIG_FILE="${ROOTFS_DIR}/boot/firmware/config.txt"
else
  CONFIG_FILE="${ROOTFS_DIR}/boot/config.txt"
fi

# Enable SPI by adding it to config.txt if not already present
if ! grep -q "dtparam=spi=on" "${CONFIG_FILE}"; then
  echo "dtparam=spi=on" >> "${CONFIG_FILE}"
fi

# Run setup commands inside the image rootfs
on_chroot << EOF
cd /opt/photo-frame-controller
python3 -m venv venv
/opt/photo-frame-controller/venv/bin/pip install -r requirements.txt
systemctl enable bluetooth
systemctl daemon-reload
systemctl enable photo-frame-controller
EOF
