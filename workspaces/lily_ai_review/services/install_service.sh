#!/bin/bash

# Make the worker script executable
chmod +x worker_service.py

# Copy the service file to the systemd directory
sudo cp worker-service.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable worker-service.service

# Start the service
sudo systemctl start worker-service.service

# Check the status of the service
sudo systemctl status worker-service.service
