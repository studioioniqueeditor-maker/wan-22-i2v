# Track Spec: Fix RunPod 404 Error

## Overview
The user is encountering a 404 error when attempting to generate video via RunPod.

## Goals
- Identify the correct RunPod API URL (run vs runsync).
- Ensure the Endpoint ID is correctly passed and used.
- Resolve the 404 error to restore video generation functionality.

## Technical Details
- Verify if the endpoint requires `/run` or `/runsync`.
- Check if the API version should be `/v1/` or `/v2/`.
