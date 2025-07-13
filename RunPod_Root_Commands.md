# Vocalis Setup Commands for RunPod (Root User)

## Step 1: Install Dependencies
```bash
apt update && apt upgrade -y
apt install -y git python3 python3-pip python3-venv nodejs npm ffmpeg curl wget unzip
```

## Step 2: Install ngrok
```bash
cd /tmp
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xzf ngrok-v3-stable-linux-amd64.tgz
mv ngrok /usr/local/bin/
ngrok version
```

**Get your ngrok token from https://ngrok.com, then:**
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

## Step 3: Verify CUDA and Setup Vocalis
```bash
# Check GPU
nvidia-smi

# Setup Vocalis
cd /workspace
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install frontend dependencies
cd frontend
npm install
cd ..
```

## Step 4: Install AI Services
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &

# Wait for service to start
sleep 5

# Download model (this will take a few minutes)
ollama pull llama3.1:8b

# Verify model is available
ollama list
```

## Step 5: Install TTS Service
```bash
# Install AllTalk TTS
cd /tmp
git clone https://github.com/erew123/alltalk_tts.git
cd alltalk_tts
pip install -r requirements.txt

# Start TTS server
python server.py --host 0.0.0.0 --port 5005 &

# Wait for TTS to start
sleep 10
```

## Step 6: Configure Environment
```bash
cd /workspace

# Create .env file
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

## Step 7: Test Services
```bash
# Test LLM
curl -X POST http://127.0.0.1:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.1:8b", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 50}'

# Test TTS
curl -X POST http://localhost:5005/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "tts-1", "input": "Hello world", "voice": "female"}' \
  --output test.wav
```

## Step 8: Start Vocalis (Need 3 Terminal Tabs)

### Terminal Tab 1: Backend
```bash
cd /workspace
source env/bin/activate
python -m backend.main
```

### Terminal Tab 2: Frontend
```bash
cd /workspace/frontend
npm start
```

### Terminal Tab 3: ngrok
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

# Start Ollama
ollama serve &
sleep 5

# Start TTS
cd /tmp/alltalk_tts
python server.py --host 0.0.0.0 --port 5005 &
sleep 10

# Start Vocalis backend
cd /workspace
python -m backend.main &
sleep 5

# Start frontend
cd frontend
npm start &
cd ..

# Start ngrok
ngrok http 8000 --region=us &
ngrok http 3000 --region=us &

echo "Services started! Check ngrok tunnels:"
sleep 3
ngrok tunnel list
EOF

chmod +x /workspace/start_vocalis.sh
```

**Then run:** `./start_vocalis.sh`

## Quick Status Checks
```bash
# Check GPU usage
nvidia-smi

# Check running services
ps aux | grep -E "(ollama|python|npm)"

# Check ports
netstat -tulpn | grep -E "(8000|3000|5005|11434)"
```

## Access Your App
After ngrok starts, you'll see URLs like:
- **Frontend (use this)**: `https://abc123.ngrok.io`
- **Backend API**: `https://def456.ngrok.io`

Open the frontend URL in your browser to test the speech-to-speech system!