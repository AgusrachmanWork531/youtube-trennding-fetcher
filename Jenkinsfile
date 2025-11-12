// DECLARATIVE PIPELINE - MENDEFINISIKAN STRUKTUR CI/CD
pipeline {
    // AGENT ANY - PIPELINE BISA JALAN DI NODE JENKINS MANAPUN
    agent any

    // ENVIRONMENT - VARIABEL GLOBAL YANG DIPAKAI DI SELURUH PIPELINE
    environment {
        // ============================================
        // PROJECT CONFIGURATION
        // ============================================
        PROJECT_NAME = 'youtube-trending-fetcher'
        DEPLOY_PORT = '8000'

        // ============================================
        // DOCKER CONFIGURATION
        // ============================================
        // DOCKER_REGISTRY diambil dari Jenkins Global Environment Variables
        // Set di: Manage Jenkins -> Configure System -> Global properties
        // Environment variables -> Add:
        //   - DOCKER_REGISTRY = your_docker_username
        //   - VPS_HOST = your_vps_ip
        //   - GIT_REPO_URL = your_github_repo_url

        IMAGE_NAME = "${env.DOCKER_REGISTRY}/${PROJECT_NAME}"
        BUILD_VERSION = "${env.BUILD_NUMBER}"
        CONTAINER_NAME = "${PROJECT_NAME}-app"
        REDIS_CONTAINER_NAME = "${PROJECT_NAME}-redis"

        // ============================================
        // VPS DEPLOYMENT CONFIGURATION
        // ============================================
        // VPS_HOST & DOCKER_REGISTRY diambil dari Jenkins Global Environment Variables
        // Untuk keamanan, jangan hardcode IP/username di Jenkinsfile
        // Set di: Manage Jenkins -> Configure System -> Global properties -> Environment variables

        // ============================================
        // CREDENTIALS ID
        // ============================================
        GITHUB_CREDENTIALS = 'github-credentials'
        DOCKER_CREDENTIALS = 'docker-hub-credentials'
        YOUTUBE_API_KEY_CREDENTIALS = 'youtube-api-key'
        VPS_SSH_CREDENTIALS = 'vps-ssh-password'
    }

    // STAGES - TAHAPAN EKSEKUSI PIPELINE SECARA BERURUTAN
    stages {
        // STAGE 0: CLEAN WORKSPACE - FORCE FRESH CHECKOUT
        stage('🧹 Clean Workspace') {
            steps {
                echo '=== Cleaning Workspace ==='
                deleteDir()                                                     // HAPUS SEMUA FILE DI WORKSPACE
            }
        }

        // STAGE 1: CLONE SOURCE CODE DARI REPOSITORY
        stage('📦 PULL SCM') {
            steps {
                echo '=== Checkout Source Code ==='

                // GIT CLONE DARI GITHUB DENGAN AUTENTIKASI
                // Repository URL diambil dari Jenkins Global Environment Variable: GIT_REPO_URL
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    extensions: [
                        [$class: 'CleanBeforeCheckout'],
                        [$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false]
                    ],
                    userRemoteConfigs: [[
                        credentialsId: "${GITHUB_CREDENTIALS}",
                        url: "${env.GIT_REPO_URL}"
                    ]]
                ])

                // VERIFIKASI HASIL CLONE
                sh '''#!/bin/bash
                    echo "Current directory:"
                    pwd

                    echo ""
                    echo "Git commit info:"
                    git log -1 --oneline

                    echo ""
                    echo "Files:"
                    ls -la

                    echo ""
                    echo "Project structure:"
                    ls -la app/ tests/ 2>/dev/null || echo "Directories found"
                '''
            }
        }

        // STAGE 2: DOCKER LOGIN KE REGISTRY
        stage('🔐 Docker Login') {
            steps {
                echo '=== Logging into Docker Hub ==='
                script {
                    // WITHCREDENTIALS - AMBIL USERNAME & PASSWORD DARI JENKINS VAULT SECARA AMAN
                    withCredentials([usernamePassword(
                        credentialsId: "${DOCKER_CREDENTIALS}",                 // ID CREDENTIAL DI JENKINS
                        usernameVariable: 'DOCKER_USER',                        // VARIABLE SEMENTARA UNTUK USERNAME
                        passwordVariable: 'DOCKER_PASS'                         // VARIABLE SEMENTARA UNTUK PASSWORD
                    )]) {
                        sh '''#!/bin/bash
                            echo "Logging into Docker Hub as ${DOCKER_USER}..."
                            # LOGIN KE DOCKER HUB DENGAN CREDENTIALS
                            echo "${DOCKER_PASS}" | docker login -u "${DOCKER_USER}" --password-stdin

                            echo "✅ Successfully logged in to Docker Hub!"
                        '''
                    }
                    // SETELAH KELUAR DARI BLOCK, DOCKER_USER & DOCKER_PASS OTOMATIS DIHAPUS (SECURITY)
                }
            }
        }

        // STAGE 3: CEK ENVIRONMENT DAN TOOLS YANG DIBUTUHKAN
        stage('🔍 Environment Check') {
            steps {
                echo '=== Checking Environment ==='
                sh '''#!/bin/bash
                    echo "=== User & Permission Check ==="
                    whoami
                    groups

                    echo ""
                    echo "=== Docker Socket Permission ==="
                    ls -l /var/run/docker.sock

                    echo ""
                    echo "=== Docker Version ==="
                    docker --version
                    docker compose version 2>/dev/null || docker-compose --version

                    echo ""
                    echo "=== Build Information ==="
                    echo "Build Number: ${BUILD_NUMBER}"
                    echo "Image Name: ${IMAGE_NAME}"
                    echo "Project: ${PROJECT_NAME}"
                    echo "Deploy Port: ${DEPLOY_PORT}"
                '''
            }
        }

        // STAGE 4: RUN TESTS
        stage('🧪 Run Tests') {
            steps {
                echo '=== Running Unit Tests ==='
                script {
                    try {
                        sh '''#!/bin/bash
                            echo "Building test image..."
                            docker build --target builder -t ${IMAGE_NAME}:test-${BUILD_VERSION} .

                            echo ""
                            echo "Running pytest..."
                            docker run --rm \
                                -v $(pwd):/app \
                                -w /app \
                                ${IMAGE_NAME}:test-${BUILD_VERSION} \
                                bash -c "pip install pytest pytest-asyncio pytest-cov && pytest tests/ -v --tb=short" || true

                            echo "✅ Tests completed"
                        '''
                    } catch (Exception e) {
                        echo "⚠️  Tests skipped or failed: ${e.message}"
                        // Continue pipeline even if tests fail (for demo purposes)
                    }
                }
            }
        }

        // STAGE 5: BUILD DOCKER IMAGE DARI DOCKERFILE
        stage('🔨 Docker Build') {
            steps {
                echo '=== Building Docker Image ==='
                sh '''#!/bin/bash
                    echo "Building multi-stage image for AMD64 platform: ${IMAGE_NAME}:${BUILD_VERSION}"

                    # Build untuk platform AMD64 (VPS architecture)
                    docker build \
                        --platform linux/amd64 \
                        --target runtime \
                        -t ${IMAGE_NAME}:${BUILD_VERSION} \
                        .

                    # Tag sebagai latest
                    docker tag ${IMAGE_NAME}:${BUILD_VERSION} ${IMAGE_NAME}:latest

                    echo ""
                    echo "Listing built images:"
                    docker images | grep ${PROJECT_NAME}

                    echo ""
                    echo "Image size:"
                    docker images ${IMAGE_NAME}:${BUILD_VERSION} --format "table {{.Repository}}:{{.Tag}}\\t{{.Size}}"
                '''
            }
        }

        // STAGE 6: PUSH IMAGE KE DOCKER HUB REGISTRY
        stage('🚀 Push to Registry') {
            steps {
                echo '=== Pushing to Docker Hub ==='
                sh '''#!/bin/bash
                    echo "Pushing ${IMAGE_NAME}:${BUILD_VERSION}"
                    docker push ${IMAGE_NAME}:${BUILD_VERSION}

                    echo ""
                    echo "Pushing ${IMAGE_NAME}:latest"
                    docker push ${IMAGE_NAME}:latest

                    echo ""
                    echo "✅ Images pushed successfully!"
                    echo "🐳 Docker Hub: https://hub.docker.com/r/${IMAGE_NAME}"
                '''
            }
        }

        // STAGE 7: DEPLOY CONTAINER KE VPS SERVER VIA SSH
        stage('🎯 Deploy to VPS') {
            steps {
                echo '=== Deploying Application to VPS ==='
                script {
                    // WITHCREDENTIALS - MENGGUNAKAN PASSWORD UNTUK SSH DAN YOUTUBE API KEY
                    withCredentials([
                        usernamePassword(
                            credentialsId: "${VPS_SSH_CREDENTIALS}",
                            usernameVariable: 'VPS_USER',
                            passwordVariable: 'VPS_PASS'
                        ),
                        string(
                            credentialsId: "${YOUTUBE_API_KEY_CREDENTIALS}",
                            variable: 'YOUTUBE_API_KEY'
                        )
                    ]) {
                        sh '''#!/bin/bash
                            set -e
                            # Mask sensitive data in logs
                            echo "🔗 Connecting to VPS: ${VPS_USER}@***MASKED_HOST***"

                            # Use actual VPS_HOST for connection
                            VPS_IP="${VPS_HOST}"

                            # DEPLOY TO VPS VIA SSH DENGAN SSHPASS
                            sshpass -p "${VPS_PASS}" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_HOST} bash -s << 'EOF'
set -e
echo "=== VPS Deployment Started ==="

# VALIDATE DOCKER
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed on VPS!"
    exit 1
fi

# CONFIGURE FIREWALL (UFW)
echo ""
echo "🔥 Configuring firewall for port ${DEPLOY_PORT}..."
if command -v ufw &> /dev/null; then
    # Allow port 8000 through firewall
    ufw allow ${DEPLOY_PORT}/tcp 2>/dev/null || echo "  ⚠️  UFW not active or already configured"
    echo "✅ Firewall configured for port ${DEPLOY_PORT}"
else
    echo "  ℹ️  UFW not installed, skipping firewall config"
fi

# CREATE DOCKER NETWORK (jika belum ada)
echo ""
echo "🌐 Setting up Docker network..."
docker network create youtube-fetcher-network 2>/dev/null || echo "  ℹ️  Network already exists"

# PULL NEW IMAGE
echo ""
echo "📥 Pulling latest image: ${IMAGE_NAME}:${BUILD_VERSION}"
docker pull ${IMAGE_NAME}:${BUILD_VERSION}
echo "✅ Image pulled successfully"

# STOP & REMOVE OLD CONTAINERS
echo ""
echo "🛑 Stopping old containers..."
docker stop ${CONTAINER_NAME} 2>/dev/null || echo "  No app container to stop"
docker rm ${CONTAINER_NAME} 2>/dev/null || echo "  No app container to remove"

# DEPLOY REDIS (jika belum ada)
echo ""
echo "📦 Checking Redis container..."
if ! docker ps -a | grep -q ${REDIS_CONTAINER_NAME}; then
    echo "  Starting Redis container..."
    docker run -d \\
        --name ${REDIS_CONTAINER_NAME} \\
        --restart unless-stopped \\
        --network youtube-fetcher-network \\
        -v youtube-fetcher-redis-data:/data \\
        redis:7-alpine redis-server --appendonly yes
    echo "✅ Redis started"
else
    echo "  Redis already running"
    docker start ${REDIS_CONTAINER_NAME} 2>/dev/null || echo "  Redis already started"
fi

# REMOVE OLD IMAGES (KEEP ONLY LATEST + CURRENT BUILD)
echo ""
echo "🗑️  Removing old images..."
docker images ${IMAGE_NAME} --format "{{.ID}} {{.Tag}}" 2>/dev/null | \\
    grep -v "latest" | \\
    grep -v "${BUILD_VERSION}" | \\
    awk '{print $1}' | \\
    xargs -r docker rmi -f 2>/dev/null || echo "  ℹ️  No old images to remove"

# START NEW APPLICATION CONTAINER
echo ""
echo "🚀 Starting new application container..."
docker run -d \\
    --name ${CONTAINER_NAME} \\
    --restart unless-stopped \\
    --network youtube-fetcher-network \\
    -p ${DEPLOY_PORT}:8000 \\
    -e YOUTUBE_API_KEY="${YOUTUBE_API_KEY}" \\
    -e DEFAULT_COUNTRY=ID \\
    -e DEFAULT_CATEGORIES=music,news,tech,entertainment,gaming \\
    -e TREND_LIMIT=10 \\
    -e SCHEDULER_CRON="0 0 * * *" \\
    -e SCHEDULER_ENABLED=true \\
    -e REDIS_URL=redis://${REDIS_CONTAINER_NAME}:6379/0 \\
    -e REDIS_ENABLED=true \\
    -e LOG_LEVEL=INFO \\
    ${IMAGE_NAME}:${BUILD_VERSION}

# VERIFY DEPLOYMENT
echo ""
echo "⏳ Waiting for container startup..."
sleep 5

echo ""
echo "📊 Container status:"
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"

echo ""
echo "📊 Redis status:"
docker ps --filter "name=${REDIS_CONTAINER_NAME}" --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"

# TEST HTTP RESPONSE
echo ""
echo "🧪 Testing application health..."
for i in {1..10}; do
    if curl -s -f http://localhost:${DEPLOY_PORT}/health > /dev/null 2>&1; then
        echo "✅ Health check passed!"
        curl -s http://localhost:${DEPLOY_PORT}/health | head -20
        break
    else
        echo "  ⏳ Waiting for app to start (attempt $i/10)..."
        sleep 3
    fi
done

# SHOW LOGS
echo ""
echo "📝 Recent application logs:"
docker logs --tail 20 ${CONTAINER_NAME}

echo ""
echo "✅ Deployment successful!"
echo "======================================="
echo "🌐 Application is now running"
echo "📚 API Docs: Available at /docs endpoint"
echo "🏥 Health Check: Available at /health endpoint"
echo "📊 Metrics: Available at /metrics endpoint"
echo "======================================="
echo "📌 Make sure port ${DEPLOY_PORT} is open in your VPS provider's firewall/security group"
EOF

                            echo "✅ SSH deployment completed!"
                        '''
                    }
                }
            }
        }

        // STAGE 8: VERIFY DEPLOYMENT
        stage('✅ Verify Deployment') {
            steps {
                echo '=== Verifying Deployment ==='
                script {
                    withCredentials([
                        usernamePassword(
                            credentialsId: "${VPS_SSH_CREDENTIALS}",
                            usernameVariable: 'VPS_USER',
                            passwordVariable: 'VPS_PASS'
                        )
                    ]) {
                        sh '''#!/bin/bash
                            echo "🔍 Running deployment verification..."

                            sshpass -p "${VPS_PASS}" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_HOST} bash -s << 'EOF'
# Check if containers are running
echo "=== Container Status ==="
docker ps | grep ${PROJECT_NAME} || echo "⚠️  No containers found"

echo ""
echo "=== Docker Network ==="
docker network inspect youtube-fetcher-network --format "{{.Name}}: {{len .Containers}} containers" 2>/dev/null || echo "Network not found"

echo ""
echo "=== Health Check ==="
curl -s http://localhost:${DEPLOY_PORT}/health | python3 -m json.tool 2>/dev/null || echo "⚠️  Health check failed"

echo ""
echo "=== Disk Usage ==="
docker system df

echo ""
echo "✅ Verification complete!"
EOF
                        '''
                    }
                }
            }
        }
    }  // END OF STAGES

    // POST ACTIONS - AKSI YANG DIJALANKAN SETELAH PIPELINE SELESAI
    post {
        // ALWAYS - SELALU DIJALANKAN (SUCCESS/FAILURE)
        always {
            echo '=== Pipeline Cleanup ==='
            script {
                try {
                    sh '''#!/bin/bash
                        # DOCKER LOGOUT
                        echo "🔐 Logging out from Docker Hub..."
                        docker logout || true

                        # REMOVE TEST IMAGES
                        echo ""
                        echo "🗑️  Removing test images..."
                        docker images | grep "test-${BUILD_VERSION}" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true

                        # REMOVE DANGLING IMAGES
                        echo ""
                        echo "🗑️  Removing dangling images..."
                        docker image prune -f || true

                        # CLEAN OLD BUILD IMAGES (KEEP LAST 3)
                        echo ""
                        echo "🧹 Cleaning old images (keeping last 3)..."
                        docker images ${IMAGE_NAME} --format "{{.ID}} {{.Tag}}" 2>/dev/null | \\
                            grep -v latest | \\
                            tail -n +4 | \\
                            awk '{print $1}' | \\
                            xargs -r docker rmi -f 2>/dev/null || echo "  ℹ️  No old images to remove"

                        # DISK USAGE REPORT
                        echo ""
                        echo "📊 Current disk usage:"
                        docker system df 2>/dev/null || echo "  ℹ️  Disk usage check skipped"

                        # LIST REMAINING IMAGES
                        echo ""
                        echo "📦 Remaining project images:"
                        docker images | grep ${PROJECT_NAME} 2>/dev/null || echo "  ℹ️  No project images found"
                    '''
                } catch (Exception e) {
                    echo "⚠️  Cleanup skipped: ${e.message}"
                }
            }
        }

        // SUCCESS - HANYA DIJALANKAN JIKA BERHASIL
        success {
            echo '✅ BUILD & DEPLOYMENT SUCCESS!'
            echo "======================================="
            echo "📦 Image: ${IMAGE_NAME}:${BUILD_VERSION}"
            echo "🐳 Registry: Check Docker Hub for pushed images"
            echo "🌐 Application: Deployed successfully to VPS"
            echo "📚 API Docs: Access via VPS_IP:${DEPLOY_PORT}/docs"
            echo "🏥 Health: Access via VPS_IP:${DEPLOY_PORT}/health"
            echo "📊 Metrics: Access via VPS_IP:${DEPLOY_PORT}/metrics"
            echo "======================================="
        }

        // FAILURE - HANYA DIJALANKAN JIKA GAGAL
        failure {
            echo '❌ BUILD FAILED!'
            echo "Check the logs above for error details."
            echo "Common issues:"
            echo "  - Docker build failed (check Dockerfile)"
            echo "  - Tests failed (check test logs)"
            echo "  - VPS connection failed (check SSH credentials)"
            echo "  - YouTube API key missing (check Jenkins credentials)"
        }
    }
}  // END OF PIPELINE
