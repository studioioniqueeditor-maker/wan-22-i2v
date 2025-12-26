# VividFlow - Quick Reference

## 🚀 Quick Start

### Start the Server
```bash
python3 web_app.py
# Server: http://localhost:8000
```

### Submit a Job
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "X-API-Key: YOUR_KEY" \
  -F "model=veo3.1" \
  -F "prompt=your prompt here" \
  -F "duration_seconds=4" \
  -F "enhance_prompt=true" \
  -F "image=@path/to/image.png"
```

### Check Status (Browser)
```
http://localhost:8000/api/v1/status/JOB_ID?api_key=YOUR_KEY
```

---

## ⚙️ Configuration

### Required Settings
```python
# MUST set enhance_prompt=true (Veo 3 requirement)
"enhance_prompt": "true"

# MUST NOT set add_keywords=true (causes RAI filtering)
# Omit add_keywords or set to false
```

### Port Configuration
- **Local:** Port 8000 (changed from 5000)
- **Production:** https://vivid.studioionique.com

---

## ✅ What Was Fixed

1. **RAI Filtering** - Disabled automatic keyword injection
2. **Port Conflict** - Changed from 5000 to 8000
3. **Browser Access** - Added query param support for API keys

---

## 🔧 Common Commands

### Get API Key
1. Go to http://localhost:8000/account
2. Click "Generate API Key"

### Run Test
```bash
python3 test-api.py
```

### Check Logs
```bash
tail -f logs/app.log
```

### Check Prompt Safety
```bash
python3 -c "from prompt_safety_checker import check_prompt_safety; check_prompt_safety('your prompt')"
```

---

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| RAI Filter Error | Check prompt for brands/celebrities, ensure `add_keywords` not set |
| 403 Error | Get valid API key from /account |
| Port in use | Kill process on 8000 or change port |
| 404 Not Found | Ensure web_app.py is running on port 8000 |
| enhance_prompt error | Must be "true", cannot disable for Veo 3 |

---

## 📖 Full Documentation

- `IMPLEMENTATION_GUIDE.md` - Complete guide
- `RAI_FILTERING_GUIDE.md` - RAI filtering details
- `PROMPT_MODIFICATION_FIX.md` - Technical fix details

---

**Server:** http://localhost:8000
**API:** http://localhost:8000/api/v1/*
**Account:** http://localhost:8000/account
