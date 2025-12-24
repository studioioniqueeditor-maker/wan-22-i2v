# Track Spec: UI Redesign (VividFlow 2.0) - REVISED

## Overview
A complete visual overhaul to strictly match the provided "VividFlow 2.0" reference image. The previous attempt was too reliant on default Bootstrap styles. This version focuses on pixel-perfect matching of the light-themed, card-based aesthetic.

## Goals
- **Full Screen Layout:** Maximize screen real estate with a responsive, full-width design.
- **Reference Fidelity:** Exact color matching (light theme, white backgrounds, subtle borders), typography, and component styling (inputs, buttons).
- **Preview Area:** Correctly sized 16:9 video player that dominates the right column.

## Requirements
### Visual Style (Strict Match)
- **Theme:** Light Mode (White/Off-White backgrounds).
- **Cards:** White background, rounded corners (approx 16-24px), subtle drop shadows or borders.
- **Typography:** Clean sans-serif (Inter/SF Pro), specific font weights for headers vs labels.
- **Colors:** 
    - Background: Light Gray (#f5f5f7 or similar).
    - Card Background: White (#ffffff).
    - Accent: Blue (for sliders).
    - Primary Button: Black (#000000).
    - Inputs: Light Gray Fill (#f9f9f9), no default borders.

### Components
- **Drop Zone:** Large, dashed border, centered icon, light background.
- **Inputs:** Rounded corners, internal padding, no harsh borders.
- **Generate Button:** Full width, black background, pill or rounded rectangle.
- **Preview:** Dark placeholder background when empty, 16:9 aspect ratio.

### Layout
- **Container:** `container-fluid` or custom max-width container (e.g. 1400px) centered vertically/horizontally.
- **Grid:** 50/50 or 60/40 split depending on screen size.