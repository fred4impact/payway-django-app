# CI/CD Pipeline Documentation

## Overview
This document outlines the Continuous Integration and Continuous Deployment pipeline for the PayWay Django application. The pipeline includes security scanning, testing, building, and deployment stages.

## CI Flow Stages

### 1. Checkout
- Clone the repository
- Checkout the target branch/commit
- Setup environment

### 2. Unit Testing
- Install dependencies
- Run Django unit tests
- Generate test coverage reports
- Fail pipeline if tests fail

### 3. SAST (Static Application Security Testing)
- Run security scanners on source code
- Check for vulnerabilities, secrets, and security issues
- Generate security reports
- Fail pipeline on critical security issues

### 4. Build Docker Image
- Build Docker image from Dockerfile
- Tag image with commit hash and branch name
- Optimize image layers

### 5. Image Security Scan
- Scan built Docker image for vulnerabilities
- Check for outdated packages and CVE issues
- Generate security reports
- Fail pipeline on critical vulnerabilities

### 6. Push Image to GitHub Container Registry
- Authenticate with GitHub Container Registry
- Push tagged images
- Update latest tags for main branch

### 7. DAST (Dynamic Application Security Testing)
- Deploy application to staging environment
- Run dynamic security tests
- Test for runtime vulnerabilities
- Generate security reports

## GitHub Actions Implementation

### Workflow File: `.github/workflows/ci-cd.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: |
          python manage.py test --verbosity=2
          coverage run --source='.' manage.py test
          coverage report

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3

  security-scan:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run SAST scan
        uses: github/codeql-action/init@v2
        with:
          languages: python

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v2

      - name: Run Bandit security scan
        run: |
          pip install bandit
          bandit -r . -f json -o bandit-report.json

      - name: Run Safety check
        run: |
          pip install safety
          safety check --json --output safety-report.json

  build-and-scan:
    runs-on: ubuntu-latest
    needs: [test, security-scan]
    permissions:
      contents: read
      packages: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  push-image:
    runs-on: ubuntu-latest
    needs: build-and-scan
    permissions:
      contents: read
      packages: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  dast-scan:
    runs-on: ubuntu-latest
    needs: push-image
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to staging
        run: |
          # Deploy application to staging environment
          # This could use kubectl, docker-compose, or other deployment tools
          echo "Deploying to staging environment..."

      - name: Wait for deployment
        run: |
          # Wait for application to be ready
          sleep 30

      - name: Run OWASP ZAP scan
        uses: zaproxy/action-full-scan@v0.8.0
        with:
          target: 'https://staging.payway.com'
          rules_file_name: '.zap/rules.tsv'
          cmd_options: '-a'

      - name: Generate DAST report
        run: |
          # Generate and upload DAST scan reports
          echo "DAST scan completed"
```

## Jenkins Implementation

### Jenkinsfile

```groovy
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'ghcr.io'
        IMAGE_NAME = 'your-username/payway-django-app'
        DOCKER_CREDENTIALS = credentials('github-container-registry')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.COMMIT_HASH = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.BRANCH_NAME = env.BRANCH_NAME ?: 'main'
                }
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh '''
                    python3 -m venv venv
                    source venv/bin/activate
                    pip install -r requirements.txt
                    python manage.py test --verbosity=2
                    coverage run --source='.' manage.py test
                    coverage report
                    coverage html
                '''
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('SAST Scan') {
            parallel {
                stage('CodeQL Analysis') {
                    steps {
                        sh '''
                            # Install CodeQL CLI
                            wget https://github.com/github/codeql-action/releases/latest/download/codeql-bundle-linux64.tar.gz
                            tar -xzf codeql-bundle-linux64.tar.gz
                            
                            # Initialize CodeQL database
                            ./codeql/codeql database create codeql_db --language=python
                            
                            # Analyze code
                            ./codeql/codeql database analyze codeql_db python-security-and-quality.qls --format=sarif-latest --output=codeql-results.sarif
                        '''
                    }
                }
                
                stage('Bandit Security Scan') {
                    steps {
                        sh '''
                            source venv/bin/activate
                            pip install bandit
                            bandit -r . -f json -o bandit-report.json
                        '''
                    }
                }
                
                stage('Safety Check') {
                    steps {
                        sh '''
                            source venv/bin/activate
                            pip install safety
                            safety check --json --output safety-report.json
                        '''
                    }
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${env.IMAGE_NAME}:${env.COMMIT_HASH}")
                    docker.tag("${env.IMAGE_NAME}:${env.COMMIT_HASH}", "${env.IMAGE_NAME}:latest")
                }
            }
        }
        
        stage('Image Security Scan') {
            steps {
                sh '''
                    # Install Trivy
                    wget https://github.com/aquasecurity/trivy/releases/latest/download/trivy_0.45.0_Linux-64bit.tar.gz
                    tar -xzf trivy_0.45.0_Linux-64bit.tar.gz
                    
                    # Scan Docker image
                    ./trivy image --format json --output trivy-results.json ${env.IMAGE_NAME}:${env.COMMIT_HASH}
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-results.json', fingerprint: true
                }
            }
        }
        
        stage('Push to GitHub Container Registry') {
            steps {
                script {
                    docker.withRegistry("https://${env.DOCKER_REGISTRY}", env.DOCKER_CREDENTIALS) {
                        docker.image("${env.IMAGE_NAME}:${env.COMMIT_HASH}").push()
                        docker.image("${env.IMAGE_NAME}:latest").push()
                    }
                }
            }
        }
        
        stage('DAST Scan') {
            steps {
                sh '''
                    # Deploy to staging environment
                    echo "Deploying to staging environment..."
                    
                    # Wait for deployment
                    sleep 30
                    
                    # Install OWASP ZAP
                    wget https://github.com/zaproxy/zaproxy/releases/latest/download/zap_2.15.0_linux.tar.gz
                    tar -xzf zap_2.15.0_linux.tar.gz
                    
                    # Run ZAP scan
                    ./zap.sh -cmd -quickurl https://staging.payway.com -quickout dast-results.html
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'dast-results.html', fingerprint: true
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
```

## Security Scanning Tools

### SAST Tools
- **CodeQL**: GitHub's semantic code analysis engine
- **Bandit**: Python security linter
- **Safety**: Checks Python dependencies for known vulnerabilities
- **Semgrep**: Fast, lightweight static analysis

### Container Security Tools
- **Trivy**: Comprehensive container vulnerability scanner
- **Clair**: Container vulnerability analysis service
- **Snyk**: Container and dependency vulnerability scanning

### DAST Tools
- **OWASP ZAP**: Web application security scanner
- **Burp Suite**: Web application security testing platform
- **Nikto**: Web server scanner

## Configuration Files

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "payway.wsgi:application"]
```

### .dockerignore
```
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
.env
.venv
.git/
.gitignore
README.md
*.md
tests/
test_*.py
.coverage
htmlcov/
.pytest_cache/
```

## Best Practices

### Security
- Always scan for vulnerabilities before deployment
- Use multi-stage Docker builds to reduce attack surface
- Implement least privilege principle
- Regular dependency updates and security patches

### Performance
- Use Docker layer caching
- Implement parallel job execution where possible
- Optimize Docker image size
- Use appropriate base images

### Monitoring
- Implement comprehensive logging
- Set up alerts for pipeline failures
- Monitor security scan results
- Track deployment metrics

## Next Steps

1. **Setup GitHub Secrets**: Configure necessary secrets for authentication
2. **Configure Staging Environment**: Set up staging environment for DAST scanning
3. **Implement Notifications**: Add Slack/email notifications for pipeline status
4. **Add Performance Testing**: Include load testing in the pipeline
5. **Implement Rollback Strategy**: Plan for quick rollbacks if issues arise
6. **Add Compliance Scanning**: Include compliance and license checking
7. **Setup Monitoring**: Implement application and infrastructure monitoring

## Troubleshooting

### Common Issues
- **Authentication Errors**: Check GitHub token permissions
- **Build Failures**: Verify Dockerfile and dependencies
- **Scan Timeouts**: Adjust timeout values for large codebases
- **Registry Push Failures**: Verify registry permissions and credentials

### Debug Commands
```bash
# Check Docker image layers
docker history <image-name>

# Inspect image contents
docker run --rm -it <image-name> /bin/bash

# Check security scan results
cat trivy-results.json | jq '.'

# Verify registry authentication
docker login ghcr.io
```
