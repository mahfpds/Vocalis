# Quick Setup Commands - Copy & Paste

## Essential Setup (Run these in order)

### 1. Install Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv nodejs npm ffmpeg curl wget unzip
```

### 2. Install ngrok
```bash
cd /tmp
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/
```

**Get ngrok token from https://ngrok.com, then:**
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

### 3. Setup Vocalis
```bash
cd /workspace
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
cd frontend && npm install && cd ..
```

### 4. Install AI Services
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
sleep 5
ollama pull llama3.1:8b

# Install TTS
cd /tmp
git clone https://github.com/erew123/alltalk_tts.git
cd alltalk_tts
pip install -r requirements.txt
python server.py --host 0.0.0.0 --port 5005 &
```

### 5. Configure Environment
```bash
cd /workspace
cat > .env << 'EOF'
LLM_API_ENDPOINT=http://127.0.0.1:11434/v1/chat/completions
TTS_API_ENDPOINT=http://localhost:5005/v1/audio/speech
TTS_MODEL=tts-1
TTS_VOICE=female
TTS_FORMAT=wav
WHISPER_MODEL=base.en
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8000
VAD_THRESHOLD=0.5
VAD_BUFFER_SIZE=30
AUDIO_SAMPLE_RATE=48000
EOF
```

## Start Services (3 Terminal Tabs)

### Tab 1: Backend
```bash
cd /workspace
source env/bin/activate
python -m backend.main
```

### Tab 2: Frontend
```bash
cd /workspace/frontend
npm start
```

### Tab 3: ngrok
```bash
ngrok http 8000 --region=us &
ngrok http 3000 --region=us &
ngrok tunnel list
```

## One-Command Startup Script
```bash
cat > /workspace/start_vocalis.sh << 'EOF'
#!/bin/bash
cd /workspace
source env/bin/activate
ollama serve &
sleep 5
cd /tmp/alltalk_tts
python server.py --host 0.0.0.0 --port 5005 &
sleep 10
cd /workspace
python -m backend.main &
sleep 5
cd frontend
npm start &
cd ..
ngrok http 8000 --region=us &
ngrok http 3000 --region=us &
echo "Services started! Check ngrok tunnels:"
sleep 3
ngrok tunnel list
EOF

chmod +x /workspace/start_vocalis.sh
```

**Then just run:** `./start_vocalis.sh`

## Quick Test Commands
```bash
# Test GPU
nvidia-smi

# Test LLM
curl -X POST http://127.0.0.1:11434/v1/chat/completions -H "Content-Type: application/json" -d '{"model": "llama3.1:8b", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 50}'

# Test TTS
curl -X POST http://localhost:5005/v1/audio/speech -H "Content-Type: application/json" -d '{"model": "tts-1", "input": "Hello world", "voice": "female"}' --output test.wav
```

## Access URLs
- **Frontend**: `https://YOUR_NGROK_URL.ngrok.io` (port 3000)
- **Backend**: `https://YOUR_NGROK_URL.ngrok.io` (port 8000)

## Quick Troubleshooting
```bash
# Restart Ollama
pkill ollama && ollama serve &

# Check running services
ps aux | grep -E "(ollama|python|npm)"

# Monitor GPU
watch -n 1 nvidia-smi
```