# Track Spec: Expose and Default CFG

## Overview
The user wants to control the CFG (Classifier-Free Guidance) scale directly from the web interface. The default value should be updated to 7.5.

## Goals
- Add a slider input for CFG in the web UI.
- Set the default value to 7.5.
- Pass the user-selected CFG value to the backend and the video generation client.

## Requirements
### UI
- **Input Type:** Range slider (step 0.5 or 0.1).
- **Label:** "Motion Guidance (CFG)" or similar user-friendly label.
- **Display:** Show the current value next to the slider.
- **Default:** 7.5.
- **Range:** 1.0 to 20.0 (typical stable diffusion range).

### Backend
- Update `web_app.py` to read `cfg` from the POST request.
- Pass `cfg` to `client.create_video_from_image`.
