# 🚀 Deployment Checklist - LATEST: Gemini Safety Filter Fix v2

## 🔥 URGENT UPDATE (Nov 13, 2025)

**Context Document Sanitization + Multi-Tier Retry Mechanism Deployed**

### Quick Deployment Steps
```bash
cd /home/kerich/Documents/SHAMBABORA/rag-service
git pull origin master
docker-compose down && docker-compose up --build -d
```

### Post-Deploy Test
```bash
curl -X POST http://localhost:8088/advice \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "analytics_context": {"crop_type": "maize"},
    "question": "What disease management for maize?",
    "conversation_id": "test"
  }'
# Should return actual advice, NOT "blocked by safety restrictions"
```

### What's New
- ✅ Context documents sanitized (dangerous words replaced)
- ✅ Two-tier retry mechanism (removes contexts, then minimal settings)
- ✅ Better debug logging (shows exactly which safety category blocks)
- ✅ 600-char context chunks (was 900, safer)

See `CONTEXT_SANITIZATION_FIX.md` for details.

---

# 🚀 Deployment Checklist

Complete checklist for deploying your RAG service to production.

## Pre-Deployment

### ✅ Development Testing
- [ ] All endpoints tested locally
- [ ] Conversation history working
- [ ] File upload working
- [ ] Multiple users tested
- [ ] Error handling verified
- [ ] Performance acceptable (1-3s per query)

### ✅ Code Review
- [ ] Code reviewed and cleaned
- [ ] No hardcoded secrets
- [ ] Logging implemented
- [ ] Error messages are user-friendly
- [ ] API documentation up to date

### ✅ Dependencies
- [ ] requirements.txt is complete
- [ ] All packages have version pins
- [ ] No development-only packages in production
- [ ] Security vulnerabilities checked

## Security Hardening

### 🔒 Authentication & Authorization
- [ ] Add JWT or OAuth2 authentication
- [ ] Implement user verification
- [ ] Add API key authentication (optional)
- [ ] Verify user owns conversations before access
- [ ] Add role-based access control (if needed)

### 🔒 API Security
- [ ] Add rate limiting (e.g., 100 requests/minute per user)
- [ ] Implement request size limits
- [ ] Add input validation and sanitization
- [ ] Enable HTTPS only
- [ ] Update CORS to specific origins
- [ ] Add security headers (HSTS, CSP, etc.)

### 🔒 Secrets Management
- [ ] Move API keys to secrets manager (AWS Secrets Manager, etc.)
- [ ] Use environment variables for all configs
- [ ] Never commit .env file
- [ ] Rotate API keys regularly
- [ ] Use different keys for dev/staging/prod

### 🔒 Data Security
- [ ] Encrypt sensitive data at rest
- [ ] Use HTTPS for all communications
- [ ] Implement data retention policies
- [ ] Add user data deletion capability (GDPR)
- [ ] Backup conversation data regularly

## Infrastructure

### 🏗️ Database
- [ ] Switch from JSON to PostgreSQL
- [ ] Set up database backups
- [ ] Configure connection pooling
- [ ] Add database indexes for performance
- [ ] Set up read replicas (if needed)

### 🏗️ Caching
- [ ] Add Redis for conversation caching
- [ ] Cache frequently accessed conversations
- [ ] Implement cache invalidation strategy
- [ ] Set appropriate TTLs

### 🏗️ Storage
- [ ] Move vector index to persistent storage
- [ ] Set up S3/blob storage for uploaded files
- [ ] Implement file size limits
- [ ] Add virus scanning for uploads

### 🏗️ Compute
- [ ] Choose deployment platform (AWS, GCP, Azure, etc.)
- [ ] Set up load balancer
- [ ] Configure auto-scaling
- [ ] Set resource limits (CPU, memory)
- [ ] Configure health checks

## Application Configuration

### ⚙️ Environment Variables
```env
# Production .env template
ENVIRONMENT=production
GOOGLE_API_KEY=<from-secrets-manager>
EMBEDDING_MODEL=nomic-embed-text
GENERATION_MODEL=gemini-1.5-flash

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379

# Storage
INDEX_DIR=/mnt/data/index
CONVERSATION_DIR=/mnt/data/conversations
UPLOAD_DIR=/mnt/data/uploads

# API Configuration
PORT=8088
WORKERS=4
LOG_LEVEL=info
MAX_UPLOAD_SIZE=10485760  # 10MB

# Security
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
RATE_LIMIT_PER_MINUTE=100
JWT_SECRET=<from-secrets-manager>
```

### ⚙️ Logging
- [ ] Configure structured logging (JSON)
- [ ] Set up log aggregation (CloudWatch, Datadog, etc.)
- [ ] Add request ID tracking
- [ ] Log all errors with context
- [ ] Set appropriate log levels
- [ ] Implement log rotation

### ⚙️ Monitoring
- [ ] Set up application monitoring (New Relic, Datadog, etc.)
- [ ] Add custom metrics (query latency, error rates)
- [ ] Configure alerts for errors
- [ ] Monitor API usage per user
- [ ] Track conversation creation rate
- [ ] Monitor database performance

### ⚙️ Error Tracking
- [ ] Integrate Sentry or similar
- [ ] Configure error notifications
- [ ] Add error context (user_id, conversation_id)
- [ ] Set up error rate alerts

## Deployment Steps

### 📦 Build & Package
- [ ] Build Docker image
- [ ] Tag image with version
- [ ] Push to container registry
- [ ] Test image locally

### 📦 Database Migration
- [ ] Create production database
- [ ] Run migration scripts
- [ ] Verify schema
- [ ] Set up backups

### 📦 Deploy Application
- [ ] Deploy to staging first
- [ ] Run smoke tests on staging
- [ ] Deploy to production
- [ ] Verify health endpoint
- [ ] Test critical endpoints

### 📦 DNS & SSL
- [ ] Configure domain name
- [ ] Set up SSL certificate (Let's Encrypt, ACM, etc.)
- [ ] Configure HTTPS redirect
- [ ] Test SSL configuration

## Post-Deployment

### 🔍 Verification
- [ ] Health check returns 200
- [ ] Can create conversation
- [ ] Can query with history
- [ ] Can list conversations
- [ ] File upload works
- [ ] CORS works from frontend
- [ ] Mobile app can connect

### 🔍 Performance Testing
- [ ] Load test with expected traffic
- [ ] Verify response times < 3s
- [ ] Check database query performance
- [ ] Monitor memory usage
- [ ] Check for memory leaks

### 🔍 Monitoring Setup
- [ ] Verify logs are flowing
- [ ] Check metrics are reporting
- [ ] Test alert notifications
- [ ] Set up uptime monitoring
- [ ] Configure status page

## Ongoing Maintenance

### 🔧 Regular Tasks
- [ ] Monitor error rates daily
- [ ] Review logs weekly
- [ ] Check performance metrics weekly
- [ ] Update dependencies monthly
- [ ] Review security advisories
- [ ] Rotate API keys quarterly
- [ ] Review and optimize database quarterly

### 🔧 Backup & Recovery
- [ ] Test backup restoration monthly
- [ ] Document recovery procedures
- [ ] Set up disaster recovery plan
- [ ] Test failover procedures

### 🔧 Scaling
- [ ] Monitor usage trends
- [ ] Plan for capacity increases
- [ ] Optimize slow queries
- [ ] Add caching where needed
- [ ] Consider CDN for static assets

## Documentation

### 📚 Internal Documentation
- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Document monitoring and alerts
- [ ] Create incident response plan
- [ ] Document backup/restore procedures

### 📚 External Documentation
- [ ] Update API documentation
- [ ] Provide production API URL
- [ ] Document rate limits
- [ ] Provide support contact
- [ ] Create changelog

## Compliance & Legal

### ⚖️ Data Privacy
- [ ] GDPR compliance (if applicable)
- [ ] Privacy policy updated
- [ ] Terms of service updated
- [ ] Data retention policy documented
- [ ] User data deletion process

### ⚖️ Licensing
- [ ] Review third-party licenses
- [ ] Ensure compliance with API terms (Google, Ollama)
- [ ] Document license requirements

## Rollback Plan

### 🔄 Preparation
- [ ] Document current version
- [ ] Keep previous Docker image
- [ ] Backup current database
- [ ] Document rollback steps

### 🔄 Rollback Procedure
1. Stop current deployment
2. Restore previous Docker image
3. Rollback database if needed
4. Verify health check
5. Test critical endpoints
6. Monitor for issues

## Production Checklist Summary

### Critical (Must Have)
- [x] HTTPS enabled
- [x] Secrets in secrets manager
- [x] Database backups configured
- [x] Monitoring and alerts set up
- [x] Error tracking enabled
- [x] Rate limiting implemented
- [x] CORS restricted to your domains

### Important (Should Have)
- [ ] PostgreSQL instead of JSON
- [ ] Redis caching
- [ ] Load balancer
- [ ] Auto-scaling
- [ ] Structured logging
- [ ] Performance monitoring

### Nice to Have
- [ ] CDN for static assets
- [ ] Read replicas
- [ ] Multi-region deployment
- [ ] A/B testing capability
- [ ] Feature flags

## Quick Production Setup (Docker)

### Dockerfile (Production)
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8088/health || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8088", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

### docker-compose.yml (Production)
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8088:8088"
    environment:
      - ENVIRONMENT=production
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - postgres
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8088/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=ragservice
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: always

volumes:
  postgres_data:
  redis_data:
```

## Support Contacts

- **DevOps**: [devops@example.com]
- **On-Call**: [oncall@example.com]
- **Security**: [security@example.com]

---

## Final Pre-Launch Checklist

- [ ] All security measures implemented
- [ ] Monitoring and alerts configured
- [ ] Backups tested
- [ ] Documentation complete
- [ ] Team trained on deployment
- [ ] Rollback plan documented
- [ ] Support contacts updated
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Legal review completed

**Ready to launch! 🚀**
