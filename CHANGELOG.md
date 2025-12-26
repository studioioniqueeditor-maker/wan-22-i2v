# Changelog

All notable changes to VividFlow Video Generation project.

## [1.0.0] - 2025-12-27

### Fixed

#### Critical: RAI Filtering Issue
- **Problem:** API requests were being blocked by Google's Responsible AI filters, while identical requests worked in Google's web UI
- **Root Cause:** Code was automatically modifying prompts by adding `". Cinematic style. Keywords: {camera_motion}."` which triggered filters
- **Solution:**
  - Added `add_keywords` parameter (defaults to `False`)
  - Prompts are now sent unchanged unless explicitly requested
  - Only Google's `enhance_prompt` modifies prompts (required by Veo 3)
- **Files Changed:**
  - `vertex_ai_veo_client.py` (lines 200-231)
- **Impact:** ✅ Videos generate successfully with same content that works in Google's UI

#### Critical: Port Conflict
- **Problem:** Server getting 403 errors, requests not reaching Flask
- **Root Cause:** Port 5000 occupied by macOS AirPlay/AirTunes service
- **Solution:** Changed server port from 5000 to 8000
- **Files Changed:**
  - `web_app.py` (line 496)
  - `test-api.py` (lines 8-9)
- **Impact:** ✅ Flask serves correctly on port 8000

#### High: Browser Status URL Access
- **Problem:** Status URLs returned "API key missing" when opened in browser
- **Root Cause:** Browsers don't send custom HTTP headers
- **Solution:** Added support for API key in query parameters
- **Files Changed:**
  - `api_router.py` (line 35-36)
- **Usage:** `http://localhost:8000/api/v1/status/JOB_ID?api_key=YOUR_KEY`
- **Impact:** ✅ Status URLs work in browsers and API clients

### Added

#### Documentation
- `IMPLEMENTATION_GUIDE.md` - Comprehensive implementation guide
- `QUICK_REFERENCE.md` - Quick reference for common tasks
- `CHANGELOG.md` - This file
- `RAI_FILTERING_GUIDE.md` - Detailed guide on avoiding RAI filters
- `PROMPT_MODIFICATION_FIX.md` - Technical details of prompt fix
- `prompt_safety_checker.py` - Tool to check prompts before submission
- `test_prompt_fix.py` - Test to verify prompt modification fix

#### Enhanced Logging
- Added comprehensive diagnostic logging for Veo API responses
- Log shows exact prompts being sent (original vs modified)
- RAI filtering detection and reporting
- Operation state logging at multiple stages

### Changed

#### API Requirements
- `enhance_prompt` is now **required** to be `"true"` (Veo 3 limitation)
- `add_keywords` defaults to `false` (prevents prompt modification)
- Port changed from 5000 to 8000

#### Error Handling
- Better error messages for RAI filtering
- Structured error responses with error types
- Clear distinction between RAI filters vs other API errors

### Technical Details

#### Prompt Handling Flow

**Before Fix:**
```
User Prompt → Add Keywords → Google Enhancement → RAI Filters ❌
"prompt"    → "prompt. Cinematic style. Keywords: X" → Enhanced → BLOCKED
```

**After Fix:**
```
User Prompt → Google Enhancement → Success ✅
"prompt"    → Enhanced by Google → Generated
```

#### Configuration Summary

**Required:**
- `enhance_prompt: "true"` (cannot be false for Veo 3)

**Recommended:**
- `add_keywords: false` (default, don't set it)
- Port: 8000 (avoid macOS conflicts)

**Optional:**
- `camera_motion`: Motion type
- `duration_seconds`: 4 or 8
- `resolution`: "720p" or "1080p"

### Migration Guide

If you have existing code using the old API:

1. **Update Port:**
   ```python
   # Old
   API_URL = "http://localhost:5000/api/v1/generate"

   # New
   API_URL = "http://localhost:8000/api/v1/generate"
   ```

2. **Update enhance_prompt:**
   ```python
   # Old (would fail)
   "enhance_prompt": "false"

   # New (required)
   "enhance_prompt": "true"
   ```

3. **Remove add_keywords if set:**
   ```python
   # Old (causes RAI filtering)
   "add_keywords": True

   # New (omit or set to false)
   # Don't include add_keywords parameter
   ```

4. **Update status URL access (optional):**
   ```python
   # Can now use query params for browser access
   url = f"{STATUS_URL}?api_key={API_KEY}"
   ```

### Testing

All changes have been tested with:
- ✅ Real video generation requests
- ✅ Browser status URL access
- ✅ API client (requests library)
- ✅ Multiple prompts and images
- ✅ Error scenarios

### Known Issues

None at this time.

### Upgrade Notes

- **Breaking Change:** Port changed from 5000 to 8000
- **Breaking Change:** `enhance_prompt=false` no longer supported (Veo 3 requirement)
- **Behavior Change:** Prompts no longer automatically modified with keywords

### Contributors

- Investigation and fixes: 2025-12-27
- Testing and validation: 2025-12-27

---

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH**
- MAJOR: Incompatible API changes
- MINOR: Backwards-compatible functionality
- PATCH: Backwards-compatible bug fixes

---

**For detailed implementation information, see `IMPLEMENTATION_GUIDE.md`**
