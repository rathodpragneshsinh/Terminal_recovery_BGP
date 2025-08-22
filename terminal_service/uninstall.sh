#!/usr/bin/bash

# Run main.py as service
systemctl disable terminal
systemctl stop terminal
rm /etc/systemd/system/terminal.service
systemctl daemon-reload

# Enable log rotation
rm /etc/logrotate.d/terminal.logrotate
