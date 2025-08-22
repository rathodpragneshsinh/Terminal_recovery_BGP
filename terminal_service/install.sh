#!/usr/bin/bash

# Run main.py as service
cp terminal.service /etc/systemd/system/terminal.service
systemctl daemon-reload
systemctl enable tga
systemctl start tga

# Enable log rotation
cp terminal.logrotate /etc/logrotate.d/terminal.logrotate
