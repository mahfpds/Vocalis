#!/bin/bash
set -e

# One-command setup and start for RunPod GPU instances

# Create and activate venv if not already present
if [ ! -d "env" ]; then
  python3 -m venv env
fi
source env/bin/activate

# Install backend dependencies with CUDA
pip install -r backend/requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Start the backend server accessible on all interfaces
python -m backend.main
