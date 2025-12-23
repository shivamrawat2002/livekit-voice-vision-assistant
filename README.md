# LiveKit Voice & Vision Assistant

A real-time multimodal AI assistant capable of understanding speech, responding with natural voice, and analyzing live video input.  
The system is built using LiveKit for real-time communication, llm for reasoning, Deepgram for speech-to-text, and OpenAI Text-to-Speech for audio responses.

This project demonstrates how voice, vision, and large language models can be combined to build interactive, low-latency AI systems.

---

## Overview

The LiveKit Voice & Vision Assistant is designed to operate inside live audio and video rooms.  
It listens to users in real time, understands their intent, and responds using spoken language.  
When a user asks a question that requires visual understanding, the assistant processes frames from the camera feed and uses them as context to generate accurate responses.

Unlike traditional chatbots, this assistant works continuously in a live environment and adapts its behavior based on both audio and visual input.

---

## Key Capabilities

- Real-time speech recognition using Deepgram  
- Natural voice responses using OpenAI Text-to-Speech  
- Vision-based reasoning using live camera frames  
- Automatic detection of when visual context is required  
- Low-latency audio and video streaming via LiveKit  
- Graceful handling of camera availability and room disconnects  
- Modular and extensible architecture for future enhancements  

---

## How It Works

1. The user joins a LiveKit room with microphone and camera enabled.  
2. Audio input is processed through voice activity detection and speech-to-text.  
3. The transcribed text is sent to the language model.  
4. If the model determines that visual context is needed, a frame from the live video stream is attached to the request.  
5. The language model generates a response using both text and image context.  
6. The response is converted to speech and played back to the user in real time.  

---

## Real-World Applications

- Virtual assistants for video conferencing platforms  
- Remote support and troubleshooting systems  
- Smart kiosks and interactive terminals  
- Assistive technology for accessibility use cases  
- Real-time training and onboarding tools  
- AI companions for live demonstrations or presentations  

---

## Technology Stack

- LiveKit – Real-time audio and video streaming  
- GPT-4o – Multimodal language model  
- Deepgram – Speech-to-text  
- OpenAI Text-to-Speech – Voice responses  
- Silero VAD – Voice activity detection  
- Python – Core implementation language  

---

## Setup and Usage

```bash
git https://github.com/shivamrawat2002/livekit-voice-vision-assistant
cd livekit-voice-vision-assistant
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python assistant.py download-files
python assistant.py start
```

---

## License

MIT License

Copyright (c) 2025
