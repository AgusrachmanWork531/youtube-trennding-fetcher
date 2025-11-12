# Security Best Practices - Jenkins CI/CD

## Data Yang Di-Mask

### 1. Sensitive Information Tidak Di-Hardcode

**BEFORE (❌ Not Secure):**
```groovy
DOCKER_REGISTRY = 'tlkmags'  // Hardcoded username
url: 'https://github.com/AgusrachmanWork531/repo.git'  // Hardcoded repo
VPS_HOST = '202.155.90.93'  // Hardcoded IP
```

**AFTER (✅ Secure):**
```groovy
IMAGE_NAME = "${env.DOCKER_REGISTRY}/${PROJECT_NAME}"  // From Jenkins env
url: "${env.GIT_REPO_URL}"  // From Jenkins env
echo "🔗 Connecting to VPS: ${VPS_USER}@***MASKED_HOST***"  // Masked in logs
```

### 2. Credentials Management

Semua credentials disimpan di **Jenkins Credentials Vault**, bukan di code:

| Data | Storage Method | Access |
|------|----------------|--------|
| GitHub Token | Jenkins Credentials (Username+Password) | `${GITHUB_CREDENTIALS}` |
| Docker Hub Password | Jenkins Credentials (Username+Password) | `${DOCKER_CREDENTIALS}` |
| VPS SSH Password | Jenkins Credentials (Username+Password) | `${VPS_SSH_CREDENTIALS}` |
| YouTube API Key | Jenkins Credentials (Secret Text) | `${YOUTUBE_API_KEY_CREDENTIALS}` |
| VPS IP | Jenkins Global Environment Variables | `${env.VPS_HOST}` |
| Docker Registry | Jenkins Global Environment Variables | `${env.DOCKER_REGISTRY}` |
| Git Repo URL | Jenkins Global Environment Variables | `${env.GIT_REPO_URL}` |

### 3. Masking in Console Output

**Sensitive data di-mask di console logs:**

```bash
# Original command
echo "Connecting to VPS: ${VPS_USER}@${VPS_HOST}"

# Masked in logs
echo "Connecting to VPS: ${VPS_USER}@***MASKED_HOST***"

# Actual command still uses real value
sshpass -p "${VPS_PASS}" ssh ${VPS_USER}@${VPS_HOST}
```

**Success message juga di-mask:**

```bash
# Instead of showing full URL
echo "🌐 Application URL: http://202.155.90.93:8000"

# Show generic message
echo "🌐 Application is now running"
echo "📚 API Docs: Available at /docs endpoint"
```

## Environment Variables Setup

### Jenkins Global Environment Variables

**Location:** Manage Jenkins → Configure System → Global properties → Environment variables

**Required Variables:**

```bash
VPS_HOST=your_vps_ip              # e.g., 202.155.90.93
DOCKER_REGISTRY=your_docker_user  # e.g., tlkmags
GIT_REPO_URL=your_git_repo_url    # e.g., https://github.com/user/repo.git
```

### Template File

File [.env.jenkins.example](.env.jenkins.example) berisi template untuk setup.

**IMPORTANT:**
- File `.env.jenkins.example` → Safe to commit (hanya contoh)
- File `.env.jenkins` → **NEVER commit** (berisi nilai asli)
- File `.env.production` → **NEVER commit** (berisi nilai asli)

### .gitignore Protection

```gitignore
# Protect sensitive files
.env
.env.local
.env.jenkins           # Jenkins actual values
.env.production        # Production values
.env.*.local          # Any local environment files
```

## Credentials Configuration

### 1. GitHub Credentials

```
ID: github-credentials
Type: Username with password
Username: your_github_username
Password: GitHub Personal Access Token (not your login password!)
```

**How to create GitHub PAT:**
1. GitHub → Settings → Developer settings
2. Personal access tokens → Tokens (classic)
3. Generate new token
4. Scope: `repo` (full control)
5. Copy token (shown only once!)

### 2. Docker Hub Credentials

```
ID: docker-hub-credentials
Type: Username with password
Username: your_docker_hub_username
Password: Docker Hub password or access token
```

**Recommended:** Use access token instead of password:
1. Docker Hub → Account Settings → Security
2. New Access Token
3. Description: Jenkins CI/CD
4. Permissions: Read & Write

### 3. VPS SSH Credentials

```
ID: vps-ssh-password
Type: Username with password
Username: root (or ubuntu, etc.)
Password: Your VPS SSH password
```

**More Secure Alternative:** Use SSH Private Key
```
Type: SSH Username with private key
Username: root
Private Key: Paste your private key
Passphrase: (if your key has passphrase)
```

### 4. YouTube API Key

```
ID: youtube-api-key
Type: Secret text
Secret: Your YouTube Data API v3 key
```

## Security Benefits

### ✅ What We Achieved

1. **No Hardcoded Secrets**
   - All sensitive data from Jenkins Vault
   - Easy to rotate credentials
   - No secrets in repository

2. **Masked Console Output**
   - VPS IP masked in logs
   - API keys never shown
   - Passwords hidden by Jenkins

3. **Credentials Rotation**
   - Change in Jenkins only (no code change)
   - Immediate effect
   - Audit trail in Jenkins

4. **Access Control**
   - Only Jenkins admins can see credentials
   - Fine-grained permissions
   - Encrypted at rest

5. **Repository Safety**
   - Safe to push to public GitHub
   - `.gitignore` protects local env files
   - Example files only

## Verification Checklist

Before deploying to production:

- [ ] No IP addresses in Jenkinsfile
- [ ] No usernames hardcoded
- [ ] No passwords in code
- [ ] No API keys in repository
- [ ] All credentials in Jenkins Vault
- [ ] All environment variables set in Jenkins
- [ ] `.gitignore` includes `.env.jenkins`
- [ ] `.env.jenkins.example` has dummy values only
- [ ] Console logs don't show sensitive data
- [ ] Success messages are generic

## Audit & Compliance

### Jenkins Audit Log

Jenkins tracks:
- Who created credentials
- When credentials were used
- Which builds used which credentials
- Failed authentication attempts

**View:** Manage Jenkins → System Log → Credentials

### Credential Usage

Check which jobs use which credentials:
```
Manage Jenkins → Credentials → [Select Credential] → Usage
```

### Best Practices

1. **Principle of Least Privilege**
   - Only give access to needed credentials
   - Separate credentials per environment (dev/staging/prod)
   - Limit credential scope

2. **Regular Rotation**
   - Rotate passwords every 90 days
   - Rotate API keys every 180 days
   - Update immediately if compromised

3. **Monitoring**
   - Monitor credential usage
   - Alert on failed authentications
   - Review access logs regularly

4. **Backup**
   - Backup Jenkins credentials (encrypted)
   - Document credential locations
   - Have recovery procedure

## Emergency Procedures

### If Credentials Compromised

1. **Immediately rotate in Jenkins:**
   - Manage Jenkins → Credentials → Update
   - No code changes needed

2. **Revoke on source:**
   - GitHub: Revoke PAT
   - Docker Hub: Revoke token
   - YouTube: Regenerate API key
   - VPS: Change password

3. **Verify:**
   - Check audit logs
   - Review recent builds
   - Scan for unauthorized access

### If IP/Host Exposed

1. **Update in Jenkins only:**
   - Manage Jenkins → Configure System
   - Update VPS_HOST variable
   - Re-run pipeline

2. **No code changes required**

## References

- [Jenkins Credentials Plugin](https://plugins.jenkins.io/credentials/)
- [Jenkins Security Best Practices](https://www.jenkins.io/doc/book/security/)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Docker Hub Access Tokens](https://docs.docker.com/docker-hub/access-tokens/)

---

**Last Updated:** 2025-11-12
**Security Level:** Production Ready ✅
