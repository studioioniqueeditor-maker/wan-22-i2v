# Track Spec: Request Timing Analysis

## Overview
The user wants to see a breakdown of the time taken for video generation, specifically distinguishing between the total request time, the time spent waiting for the job to start (spin-up/queue), and the actual generation time.

## Goals
- Measure total request duration in `web_app.py`.
- Update `GenerateVideoClient` to track:
    - **Submission Time:** When the request was sent.
    - **Start Time:** When the job status changed from IN_QUEUE to IN_PROGRESS.
    - **Completion Time:** When the job status changed to COMPLETED.
- Calculate:
    - **Spin-up Time:** Start Time - Submission Time.
    - **Generation Time:** Completion Time - Start Time.
- Return these metrics from the client and display them in the UI.

## Requirements
### Backend
- Update `create_video_from_image` to return timing metrics in the result dictionary.
- Update `_poll_job` to track status changes and record timestamps.

### Frontend
- Update `templates/index.html` to display the timing breakdown (Total, Spin-up, Generation) nicely formatted.
