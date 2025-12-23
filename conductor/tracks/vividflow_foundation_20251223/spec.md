# Track Spec: VividFlow Foundation & Prompt Enhancement

## Overview
This track focuses on establishing the core visual identity of "VividFlow" and adding an AI-powered prompt enhancement feature using the Groq API.

## Goals
- Refresh the web interface with a Deep Charcoal/Electric Purple "Studio" theme.
- Implement Glassmorphism and modern UI components.
- Integrate Groq API (Llama-3/Qwen) to expand simple user prompts into cinematic descriptions.
- Provide a seamless user experience during the prompt enhancement and video generation phases.

## Requirements
### Visual Identity (VividFlow)
- **Color Palette:** Deep Charcoal/OLED Black (#000000 or #121212) with Electric Purple (#A855F7) accents.
- **Glassmorphism:** Use translucent backgrounds with backdrop-filter: blur for UI panels.
- **Micro-interactions:** Subtle glows and hover effects on buttons and interactive elements.
- **Live Progress:** Glowing/Building animations during generation wait times.

### Prompt Enhancement (Groq)
- **Groq Integration:** Use Groq API for fast LLM inference.
- **Prompt Expansion:** Transform a short input (e.g., "running man") into a detailed cinematic prompt (e.g., "A high-octane cinematic shot of a man running through a neon-lit cyberpunk city, rain droplets glistening on his leather jacket, motion blur, 8k resolution").
- **UI Integration:** A button in the web interface to "Enhance" the current prompt.
- **Visual Feedback:** Show a loading state while the prompt is being enhanced.

## Technical Details
- **Backend:** Flask (web_app.py) update to handle Groq API requests.
- **Frontend:** index.html and CSS updates.
- **Environment:** GROQ_API_KEY in .env.client.
