#!/bin/bash

# Start Xvfb
Xvfb :99 -ac -screen 0 1280x1024x16 &

# Set display environment variable
export DISPLAY=:99

# Wait for a few seconds to ensure Chrome starts
sleep 5

# Execute Python script
python /work/scrap.py

# Keep the container running
/bin/bash
