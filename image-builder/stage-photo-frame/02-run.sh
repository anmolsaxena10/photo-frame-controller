#!/bin/bash
set -e

echo "Installing systemd service..."

install -m 644 \
  "${STAGE_DIR}/files/photo-frame-controller.service" \
  "${ROOTFS_DIR}/etc/systemd/system/photo-frame-controller.service"

on_chroot << EOF
systemctl daemon-reload
systemctl enable photo-frame-controller
EOF
