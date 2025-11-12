# Jenkins Quick Reference Card

## 📋 Credentials yang Dibutuhkan

| Credential ID | Type | Purpose |
|---------------|------|---------|
| `github-credentials` | Username+Password | Clone repository |
| `docker-hub-credentials` | Username+Password | Push Docker images |
| `vps-ssh-password` | Username+Password | Deploy ke VPS |
| `youtube-api-key` | Secret Text | YouTube Data API v3 |

## 🌍 Global Environment Variables

**Location:** Manage Jenkins → Configure System → Global properties → Environment variables

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `VPS_HOST` | `202.155.90.93` | VPS IP address |
| `DOCKER_REGISTRY` | `tlkmags` | Docker Hub username |
| `GIT_REPO_URL` | `https://github.com/user/repo.git` | Git repository URL |

**Security Note:** Nilai di atas adalah contoh. Gunakan nilai Anda sendiri dan jangan share ke public.

## 🚀 Quick Commands

### Trigger Build
```bash
# Manual trigger
Jenkins Dashboard → youtube-trending-fetcher → Build Now

# Via Git push
git push origin main  # Auto-trigger jika webhook configured
```

### Check Build Status
```bash
Jenkins Dashboard → youtube-trending-fetcher → Build History
```

### View Console Output
```bash
Click build number → Console Output
```

## 🔍 Verify Deployment

### Health Check
```bash
curl http://VPS_IP:8000/health
```

### API Docs
```
http://VPS_IP:8000/docs
```

### Test Trending Endpoint
```bash
curl "http://VPS_IP:8000/trending?country=ID&limit=5"
```

### Check Logs on VPS
```bash
ssh user@VPS_IP
docker logs youtube-trending-fetcher-app --tail 50
```

## 🐛 Troubleshooting Quick Fixes

### Build Failed at Docker Build
```bash
# Check Dockerfile exists
# Verify requirements.txt is valid
# Check Jenkins server disk space
```

### Build Failed at Tests
```bash
# Tests are optional - pipeline continues
# Check test logs in console output
```

### Cannot Connect to VPS
```bash
# Verify VPS_HOST in Jenkins global variables
# Check VPS SSH credentials
# Test manual: ssh user@VPS_IP
```

### Container Won't Start
```bash
# SSH to VPS
docker logs youtube-trending-fetcher-app
docker ps -a | grep youtube

# Common issues:
# - Port 8000 in use: netstat -tlnp | grep 8000
# - Invalid API key: check Jenkins credential
# - Redis not running: docker ps | grep redis
```

## 📊 Pipeline Stages

1. 🧹 Clean Workspace
2. 📦 Pull SCM
3. 🔐 Docker Login
4. 🔍 Environment Check
5. 🧪 Run Tests
6. 🔨 Docker Build
7. 🚀 Push to Registry
8. 🎯 Deploy to VPS
9. ✅ Verify Deployment

## 🔄 Rollback Steps

```bash
# 1. SSH to VPS
ssh user@VPS_IP

# 2. Stop current
docker stop youtube-trending-fetcher-app
docker rm youtube-trending-fetcher-app

# 3. List versions
docker images tlkmags/youtube-trending-fetcher

# 4. Run previous version
docker run -d \
  --name youtube-trending-fetcher-app \
  --network youtube-fetcher-network \
  -p 8000:8000 \
  -e YOUTUBE_API_KEY="your_key" \
  -e REDIS_URL=redis://youtube-trending-fetcher-redis:6379/0 \
  tlkmags/youtube-trending-fetcher:PREVIOUS_BUILD_NUMBER
```

## 🛠️ Maintenance Commands

### Clean Docker on Jenkins Server
```bash
# Remove old images
docker image prune -a

# Remove dangling images
docker image prune -f

# Check disk usage
docker system df
```

### Clean Docker on VPS
```bash
ssh user@VPS_IP

# Stop old containers
docker ps -a | grep Exited | awk '{print $1}' | xargs docker rm

# Remove old images
docker images | grep youtube-trending-fetcher | tail -n +4 | awk '{print $3}' | xargs docker rmi

# Clean system
docker system prune -f
```

## 📈 Monitoring URLs

| Endpoint | URL | Purpose |
|----------|-----|---------|
| API Docs | `http://VPS_IP:8000/docs` | Interactive API testing |
| Health | `http://VPS_IP:8000/health` | Service health status |
| Metrics | `http://VPS_IP:8000/metrics` | Application metrics |
| Root | `http://VPS_IP:8000/` | API information |

## 🔐 Security Checklist

- [ ] GitHub credentials configured
- [ ] Docker Hub credentials configured
- [ ] VPS SSH credentials configured
- [ ] YouTube API key configured
- [ ] Global environment variables set:
  - [ ] VPS_HOST
  - [ ] DOCKER_REGISTRY
  - [ ] GIT_REPO_URL
- [ ] No sensitive data hardcoded in Jenkinsfile
- [ ] VPS port 8000 opened in firewall
- [ ] VPS SSH port 22 accessible
- [ ] Jenkins server can reach VPS IP

## 📞 Emergency Contacts

**If deployment fails:**
1. Check Jenkins console output
2. Check VPS logs: `docker logs youtube-trending-fetcher-app`
3. Check health: `curl http://VPS_IP:8000/health`
4. Read [JENKINS_SETUP.md](JENKINS_SETUP.md)

**Common Exit Codes:**
- Exit 0: Success
- Exit 1: General error
- Exit 137: Out of memory
- Exit 143: SIGTERM (normal shutdown)

---

**Last Updated:** 2025-11-12
