#!/bin/bash
set -e

echo "Installing photo-frame-controller..."

mkdir -p "${ROOTFS_DIR}/opt"

cp -r "${STAGE_DIR}/files/photo-frame-controller" \
      "${ROOTFS_DIR}/opt/"

chown -R 1000:1000 "${ROOTFS_DIR}/opt/photo-frame-controller"

on_chroot << EOF
cd /opt/photo-frame-controller
python3 -m venv venv
/opt/photo-frame-controller/venv/bin/pip install -r requirements.txt
systemctl enable bluetooth
EOF
