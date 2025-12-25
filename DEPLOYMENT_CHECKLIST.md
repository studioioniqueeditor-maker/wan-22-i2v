# Vivid Flow v2.0 Deployment Checklist

## ✅ Pre-Deployment

### 1. Environment Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Fill in all required environment variables:
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `SUPABASE_SERVICE_KEY`
  - `FLASK_SECRET_KEY`
  - `GOOGLE_CLOUD_PROJECT`
  - `GCS_BUCKET_NAME`
  - `RUNPOD_API_KEY`
  - `RUNPOD_ENDPOINT_ID`
  - `GROQ_API_KEY` (optional)
- [ ] Set `FLASK_ENV=production` for production mode
- [ ] Verify `.env` is in `.gitignore`

### 2. Database Setup
- [ ] Run `schema.sql` in Supabase SQL Editor
- [ ] Verify tables created:
  - `public.profiles`
  - `public.history`
- [ ] Verify RLS policies are active
- [ ] Test row-level security with test user

### 3. Google Cloud Configuration
- [ ] Enable APIs:
  - Vertex AI API
  - Cloud Storage API
  - Cloud Run API (for deployment)
- [ ] Create service account with appropriate roles
- [ ] Download service account key (JSON)
- [ ] Create GCS bucket
- [ ] Set bucket permissions for service account
- [ ] Verify bucket lifecycle policies (if needed)

### 4. Storage Setup
- [ ] Create temporary upload directory: `temp_uploads/`
- [ ] Create output directory: `output/`
- [ ] Set appropriate permissions (755)
- [ ] Configure auto-cleanup (cron job or similar)

### 5. Code Verification
- [ ] Run all unit tests: `pytest tests/`
- [ ] Check test coverage
- [ ] Verify all imports work
- [ ] Check for any hardcoded credentials
- [ ] Review security settings

## ✅ Deployment Steps

### Option A: Google Cloud Run (Recommended)

1. **Build Container**
```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
./deploy.sh
```

2. **Manual Deployment**
```bash
# Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/vivid-flow

# Deploy to Cloud Run
gcloud run deploy vivid-flow \
  --image gcr.io/YOUR_PROJECT_ID/vivid-flow \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "$(grep -v '^#' .env | tr '\n' ',')"
```

3. **Configure Cloud Run**
- [ ] Set memory to 2GB+ (for video processing)
- [ ] Set timeout to 3600s (1 hour)
- [ ] Set max instances to prevent resource exhaustion
- [ ] Enable VPC connector (if needed for private services)

### Option B: Traditional Server

1. **Install Dependencies**
```bash
sudo apt-get update
sudo apt-get install python3.10 python3-pip nginx

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure Gunicorn**
```bash
# Create systemd service
sudo nano /etc/systemd/system/vivid-flow.service
```

Service file contents:
```ini
[Unit]
Description=Vivid Flow Web App
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/vivid-flow
Environment="PATH=/opt/vivid-flow/venv/bin"
ExecStart=/opt/vivid-flow/venv/bin/gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 8 --timeout 0 web_app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

3. **Configure Nginx**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /output {
        alias /opt/vivid-flow/output;
        expires 1h;
    }
}
```

## ✅ Post-Deployment

### 1. System Verification
- [ ] Run health check: `python monitor.py`
- [ ] Test web interface access
- [ ] Test API endpoints
- [ ] Check logs: `tail -f logs/app.log`

### 2. Queue System
- [ ] Verify job queue worker started
- [ ] Test job submission via API
- [ ] Verify status tracking works
- [ ] Test job cancellation

### 3. Authentication
- [ ] Test user registration
- [ ] Test user login/logout
- [ ] Test API key generation
- [ ] Test API authentication

### 4. Video Generation
- [ ] Test Wan 2.1 model
- [ ] Test Veo 3.1 model
- [ ] Test with file upload
- [ ] Test with GCS URL
- [ ] Verify video storage
- [ ] Check history tracking

### 5. Rate Limiting
- [ ] Verify API limits enforced
- [ ] Verify web limits enforced
- [ ] Test 429 responses
- [ ] Verify retry headers

### 6. Monitoring
- [ ] Set up log aggregation
- [ ] Configure error alerts
- [ ] Monitor disk space
- [ ] Monitor queue depth

## ✅ Security Verification

### 1. Access Control
- [ ] Verify API key requirement
- [ ] Test ownership validation
- [ ] Check RLS policies
- [ ] Verify no data leakage

### 2. Input Validation
- [ ] Test file size limits
- [ ] Test file type restrictions
- [ ] Test prompt length limits
- [ ] Test parameter validation

### 3. Secrets Management
- [ ] Verify no secrets in code
- [ ] Check .env in .gitignore
- [ ] Review environment variable exposure in logs
- [ ] Test secret rotation procedure

### 4. Network Security
- [ ] Verify HTTPS only
- [ ] Test CORS policies
- [ ] Check firewall rules
- [ ] Verify no open ports

## ✅ Performance Testing

### 1. Load Testing
- [ ] Test concurrent users (10+)
- [ ] Test concurrent job submissions
- [ ] Monitor resource usage
- [ ] Check for bottlenecks

### 2. Stress Testing
- [ ] Submit 50+ jobs
- [ ] Test queue depth limits
- [ ] Monitor memory usage
- [ ] Check for leaks

### 3. Endurance Testing
- [ ] Run system for 24 hours
- [ ] Monitor disk usage
- [ ] Check log file sizes
- [ ] Verify cleanup processes

## ✅ Backup & Recovery

### 1. Database
- [ ] Set up automated Supabase backups
- [ ] Test restore procedure
- [ ] Verify backup integrity

### 2. Configuration
- [ ] Backup .env file securely
- [ ] Document all custom configurations
- [ ] Store deployment scripts in version control

### 3. Logs
- [ ] Set up log rotation
- [ ] Configure log archival
- [ ] Monitor disk space

## ✅ Documentation

### 1. User Documentation
- [ ] Update API documentation
- [ ] Create user guides
- [ ] Document common issues
- [ ] Provide contact information

### 2. Operations Documentation
- [ ] Write runbook for common tasks
- [ ] Document scaling procedures
- [ ] Create incident response guide
- [ ] List monitoring metrics

### 3. Developer Documentation
- [ ] Update architecture diagrams
- [ ] Document data flow
- [ ] List dependencies and versions
- [ ] Explain queue system

## ✅ Rollback Plan

If deployment fails:

1. **Immediate Rollback**
```bash
# Redeploy previous version
gcloud run deploy vivid-flow --image gcr.io/PROJECT/vivid-flow:PREVIOUS_TAG

# Or restore service
gcloud run services update vivid-flow --image gcr.io/PROJECT/vivid-flow:PREVIOUS
```

2. **Data Safety**
- [ ] No data loss from failed deployment
- [ ] Database migrations are idempotent
- [ ] Rollback doesn't break existing data

3. **Communication**
- [ ] Notify users of issues
- [ ] Provide ETA for fix
- [ ] Document root cause

## ✅ Go-Live Checklist

- [ ] All tests passing
- [ ] Security scan complete
- [ ] Performance benchmarks met
- [ ] Monitoring configured
- [ ] Backup systems tested
- [ ] Rollback plan ready
- [ ] Team briefed
- [ ] Support ready

## 🚀 Deployment Commands

```bash
# Full deployment
./deploy.sh

# Check system health
python monitor.py

# View logs
tail -f logs/app.log

# Check queue status
python -c "from job_queue import JobQueue; q=JobQueue.get_instance(); print(q.get_user_jobs('all', limit=10))"

# Run tests
pytest tests/ -v --cov=.
```

## 📞 Support Contacts

- **Technical Support**: [Your support email]
- **Security Issues**: [Your security email]
- **Emergency**: [Your emergency contact]

---

**Last Updated**: 2025-01-15
**Version**: 2.0.0
**Next Review**: After 30 days or major change
