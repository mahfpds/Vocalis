# Vocalis RunPod Web Terminal Setup - Exact Instructions

## Prerequisites
- RunPod instance with H100 GPU
- Access to RunPod web terminal
- Your computer with internet access

## Step 1: System Setup and Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git python3 python3-pip python3-venv nodejs npm ffmpeg curl wget unzip

# Verify CUDA is available
nvidia-smi
python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

## Step 2: Install ngrok for External Access

```bash
# Download and install ngrok
cd /tmp
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Verify installation
ngrok version
```

**Note**: You'll need to sign up at https://ngrok.com and get your auth token. Then run:
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

## Step 3: Clone and Setup Vocalis

```bash
# Go to workspace directory
cd /workspace

# Clone the repository (assuming it's already in the workspace)
# If not, you would run: git clone <your-repo-url>

# Make scripts executable
chmod +x setup.sh run.sh install-deps.sh

# Create and activate virtual environment
python3 -m venv env
source env/bin/activate

# Install Python dependencies with CUDA support
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install frontend dependencies
cd frontend
npm install
cd ..
```

## Step 4: Setup Local AI Services

### Install and Configure Ollama (for LLM)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service in background
ollama serve &

# Wait a moment for service to start
sleep 5

# Download a model (this will take a few minutes)
ollama pull llama3.1:8b

# Verify the model is available
ollama list
```

### Setup TTS Service (AllTalk TTS - OpenAI Compatible)

```bash
# Install AllTalk TTS (OpenAI compatible TTS server)
cd /tmp
git clone https://github.com/erew123/alltalk_tts.git
cd alltalk_tts
pip install -r requirements.txt

# Start AllTalk TTS server in background
python server.py --host 0.0.0.0 --port 5005 &

# Wait for TTS server to start
sleep 10
```

## Step 5: Configure Environment Variables

```bash
# Go back to Vocalis directory
cd /workspace

# Create .env file with configuration
cat > .env << 'EOF'
# LLM Configuration (Ollama)
LLM_API_ENDPOINT=http://127.0.0.1:11434/v1/chat/completions

# TTS Configuration (AllTalk)
TTS_API_ENDPOINT=http://localhost:5005/v1/audio/speech
TTS_MODEL=tts-1
TTS_VOICE=female
TTS_FORMAT=wav

# Whisper Configuration (STT)
WHISPER_MODEL=base.en

# Server Configuration
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8000

# Audio Processing
VAD_THRESHOLD=0.5
VAD_BUFFER_SIZE=30
AUDIO_SAMPLE_RATE=48000
EOF
```

## Step 6: Test Services Before Starting

```bash
# Activate environment
source env/bin/activate

# Test Ollama LLM
curl -X POST http://127.0.0.1:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'

# Test TTS service
curl -X POST http://localhost:5005/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello world",
    "voice": "female"
  }' --output test.wav

# If both work, you're ready to proceed
```

## Step 7: Start Vocalis Services

### Terminal 1: Backend Server
```bash
cd /workspace
source env/bin/activate
python -m backend.main
```

### Terminal 2: Frontend Server (open new terminal tab)
```bash
cd /workspace/frontend
npm start
```

### Terminal 3: ngrok Setup (open new terminal tab)
```bash
# Expose backend (port 8000)
ngrok http 8000 --region=us &

# Expose frontend (port 3000) 
ngrok http 3000 --region=us &

# Show running tunnels
ngrok tunnel list
```

## Step 8: Access from Your Computer

After running ngrok, you'll see output like:
```
https://abc123.ngrok.io -> http://localhost:3000
https://def456.ngrok.io -> http://localhost:8000
```

1. **Frontend Access**: Open the first ngrok URL (port 3000) in your browser
2. **Backend API**: The second URL (port 8000) is for the backend API

## Step 9: Alternative All-in-One Script

Create a startup script for easier launching:

```bash
cat > start_vocalis.sh << 'EOF'
#!/bin/bash
cd /workspace
source env/bin/activate

# Start services in background
ollama serve &
sleep 5

# Start TTS server
cd /tmp/alltalk_tts
python server.py --host 0.0.0.0 --port 5005 &
sleep 10

# Go back to Vocalis
cd /workspace

# Start backend
python -m backend.main &
sleep 5

# Start frontend
cd frontend
npm start &

# Start ngrok tunnels
ngrok http 8000 --region=us &
ngrok http 3000 --region=us &

echo "Services started! Check ngrok tunnels:"
sleep 3
ngrok tunnel list
EOF

chmod +x start_vocalis.sh
```

Then simply run:
```bash
./start_vocalis.sh
```

## Step 10: Verification and Testing

1. **Check GPU Usage**: `nvidia-smi` should show GPU memory usage
2. **Test Speech-to-Text**: Use the frontend to record audio
3. **Test LLM**: Send a message and verify response
4. **Test TTS**: Ensure audio response is generated

## Troubleshooting

### If Ollama fails to start:
```bash
# Check if already running
ps aux | grep ollama
# Kill if needed
pkill ollama
# Restart
ollama serve &
```

### If TTS fails:
```bash
# Alternative TTS setup using Coqui TTS
pip install coqui-tts
tts-server --model_name tts_models/en/ljspeech/tacotron2-DDC --port 5005
```

### If ngrok fails:
```bash
# Check your auth token
ngrok config check
# Re-add token if needed
ngrok config add-authtoken YOUR_TOKEN
```

### If CUDA not working:
```bash
# Verify CUDA installation
nvcc --version
# Reinstall PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 --force-reinstall
```

## Performance Monitoring

```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor system resources
htop

# Check service logs
journalctl -f
```

## Notes

- The H100 GPU will be automatically used by all components that support CUDA
- First model downloads may take 5-10 minutes depending on internet speed
- Expected total setup time: 15-20 minutes
- Memory usage should be well within H100's 80GB capacity
- Response times should be very fast with H100 acceleration

Your Vocalis system will be accessible from any computer via the ngrok URLs!