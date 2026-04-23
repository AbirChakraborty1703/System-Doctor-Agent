# SystemDoctor AI - Production Deployment Guide

## Overview

SystemDoctor AI is a multi-agent diagnostic system deployed using Streamlit for the UI and FastAPI for the backend API. This guide covers production deployment best practices.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- 2GB RAM minimum (4GB recommended)
- Network connectivity to Streamlit Cloud (if cloud deployment)

## Local Deployment

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env for your environment
# - Set ENVIRONMENT=production
# - Configure API_HOST, API_PORT, STREAMLIT_SERVER_PORT
# - Add LLM API keys if needed
# - Configure ALLOWED_ORIGINS for CORS
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Services Locally

**Option A: Streamlit Only (In-Process)**
```bash
streamlit run app.py --logger.level=info
```

**Option B: Both Streamlit and FastAPI (Separate Processes)**

Terminal 1 - FastAPI Backend:
```bash
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --log-level info
```

Terminal 2 - Streamlit Frontend:
```bash
streamlit run apps/streamlit/app.py --server.port 8501 --server.address 0.0.0.0
```

## Docker Deployment

### 1. Build Docker Images

```bash
docker-compose build
```

### 2. Run with Docker Compose

```bash
# Start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Streamlit Cloud Deployment

### 1. Prepare Repository

- Push code to GitHub repository
- Ensure `.gitignore` excludes `.env` and sensitive files
- Commit all production code

### 2. Connect to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect GitHub repository
4. Select branch and main file (`app.py`)
5. Configure secrets in Streamlit Cloud settings
   - Add environment variables as secrets
   - Format: `KEY=value` in secrets panel

### 3. Deploy

Streamlit Cloud automatically deploys when you push to the connected branch.

## Production Configuration

### CORS Configuration

Edit `apps/api/main.py` to restrict CORS origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://streamlit-cloud-url.streamlit.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

### Security Headers

The FastAPI app includes security headers by default:
- X-Content-Type-Options: nosniff
- X-Frame-Options: SAMEORIGIN
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000; includeSubDomains

### Logging

Configure log levels in `.env`:
- `DEBUG=false` for production
- `LOG_LEVEL=INFO` or `LOG_LEVEL=WARNING`

Logs are written to `logs/systemdoctor.log`

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
# Expected response: {"status": "ok", "service": "SystemDoctor AI API"}
```

### API Endpoints (for monitoring/integration)

- `GET /health` - Health check
- `GET /api/v1/app/event/open` - Component initialization endpoint
- `POST /sessions` - Start new diagnostic session
- `GET /sessions/{session_id}` - Get session status
- `POST /sessions/{session_id}/answer` - Submit answer to question
- `POST /sessions/{session_id}/verify` - Verify fix outcome

## Troubleshooting

### Issue: 403 Forbidden on API endpoints

**Solution**: Check CORS configuration in `apps/api/main.py`. Ensure your frontend origin is in `allow_origins`.

### Issue: Wavesurfer container errors in console

**Solution**: This is suppressed in production. Browser console shows warnings but doesn't affect functionality. The audio container is properly initialized via HTML meta tags.

### Issue: Port already in use

**Solution**: Change port in `.env` or docker-compose.yml and restart services.

### Issue: Out of memory

**Solution**: Increase memory in Docker compose limits or host machine. Monitor with `docker stats`.

## Performance Tuning

### Caching

Enable knowledge base caching in `.env`:
```
CACHE_KNOWLEDGE_BASE=true
```

### Session Management

Configure session timeout:
```
SESSION_TIMEOUT_MINUTES=60
```

### Concurrent Session Limit

Set maximum concurrent sessions:
```
MAX_CONCURRENT_SESSIONS=100
```

## Backup and Recovery

### Database Backup (SQLite)

```bash
# Backup session database
cp systemdoctor.db systemdoctor.db.backup.$(date +%s)
```

### Environment Configuration

```bash
# Backup .env
cp .env .env.backup.$(date +%s)
```

## Updates and Maintenance

### Update Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

### Restart Services

```bash
# Using Docker Compose
docker-compose restart

# Using systemd (if configured)
sudo systemctl restart systemdoctor-api
sudo systemctl restart systemdoctor-streamlit
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs api` or `docker-compose logs streamlit`
2. Review environment configuration in `.env`
3. Verify network connectivity and firewall rules
4. Check API health endpoint: `curl http://localhost:8000/health`

---

**Last Updated**: 2025-01-01
**Version**: 1.0.0
