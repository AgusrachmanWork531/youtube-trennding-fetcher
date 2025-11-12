# Jenkins CI/CD Setup Guide

Panduan lengkap untuk setup Jenkins pipeline untuk YouTube Trending Fetcher.

## Prerequisites

### 1. Jenkins Server
- Jenkins version 2.x+
- Plugins yang dibutuhkan:
  - Pipeline
  - Git
  - Docker Pipeline
  - Credentials Binding
  - SSH Agent

### 2. Tools di Jenkins Server
```bash
# Docker
docker --version

# Docker Compose
docker compose version

# SSH Pass (untuk deployment ke VPS)
sudo apt-get install sshpass

# Python (untuk JSON formatting)
python3 --version
```

### 3. VPS Target
- Docker installed
- Port 8000 terbuka
- SSH access enabled
- Firewall configured

## Jenkins Credentials Setup

### 1. GitHub Credentials

**Type:** Username with password

**ID:** `github-credentials`

**Username:** Your GitHub username

**Password:** GitHub Personal Access Token

**Cara membuat GitHub PAT:**
1. GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Pilih scope: `repo` (full control)
4. Copy token dan simpan di Jenkins

### 2. Docker Hub Credentials

**Type:** Username with password

**ID:** `docker-hub-credentials`

**Username:** `tlkmags` (atau username Docker Hub Anda)

**Password:** Docker Hub password atau access token

**Cara membuat Docker Hub token:**
1. Docker Hub → Account Settings → Security → New Access Token
2. Description: Jenkins CI/CD
3. Permissions: Read & Write
4. Copy token dan simpan di Jenkins

### 3. VPS SSH Credentials

**Type:** Username with password

**ID:** `vps-ssh-password`

**Username:** VPS username (e.g., `root` atau `ubuntu`)

**Password:** VPS SSH password

**Note:** Lebih aman pakai SSH key, tapi untuk simplicity kita pakai password.

### 4. YouTube API Key

**Type:** Secret text

**ID:** `youtube-api-key`

**Secret:** Your YouTube Data API v3 key

**Cara mendapatkan:**
1. https://console.cloud.google.com/apis/credentials
2. Create Credentials → API Key
3. Restrict key ke YouTube Data API v3
4. Copy dan simpan di Jenkins

## Jenkins Global Environment Variables

Set di: **Manage Jenkins** → **Configure System** → **Global properties** → **Environment variables**

**IMPORTANT:** Jangan hardcode nilai sensitif di Jenkinsfile. Gunakan environment variables untuk keamanan.

| Name | Value Example | Description |
|------|---------------|-------------|
| `VPS_HOST` | `202.155.90.93` | IP address VPS target deployment |
| `DOCKER_REGISTRY` | `tlkmags` | Docker Hub username/registry |
| `GIT_REPO_URL` | `https://github.com/user/repo.git` | GitHub repository URL |

**Cara Setting:**
1. Jenkins Dashboard → **Manage Jenkins**
2. **Configure System**
3. Scroll ke **Global properties**
4. ✅ Check **Environment variables**
5. Click **Add**
6. Name: `VPS_HOST`, Value: `your_vps_ip`
7. Repeat untuk `DOCKER_REGISTRY` dan `GIT_REPO_URL`
8. **Save**

## Pipeline Configuration

### 1. Create New Pipeline Job

1. Jenkins Dashboard → **New Item**
2. Enter name: `youtube-trending-fetcher`
3. Select: **Pipeline**
4. Click **OK**

### 2. Configure Pipeline

**General:**
- ✅ GitHub project
- Project url: `https://github.com/AgusrachmanWork531/youtube-trennding-fetcher`

**Build Triggers:**
- ✅ GitHub hook trigger for GITScm polling (jika ada webhook)
- ✅ Poll SCM: `H/5 * * * *` (check setiap 5 menit)

**Pipeline:**
- Definition: **Pipeline script from SCM**
- SCM: **Git**
- Repository URL: `https://github.com/AgusrachmanWork531/youtube-trennding-fetcher.git`
- Credentials: `github-credentials`
- Branch: `*/main`
- Script Path: `Jenkinsfile`

### 3. Save Configuration

## Pipeline Stages Explanation

### Stage 1: 🧹 Clean Workspace
```groovy
deleteDir()  // Hapus semua file untuk fresh start
```

### Stage 2: 📦 Pull SCM
```groovy
checkout from GitHub
git log -1  // Show last commit
ls -la      // Verify files
```

### Stage 3: 🔐 Docker Login
```groovy
docker login dengan credentials dari Jenkins Vault
```

### Stage 4: 🔍 Environment Check
```groovy
whoami          // Check user
docker --version // Verify Docker
groups          // Check permissions
```

### Stage 5: 🧪 Run Tests
```groovy
docker build --target builder  // Build test image
pytest tests/ -v              // Run unit tests
```

### Stage 6: 🔨 Docker Build
```groovy
docker build --platform linux/amd64  // Build for VPS
docker tag as :latest                // Tag latest
```

### Stage 7: 🚀 Push to Registry
```groovy
docker push IMAGE:BUILD_NUMBER
docker push IMAGE:latest
```

### Stage 8: 🎯 Deploy to VPS
```groovy
sshpass + ssh ke VPS
docker pull IMAGE:latest
docker stop old container
docker run new container with Redis
Configure firewall
```

### Stage 9: ✅ Verify Deployment
```groovy
Check container status
Test health endpoint
Verify Redis connection
```

## VPS Deployment Architecture

```
VPS Server
├── Docker Network: youtube-fetcher-network
│
├── Redis Container
│   ├── Name: youtube-trending-fetcher-redis
│   ├── Image: redis:7-alpine
│   ├── Port: 6379 (internal)
│   ├── Volume: youtube-fetcher-redis-data
│   └── Restart: unless-stopped
│
└── App Container
    ├── Name: youtube-trending-fetcher-app
    ├── Image: tlkmags/youtube-trending-fetcher:latest
    ├── Port: 8000:8000 (external:internal)
    ├── Env Variables:
    │   ├── YOUTUBE_API_KEY (from Jenkins)
    │   ├── REDIS_URL=redis://redis:6379/0
    │   ├── DEFAULT_COUNTRY=ID
    │   └── SCHEDULER_ENABLED=true
    └── Restart: unless-stopped
```

## Environment Variables Passed to Container

```bash
YOUTUBE_API_KEY      # From Jenkins credentials
DEFAULT_COUNTRY=ID
DEFAULT_CATEGORIES=music,news,tech,entertainment,gaming
TREND_LIMIT=10
SCHEDULER_CRON=0 0 * * *
SCHEDULER_ENABLED=true
REDIS_URL=redis://youtube-trending-fetcher-redis:6379/0
REDIS_ENABLED=true
LOG_LEVEL=INFO
```

## Firewall Configuration

Pipeline automatically configures UFW on VPS:

```bash
ufw allow 8000/tcp
```

**Manual verification on VPS:**
```bash
# Check UFW status
sudo ufw status

# Check if port is open
sudo netstat -tlnp | grep 8000
```

## Testing Deployment

### 1. From Jenkins Console

Pipeline akan otomatis test:
```bash
curl http://localhost:8000/health
```

### 2. From External

```bash
# Health check
curl http://VPS_IP:8000/health

# API docs
open http://VPS_IP:8000/docs

# Trending endpoint
curl "http://VPS_IP:8000/trending?country=ID&limit=5"

# Metrics
curl http://VPS_IP:8000/metrics
```

### 3. SSH to VPS

```bash
# Check containers
ssh user@VPS_IP
docker ps | grep youtube-trending-fetcher

# Check logs
docker logs youtube-trending-fetcher-app --tail 50

# Check Redis
docker exec -it youtube-trending-fetcher-redis redis-cli ping
```

## Troubleshooting

### Issue 1: Docker Build Failed

**Error:** `ERROR [builder X/Y] RUN pip install ...`

**Solution:**
```bash
# Check Dockerfile syntax
# Verify requirements.txt exists
# Check internet connection on Jenkins server
```

### Issue 2: Tests Failed

**Error:** `pytest: command not found`

**Solution:**
```groovy
// Pipeline already handles this with:
docker run ... bash -c "pip install pytest && pytest ..."
```

### Issue 3: Cannot Connect to VPS

**Error:** `ssh: connect to host X.X.X.X port 22: Connection refused`

**Solution:**
```bash
# Check VPS IP is correct
# Verify SSH credentials in Jenkins
# Check VPS firewall allows SSH (port 22)
# Test manual SSH: ssh user@VPS_IP
```

### Issue 4: Container Fails to Start

**Error:** `docker: Error response from daemon: Conflict`

**Solution:**
```bash
# SSH to VPS
docker ps -a | grep youtube-trending-fetcher
docker logs youtube-trending-fetcher-app

# Common causes:
# - Port 8000 already in use
# - YouTube API key invalid
# - Redis not running
```

### Issue 5: YouTube API Key Not Working

**Error:** `YOUTUBE_API_KEY environment variable is required`

**Solution:**
1. Check Jenkins credentials: `youtube-api-key` exists
2. Verify credential ID in Jenkinsfile
3. Check API key is valid in Google Console
4. Test manually:
```bash
docker exec youtube-trending-fetcher-app env | grep YOUTUBE_API_KEY
```

## Build History & Rollback

### View Build History

Jenkins Dashboard → youtube-trending-fetcher → Build History

### Rollback to Previous Version

```bash
# SSH to VPS
ssh user@VPS_IP

# List available images
docker images tlkmags/youtube-trending-fetcher

# Stop current container
docker stop youtube-trending-fetcher-app
docker rm youtube-trending-fetcher-app

# Run specific version
docker run -d \
  --name youtube-trending-fetcher-app \
  --restart unless-stopped \
  --network youtube-fetcher-network \
  -p 8000:8000 \
  -e YOUTUBE_API_KEY="your_key" \
  -e REDIS_URL=redis://youtube-trending-fetcher-redis:6379/0 \
  tlkmags/youtube-trending-fetcher:BUILD_NUMBER
```

## Monitoring

### 1. Jenkins Build Status

- Green: Build & deployment success
- Red: Build failed
- Blue: Build in progress

### 2. Application Logs

```bash
# Via SSH
ssh user@VPS_IP
docker logs -f youtube-trending-fetcher-app

# Last 100 lines
docker logs --tail 100 youtube-trending-fetcher-app
```

### 3. Application Metrics

```bash
# From VPS
curl http://localhost:8000/metrics

# From external
curl http://VPS_IP:8000/metrics
```

### 4. Docker Stats

```bash
# SSH to VPS
docker stats youtube-trending-fetcher-app youtube-trending-fetcher-redis
```

## Security Best Practices

1. **Never commit credentials** to repository
2. **Use Jenkins Credentials Vault** untuk semua secrets
3. **Rotate API keys regularly**
4. **Limit Docker Hub token** scope ke read/write only
5. **Use SSH keys** instead of password (production)
6. **Configure VPS firewall** properly
7. **Regular security updates** untuk Docker images

## Maintenance

### Daily
- Monitor Jenkins build status
- Check application health endpoint

### Weekly
- Review Docker disk usage
- Clean old images: `docker image prune -a`
- Check application logs for errors

### Monthly
- Update dependencies in requirements.txt
- Review and rotate credentials
- Update Docker base images
- Review VPS firewall rules

## Additional Resources

- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Docker Pipeline Plugin](https://plugins.jenkins.io/docker-workflow/)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Project README](README.md)

## Support

Jika ada masalah:
1. Check Jenkins console output
2. Check VPS logs: `docker logs youtube-trending-fetcher-app`
3. Check health endpoint: `curl http://VPS_IP:8000/health`
4. Review this documentation

---

**Happy CI/CD! 🚀**
