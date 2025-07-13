# Vocalis Setup Guide for RunPod H100

## Overview

**Vocalis** is a sophisticated speech-to-speech AI assistant that provides real-time conversation capabilities with advanced features including:
- 🗣️ Speech-to-text (STT) transcription using Faster Whisper
- 🧠 Large Language Model (LLM) processing 
- 🔊 Text-to-speech (TTS) synthesis
- 🖼️ Vision/image analysis capabilities
- 🎯 Real-time barge-in interruption technology

## H100 GPU Acceleration

**YES**, the H100 chip will be utilized for all three main components:

### 1. **Speech-to-Text (STT)** - Faster Whisper
- Uses `faster-whisper` library with CUDA acceleration
- Automatically detects CUDA availability: `torch.cuda.is_available()`
- Supports compute types: `int8`, `int16`, `float16`, `float32`
- Model sizes: `tiny.en`, `base.en`, `small.en`, `medium.en`, `large`

### 2. **Large Language Model (LLM)**
- Expects a local LLM API endpoint (default: `http://127.0.0.1:1234/v1/chat/completions`)
- Compatible with OpenAI API format
- You'll need to run a local LLM server (e.g., llama.cpp, Ollama, vLLM)

### 3. **Text-to-Speech (TTS)**
- Expects a local TTS API endpoint (default: `http://localhost:5005/v1/audio/speech`)
- Compatible with OpenAI TTS API format
- You'll need to run a local TTS server (e.g., Coqui TTS, XTTS)

### 4. **Vision Processing**
- Uses SmolVLM-256M-Instruct model via Transformers library
- Supports CUDA acceleration through PyTorch

## RunPod Setup Instructions

### Step 1: Create RunPod Instance

1. **Select Template**: Choose an H100 instance with:
   - NVIDIA H100 (80GB VRAM recommended)
   - Ubuntu 22.04 or similar
   - CUDA 12.4+ support
   - At least 32GB RAM
   - 100GB+ storage

2. **Connect**: SSH into your RunPod instance

### Step 2: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y git python3 python3-pip python3-venv nodejs npm ffmpeg

# Verify CUDA installation
nvidia-smi
nvcc --version
```

### Step 3: Clone and Setup Vocalis

```bash
# Clone the repository
git clone <your-vocalis-repo-url>
cd vocalis

# Make scripts executable
chmod +x setup.sh run.sh

# Run setup (choose CUDA support when prompted)
./setup.sh
```

### Step 4: Configure Local AI Services

You'll need to set up local AI services. Here are recommended options:

#### Option A: Using Ollama (Recommended)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &

# Download a model (e.g., Llama 3.1 8B)
ollama pull llama3.1:8b

# The API will be available at: http://localhost:11434/v1/chat/completions
```

#### Option B: Using llama.cpp
```bash
# Clone and build llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make LLAMA_CUDA=1

# Download a model (e.g., Llama 3.1 8B GGUF)
# Run server
./llama-server -m /path/to/model.gguf --host 0.0.0.0 --port 1234
```

#### TTS Service Setup (Coqui TTS)
```bash
# Install Coqui TTS
pip install coqui-tts

# Start TTS server (you'll need to implement OpenAI-compatible API wrapper)
# Or use alternatives like XTTS-v2
```

### Step 5: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# LLM Configuration
LLM_API_ENDPOINT=http://127.0.0.1:11434/v1/chat/completions  # For Ollama
# LLM_API_ENDPOINT=http://127.0.0.1:1234/v1/chat/completions  # For llama.cpp

# TTS Configuration
TTS_API_ENDPOINT=http://localhost:5005/v1/audio/speech
TTS_MODEL=tts-1
TTS_VOICE=tara
TTS_FORMAT=wav

# Whisper Configuration (STT)
WHISPER_MODEL=base.en  # or large for better accuracy

# Server Configuration
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8000

# Audio Processing
VAD_THRESHOLD=0.5
VAD_BUFFER_SIZE=30
AUDIO_SAMPLE_RATE=48000
```

### Step 6: Start the Application

```bash
# Activate virtual environment
source env/bin/activate

# Start the application
./run.sh
```

This will start:
- Backend FastAPI server on port 8000
- Frontend React development server on port 3000

### Step 7: Access the Application

If running on RunPod:
1. Expose ports 3000 and 8000 in your RunPod configuration
2. Access via `https://<your-pod-id>-3000.proxy.runpod.net`

## GPU Memory Optimization

For H100 with 80GB VRAM:
- **Whisper Model**: 1-4GB (depending on model size)
- **LLM**: 8-40GB (depending on model size)
- **TTS**: 2-8GB (depending on text length)
- **Vision Model**: 1-2GB

**Total estimated usage**: 15-55GB (plenty of headroom for the H100)

## Performance Expectations

With H100 acceleration:
- **STT Latency**: 50-200ms (depending on Whisper model size)
- **LLM Response**: 20-100ms/token (depending on model size)
- **TTS Synthesis**: 100-500ms (depending on text length)
- **Overall Response**: Sub-second for typical interactions

## Troubleshooting

### Common Issues:

1. **CUDA Not Detected**:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **Missing Dependencies**:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
   ```

3. **Port Access Issues**:
   - Ensure RunPod ports are properly exposed
   - Check firewall settings

4. **Model Loading Issues**:
   - Verify VRAM availability: `nvidia-smi`
   - Check model file permissions

## Cost Optimization

- Use appropriate model sizes for your needs
- Consider using quantized models (int8/int16) for better performance
- Monitor GPU utilization to ensure efficient resource usage

## Conclusion

The H100 chip will significantly accelerate all three main components (STT, LLM, TTS) of the Vocalis system. The setup process involves configuring the base system, setting up local AI services, and ensuring proper GPU acceleration. With the H100's 80GB VRAM, you'll have plenty of headroom to run large, high-quality models for all components simultaneously.