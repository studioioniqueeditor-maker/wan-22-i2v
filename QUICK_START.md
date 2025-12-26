# Veo 3.1 Fix - Quick Start Guide

## What Was Fixed

**Problem**: "Video generation returned no results" error with no details about why.

**Solution**: Added comprehensive logging + SDK upgrade to reveal the actual cause.

---

## ✅ What You Have Now

1. **google-genai SDK upgraded** to 1.56.0
2. **Detailed logging** in all components
3. **Operation inspection** to see what Veo actually returns
4. **Diagnostic tool** to verify setup
5. **Test script** to validate everything works

---

## 🚀 Get Started in 3 Steps

### Step 1: Verify Setup
```bash
python3 diagnose.py
```

Should show:
```
✅ All checks passed! System is ready.
```

### Step 2: Start Server
```bash
python3 web_app.py
```

Watch for initialization logs:
```
[Veo:xxxx] ===== VEO CLIENT INITIALIZATION =====
[Veo:xxxx] SDK Version: 1.56.0
[JobQueue] Worker thread started
```

### Step 3: Make a Test Request

```bash
# First, upload an image to GCS (if you don't have one)
# Or use this curl with your image:

curl -X POST http://127.0.0.1:5000/api/v1/generate \
  -H "X-API-Key: A6F3BF16-8076-41E8-918A-D7ACFDB086BC" \
  -F "model=veo3.1" \
  -F "prompt=A scenic landscape, cinematic, high quality" \
  -F "image=@/path/to/your/image.jpg"
```

---

## 📊 What the Logs Will Show You

### On Request:
```
[Veo:abc123] ===== CREATE_VIDEO_FROM_IMAGE STARTED =====
[Veo:abc123] Image: /tmp/upload.jpg (2.5MB)
[Veo:abc123] Prompt: 'A scenic landscape...'
[Veo:abc123] Uploading to GCS...
[Veo:abc123] ✓ Uploaded to: gs://ltx-assets/inputs/12345.jpg
```

### During Processing:
```
[Veo:abc123] Calling Veo API...
[Veo:abc123] Polling for completion...
[Veo:abc123] ✓ Completed after 4 polls
[Veo:abc123] Operation state at [after_polling]:
[Veo:abc123]   - done: True
[Veo:abc123]   - error: None
[Veo:abc123]   - generated_videos length: 1  ✓
[Veo:abc123] ✓ Successfully extracted video: 2048576 bytes
```

### If It Fails (NOW you get details):
```
[Veo:abc123] ✗ No generated videos
[Veo:abc123] Inspection: {
  "has_result": true,
  "generated_videos_count": 0,
  "metadata": {
    "safety_reasons": ["violates_policy"],
    "prompt_rewrite": "..."
  }
}
```

---

## 🔍 Diagnosing Your Original Issue

Your error: `"Video generation returned no results for prompt: dolly zoom in, no character movement, cinematic sh..."`

With the new logs, you'll see:

### Option A: Content Policy Issue
```
"metadata": {"safety": "BLOCKED", "reason": "camera_motion_too_extreme"}
```
**Fix**: Change your prompt to be less aggressive:
```diff
- "dolly zoom in, no character movement, cinematic shot"
+ "gentle zoom, static camera, cinematic shot"
```

### Option B: Rate Limiting
```
"metadata": {"quota": "exceeded", "limit": "100/day"}
```
**Fix**: Wait or request higher quota from Google

### Option C: Prompt Too Complex
```
"metadata": {"prompt_rewrite": "simplified version of your prompt"}
```
**Fix**: Use the rewritten prompt

### Option D: Image Issue
```
"inspection": {"first_video_has_bytes": false, "video_bytes": null}
```
**Fix**: Check image format (must be JPG/PNG/WEBP, <10MB)

---

## 📝 Debugging Checklist

When you get an error, check:

- [ ] **Logs show** request ID (e.g., `[Veo:abc123]`)
- [ ] **Logs show** `generated_videos_count` value
- [ ] **If count = 0**, check `inspection.metadata` for clues
- [ ] **Try simpler prompt**: "A simple test, high quality"
- [ ] **Try different image**: Smaller, different format
- [ ] **Check image size**: Should be <10MB
- [ ] **Check prompt length**: Keep it <100 words

---

## 🎯 Example Test Flow

```bash
# Terminal 1: Start server
python3 web_app.py

# Terminal 2: Watch logs, then send request
curl -X POST http://127.0.0.1:5000/api/v1/generate \
  -H "X-API-Key: A6F3BF16-8076-41E8-918A-D7ACFDB086BC" \
  -F "model=veo3.1" \
  -F "prompt=A beautiful sunset over mountains" \
  -F "image=@test_image.jpg"

# Server logs show exactly what happens:
[Veo:xxxx][Op:yyyy] ===== CREATE_VIDEO_FROM_IMAGE STARTED =====
...
[Veo:xxxx][Op:yyyy]   - generated_videos length: 1  ✓ SUCCESS
```

---

## 📞 What to Share if It Still Fails

If you still get errors, please share:

1. **The complete log output** from `web_app.py` (especially the inspection JSON)
2. **Your exact prompt** (full text)
3. **Image details** (size, format, subject)
4. **The response from** `curl http://127.0.0.1:5000/api/v1/status/{job_id}`

With this info, we can pinpoint the exact cause!

---

## 🎉 Summary

**Before**: "Video generation returned no results" (mysterious, useless)

**After**: 
```
[Veo:abc123] Inspection: {
  "generated_videos_count": 0,
  "metadata": {"safety": "BLOCKED", "reason": "violates_camera_motion_policy"}
}
```
(now you know WHY and can fix it!)

The fix is ready. Run `python3 diagnose.py` and then test!
