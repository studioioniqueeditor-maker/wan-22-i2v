# Vivid Flow - Professional Video Generation Platform

A production-grade web application and API for generating high-quality videos from images using **Wan 2.1** (RunPod) and **Google Veo 3.1** (Vertex AI) models.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 🎯 Features

### Core Functionality
- **Dual Model Support**: Switch between Wan 2.1 (open-source) and Google Veo 3.1 (enterprise)
- **Advanced Controls**: Camera motion, subject animation, environmental effects
- **Audio Generation**: Native audio support in Veo 3.1 videos
- **Prompt Enhancement**: AI-powered prompt optimization using Groq/Gemini
- **Cloud Storage**: Automatic upload to Google Cloud Storage

### Technical Features
- **Modern Web UI**: Glassmorphism-inspired interface with real-time previews
- **RESTful API**: Full-featured API with authentication and rate limiting
- **Queue System**: Async job processing with concurrency management
- **Secure Authentication**: User management via Supabase
- **Production Ready**: Comprehensive logging, error handling, and monitoring

## 🏗️ Architecture

### Technology Stack
- **Backend**: Flask (Python 3.10+), Gunicorn
- **Video Models**: Wan 2.1 (RunPod), Google Veo 3.1 (Vertex AI)
- **Storage**: Google Cloud Storage
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth + API Keys
- **Deployment**: Docker, Google Cloud Run

### Project Structure
```
wan-22-i2v/
├── web_app.py              # Main Flask application
├── api_router.py           # API endpoints
├── vertex_ai_veo_client.py # Veo 3.1 client
├── job_queue.py            # Asynchronous job processing
├── auth_service.py         # Authentication & user management
├── concurrency_manager.py  # Job concurrency control
├── templates/              # Web UI templates
├── Dockerfile              # Container configuration
├── deploy.sh               # Deployment automation
├── schema.sql              # Database schema
└── requirements.txt        # Python dependencies
```

## 📋 Prerequisites

- Python 3.10+
- Docker (for containerized deployment)
- **Google Cloud Platform**: Project with Vertex AI and Cloud Storage
- **RunPod Account**: Endpoint for Wan 2.1 model
- **Supabase Account**: For authentication and database

## 🚀 Installation

### Local Development

1. **Clone repository**:
   ```bash
   git clone https://github.com/studioioniqueeditor-maker/wan-22-i2v.git
   cd wan-22-i2v
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Setup database**:
   - Open Supabase SQL Editor
   - Run `schema.sql` to create tables and policies

6. **Run application**:
   ```bash
   python web_app.py
   ```
   Access at `http://localhost:8000`

### Docker Deployment

```bash
docker build -t vivid-flow .
docker run -p 8080:8080 --env-file .env vivid-flow
```

### Google Cloud Run Deployment

```bash
./deploy.sh
```

See deployment section for detailed instructions.

## ⚙️ Configuration

### Environment Variables

**RunPod (Wan 2.1)**:
- `RUNPOD_API_KEY` - Your RunPod API key
- `RUNPOD_ENDPOINT_ID` - Wan 2.1 endpoint ID

**Google Cloud (Veo 3.1)**:
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `GCS_BUCKET_NAME` - Cloud Storage bucket name
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account key (optional for Cloud Run)

**Supabase (Auth & Database)**:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `SUPABASE_SERVICE_KEY` - Service role key

**Application**:
- `FLASK_SECRET_KEY` - Session encryption key
- `FLASK_ENV` - `production` or `development`
- `ADMIN_EMAIL` - Admin user email for dashboard access
- `ADMIN_API_KEY` - Admin API access key
- `GROQ_API_KEY` - For prompt enhancement (optional)

## 🎮 Usage

### Web Interface

1. Navigate to application URL
2. Register/Login
3. Select model (Wan 2.1 or Veo 3.1)
4. Upload image
5. Configure parameters:
   - **Prompt**: Describe desired motion/scene
   - **Camera Motion**: Dolly, zoom, pan, tilt, etc.
   - **Subject Animation**: Head turn, blink, smile, etc.
   - **Environment**: Light changes, fog, rain, etc.
   - **Audio**: Enable for Veo 3.1 videos
6. Click **CREATE VIDEO**

### REST API

**Generate Video**:
```bash
curl -X POST https://your-app.run.app/api/v1/generate \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "model=veo3.1" \
  -F "prompt=A mountain landscape at sunset with gentle wind" \
  -F "image=@input.jpg" \
  -F "generate_audio=true" \
  -F "camera_motion=Slow zoom in" \
  -F "duration_seconds=6"
```

**Check Job Status**:
```bash
curl https://your-app.run.app/api/v1/status/JOB_ID \
  -H "X-API-Key: YOUR_API_KEY"
```

**Get History**:
```bash
curl https://your-app.run.app/api/v1/history \
  -H "X-API-Key: YOUR_API_KEY"
```

### API Response Format

```json
{
  "job_id": "abc123",
  "status": "queued",
  "message": "Job accepted. Queued for processing.",
  "request_id": "xyz789"
}
```

Job statuses: `queued`, `processing`, `completed`, `failed`, `cancelled`

## 🔧 Deployment

### Google Cloud Run (Recommended)

1. **Prepare**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Deploy**:
   ```bash
   ./deploy.sh
   ```

3. **Set environment variables** in Cloud Run console or via:
   ```bash
   gcloud run services update vivid-flow \
     --set-env-vars GOOGLE_CLOUD_PROJECT=your-project,...
   ```

4. **Configure secrets** (recommended for sensitive keys):
   ```bash
   echo -n "your-secret-value" | gcloud secrets create SECRET_NAME --data-file=-
   ```

### Health Checks

The application exposes `/health` endpoint:
```bash
curl https://your-app.run.app/health
```

## 📝 Prompt Best Practices (Veo 3.1)

### Optimal Structure
Follow this format for best results:
```
[Camera Motion]. [Main Subject and Action]. [Environmental Details].
```

### Examples

✅ **Good**:
- "Slow zoom in. A mountain landscape at sunset. Light gradually increases."
- "Pan left. A person walking through a forest. Leaves rustle in the wind."

❌ **Avoid**:
- "Keywords: zoom, mountain, sunset" (metadata-style)
- Celebrity/brand names (triggers RAI filters)
- Violent or inappropriate content

### RAI Filter Tips
- Use generic terms instead of specific people/brands
- Be descriptive but not explicit
- Avoid copyrighted characters
- Keep prompts clear and specific (100-150 words)

## 🐛 Troubleshooting

### Common Issues

**1. RAI Filtering Error**
```
Error: Content blocked by Responsible AI filters
```
**Solution**: Revise prompt to remove celebrity names, brands, or inappropriate content. Follow prompt best practices above.

**2. Cloud Run 404 Errors**
- Check Cloud Run logs for specific missing routes
- Verify all static files are included in deployment
- Ensure `static/` and `templates/` directories exist

**3. Video Generation Timeout**
- Veo 3.1: ~1 minute typical
- Wan 2.1: ~5 minutes typical
- Check job status via API rather than waiting synchronously

**4. Authentication Failures**
- Verify Supabase credentials in `.env`
- Check user is approved in admin dashboard
- Regenerate API key if needed

### Debugging

Enable detailed logging:
```bash
export FLASK_ENV=development
python web_app.py
```

Check logs:
```bash
tail -f logs/app.log
```

## 📊 Monitoring

### Admin Dashboard
Access at `/admin` (requires `ADMIN_EMAIL` match):
- View pending user approvals
- Monitor queue statistics
- Check concurrency status

### Metrics to Track
- Job queue length
- Active concurrent jobs
- Success/failure rates
- Average generation time
- RAI filter rate

## 🔮 Future Development

### Planned Features
- [ ] Batch video generation
- [ ] Video-to-video support
- [ ] Custom model fine-tuning
- [ ] Advanced editing tools
- [ ] Multi-language UI
- [ ] Webhook notifications
- [ ] Credit/billing system

### Known Issues
- Long videos (8s) may timeout on slow connections
- RAI filters can be overly sensitive for complex prompts
- SQLite job queue not suitable for high concurrency (consider Redis)

### Optimization Opportunities
- Implement Redis for job queue
- Add video thumbnail generation
- Implement progressive video streaming
- Add result caching
- Optimize image preprocessing

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues or questions:
- Check troubleshooting section above
- Review Cloud Run logs
- Contact project maintainer

## 📚 Additional Resources

- [Google Veo 3.1 Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/video/overview)
- [RunPod Documentation](https://docs.runpod.io/)
- [Supabase Documentation](https://supabase.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

**Version**: 2.0.0  
**Last Updated**: January 2026  
**Maintained by**: Studio Ionique