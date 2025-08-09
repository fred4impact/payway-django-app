# 🚀 PayWay Django App - Kubernetes & GitOps Deployment Guide

## 📋 Overview

This document outlines the recommended GitOps deployment strategy using ArgoCD and Kubernetes for the PayWay Django digital payment platform. The approach follows modern cloud-native practices with automated deployments, scalability, and high availability.

---

## 🎯 **GitOps Strategy with ArgoCD**

### **Core Principles**
- **Infrastructure as Code**: All K8s manifests stored in Git
- **Declarative Deployments**: ArgoCD automatically syncs desired state
- **Automated Rollbacks**: Git-based version control for deployments
- **Environment Parity**: Consistent deployments across dev/staging/prod
- **Security First**: Secrets management and RBAC integration

### **Repository Structure**
```
payway-infrastructure/
├── k8s/
│   ├── base/                    # Base Kustomize configurations
│   │   ├── django/
│   │   ├── postgresql/
│   │   ├── redis/
│   │   └── nginx/
│   ├── overlays/                # Environment-specific overlays
│   │   ├── development/
│   │   ├── staging/
│   │   └── production/
│   ├── argocd/                  # ArgoCD application definitions
│   └── monitoring/              # Prometheus, Grafana, etc.
├── helm/                        # Helm charts (alternative approach)
├── terraform/                   # Infrastructure provisioning
└── scripts/                     # Deployment and maintenance scripts
```

---

## 🏗️ **Kubernetes Architecture**

### **Application Components**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Ingress NGINX │    │   Django App    │
│   (Cloud/On-Prem)│    │   Controller    │    │   (Deployment)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cert Manager  │    │   ArgoCD        │    │   PostgreSQL    │
│   (SSL/TLS)     │    │   (GitOps)      │    │   (StatefulSet) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Cache   │    │   Monitoring    │    │   Storage       │
│   (Deployment)  │    │   Stack         │    │   (PVCs)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Resource Requirements**
- **Django App**: 2-4 replicas (CPU: 500m-1000m, Memory: 1-2Gi)
- **PostgreSQL**: 1-3 replicas (CPU: 1000m-2000m, Memory: 2-4Gi)
- **Redis**: 2-3 replicas (CPU: 250m-500m, Memory: 512Mi-1Gi)
- **Nginx**: 2-3 replicas (CPU: 250m-500m, Memory: 256Mi-512Mi)

---

## 🔧 **Kubernetes Manifests**

### **1. Django Application Deployment**

```yaml
# k8s/base/django/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payway-django
  labels:
    app: payway-django
    tier: backend
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: payway-django
  template:
    metadata:
      labels:
        app: payway-django
        tier: backend
    spec:
      containers:
      - name: django
        image: payway/django:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: payway-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: payway-secrets
              key: redis-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: payway-secrets
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: media-files
          mountPath: /app/media
        - name: static-files
          mountPath: /app/static
      volumes:
      - name: media-files
        persistentVolumeClaim:
          claimName: payway-media-pvc
      - name: static-files
        persistentVolumeClaim:
          claimName: payway-static-pvc
      imagePullSecrets:
      - name: payway-registry-secret
```

### **2. Service & Ingress Configuration**

```yaml
# k8s/base/django/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: payway-django-service
  labels:
    app: payway-django
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: payway-django
---
# k8s/base/django/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: payway-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "30"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
spec:
  tls:
  - hosts:
    - payway.example.com
    - api.payway.example.com
    secretName: payway-tls
  rules:
  - host: payway.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: payway-django-service
            port:
              number: 80
  - host: api.payway.example.com
    http:
      paths:
      - path: /api/
        pathType: Prefix
        backend:
          service:
            name: payway-django-service
            port:
              number: 80
```

### **3. Database Configuration**

```yaml
# k8s/base/postgresql/statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: payway-postgresql
  labels:
    app: payway-postgresql
spec:
  serviceName: payway-postgresql-service
  replicas: 1
  selector:
    matchLabels:
      app: payway-postgresql
  template:
    metadata:
      labels:
        app: payway-postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: payway
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: payway-secrets
              key: postgres-user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: payway-secrets
              key: postgres-password
        volumeMounts:
        - name: postgresql-data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: postgresql-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
      storageClassName: fast-ssd
```

### **4. Redis Configuration**

```yaml
# k8s/base/redis/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payway-redis
  labels:
    app: payway-redis
spec:
  replicas: 2
  selector:
    matchLabels:
      app: payway-redis
  template:
    metadata:
      labels:
        app: payway-redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - /etc/redis/redis.conf
        volumeMounts:
        - name: redis-config
          mountPath: /etc/redis
        - name: redis-data
          mountPath: /data
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "250m"
      volumes:
      - name: redis-config
        configMap:
          name: payway-redis-config
      - name: redis-data
        persistentVolumeClaim:
          claimName: payway-redis-pvc
```

---

## 🔐 **Secrets & Config Management**

### **1. External Secrets Operator (Recommended)**

```yaml
# k8s/base/secrets/external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: payway-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: payway-secrets
    type: Opaque
  data:
  - secretKey: database-url
    remoteRef:
      key: payway/database-url
  - secretKey: redis-url
    remoteRef:
      key: payway/redis-url
  - secretKey: secret-key
    remoteRef:
      key: payway/secret-key
  - secretKey: postgres-user
    remoteRef:
      key: payway/postgres-user
  - secretKey: postgres-password
    remoteRef:
      key: payway/postgres-password
```

### **2. ConfigMaps for Non-Sensitive Data**

```yaml
# k8s/base/django/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: payway-django-config
data:
  DEBUG: "False"
  ALLOWED_HOSTS: "payway.example.com,api.payway.example.com"
  CORS_ALLOWED_ORIGINS: "https://payway.example.com"
  STATIC_URL: "/static/"
  MEDIA_URL: "/media/"
  LOG_LEVEL: "INFO"
```

---

## 🚀 **ArgoCD Application Configuration**

### **1. Main Application**

```yaml
# k8s/argocd/payway-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payway-application
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/payway-infrastructure.git
    targetRevision: HEAD
    path: k8s/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: payway
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
```

### **2. Application Set (Multi-Environment)**

```yaml
# k8s/argocd/payway-appset.yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: payway-applications
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - env: development
        domain: dev.payway.example.com
        replicas: 2
      - env: staging
        domain: staging.payway.example.com
        replicas: 3
      - env: production
        domain: payway.example.com
        replicas: 4
  template:
    metadata:
      name: 'payway-{{env}}'
      namespace: argocd
      finalizers:
        - resources-finalizer.argocd.argoproj.io
    spec:
      project: default
      source:
        repoURL: https://github.com/your-org/payway-infrastructure.git
        targetRevision: HEAD
        path: k8s/overlays/{{env}}
      destination:
        server: https://kubernetes.default.svc
        namespace: payway-{{env}}
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
      revisionHistoryLimit: 10
```

---

## 📊 **Monitoring & Observability**

### **1. Prometheus ServiceMonitor**

```yaml
# k8s/base/monitoring/servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: payway-django-monitor
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: payway-django
  endpoints:
  - port: http
    path: /metrics/
    interval: 30s
    scrapeTimeout: 10s
  namespaceSelector:
    matchNames:
    - payway
```

### **2. Grafana Dashboard**

```yaml
# k8s/base/monitoring/grafana-dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: payway-grafana-dashboard
  labels:
    grafana_dashboard: "1"
data:
  payway-dashboard.json: |
    {
      "dashboard": {
        "title": "PayWay Django Dashboard",
        "panels": [
          {
            "title": "Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total[5m])",
                "legendFormat": "{{method}} {{endpoint}}"
              }
            ]
          },
          {
            "title": "Response Time",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                "legendFormat": "95th percentile"
              }
            ]
          }
        ]
      }
    }
```

---

## 🔄 **CI/CD Pipeline Integration**

### **1. GitHub Actions Workflow**

```yaml
# .github/workflows/deploy.yml
name: Deploy to Kubernetes
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: payway-django

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ env.REGISTRY }}/${{ github.repository }}:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
    
    - name: Update Kustomize image
      run: |
        cd k8s/base/django
        kustomize edit set image ${{ env.REGISTRY }}/${{ github.repository }}:${{ github.sha }}
    
    - name: Commit and push changes
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add k8s/base/django/kustomization.yaml
        git commit -m "Update image to ${{ github.sha }}"
        git push
    
    - name: Sync ArgoCD
      if: github.ref == 'refs/heads/main'
      run: |
        curl -X POST \
          -H "Authorization: Bearer ${{ secrets.ARGOCD_TOKEN }}" \
          -H "Content-Type: application/json" \
          -d '{"revision":"HEAD"}' \
          ${{ secrets.ARGOCD_SERVER }}/api/v1/applications/payway-application/sync
```

---

## 🚀 **Deployment Best Practices**

### **1. Blue-Green Deployment Strategy**

```yaml
# k8s/base/django/blue-green-deployment.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: payway-django-rollout
spec:
  replicas: 4
  strategy:
    blueGreen:
      activeService: payway-django-active
      previewService: payway-django-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
      prePromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: payway-django-preview
      postPromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: payway-django-active
  selector:
    matchLabels:
      app: payway-django
  template:
    metadata:
      labels:
        app: payway-django
    spec:
      containers:
      - name: django
        image: payway/django:latest
        ports:
        - containerPort: 8000
```

### **2. Horizontal Pod Autoscaler**

```yaml
# k8s/base/django/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: payway-django-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payway-django
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

---

## 🔒 **Security & Compliance**

### **1. Network Policies**

```yaml
# k8s/base/security/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: payway-network-policy
spec:
  podSelector:
    matchLabels:
      app: payway-django
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: cache
    ports:
    - protocol: TCP
      port: 6379
```

### **2. Pod Security Standards**

```yaml
# k8s/base/security/pod-security.yaml
apiVersion: v1
kind: PodSecurityPolicy
metadata:
  name: payway-restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'projected'
  - 'secret'
  - 'downwardAPI'
  - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  supplementalGroups:
    rule: 'MustRunAs'
    ranges:
    - min: 1
      max: 65535
  fsGroup:
    rule: 'MustRunAs'
    ranges:
    - min: 1
      max: 65535
  readOnlyRootFilesystem: true
```

---

## 📈 **Performance Optimization**

### **1. Resource Quotas**

```yaml
# k8s/base/quotas/resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: payway-quota
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    persistentvolumeclaims: "10"
    services: "20"
    secrets: "50"
    configmaps: "50"
```

### **2. Priority Classes**

```yaml
# k8s/base/scheduling/priority-class.yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: payway-high-priority
value: 1000000
globalDefault: false
description: "High priority for PayWay Django application"
```

---

## 🚨 **Disaster Recovery & Backup**

### **1. Velero Backup Configuration**

```yaml
# k8s/base/backup/velero-backup.yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: payway-daily-backup
spec:
  schedule: "0 2 * * *"
  template:
    includedNamespaces:
    - payway
    includedResources:
    - deployments
    - services
    - configmaps
    - secrets
    - persistentvolumeclaims
    - persistentvolumes
    storageLocation: default
    volumeSnapshotLocations:
    - default
    ttl: "720h"
```

### **2. Database Backup Job**

```yaml
# k8s/base/backup/db-backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: payway-db-backup
spec:
  schedule: "0 1 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15-alpine
            command:
            - /bin/sh
            - -c
            - |
              pg_dump $DATABASE_URL > /backup/backup-$(date +%Y%m%d-%H%M%S).sql
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: payway-secrets
                  key: database-url
            volumeMounts:
            - name: backup-volume
              mountPath: /backup
          volumes:
          - name: backup-volume
            persistentVolumeClaim:
              claimName: payway-backup-pvc
          restartPolicy: OnFailure
```

---

## 🎯 **Deployment Checklist**

### **Pre-Deployment**
- [ ] Infrastructure provisioning (EKS/GKE/AKS)
- [ ] ArgoCD installation and configuration
- [ ] Secrets management setup (Vault/AWS Secrets Manager)
- [ ] Monitoring stack deployment (Prometheus, Grafana)
- [ ] Storage classes and persistent volumes
- [ ] Network policies and security groups

### **Application Deployment**
- [ ] Docker image building and registry push
- [ ] Kustomize manifests creation
- [ ] ArgoCD application configuration
- [ ] Database migration and initialization
- [ ] SSL/TLS certificate provisioning
- [ ] Load balancer configuration

### **Post-Deployment**
- [ ] Health checks and monitoring
- [ ] Performance testing and optimization
- [ ] Security scanning and compliance
- [ ] Backup and disaster recovery testing
- [ ] Documentation and runbooks
- [ ] Team training and handover

---

## 🔄 **Maintenance & Updates**

### **Regular Tasks**
- **Daily**: Monitor application health and performance
- **Weekly**: Review logs and security alerts
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Performance optimization and capacity planning
- **Annually**: Disaster recovery testing and compliance audit

### **Update Strategy**
1. **Development**: Test new features in dev environment
2. **Staging**: Validate changes in staging environment
3. **Production**: Gradual rollout with ArgoCD
4. **Monitoring**: Watch metrics and rollback if needed
5. **Documentation**: Update runbooks and procedures

---

## 📚 **Additional Resources**

### **Documentation**
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/)
- [GitOps Principles](https://www.gitops.tech/)

### **Tools & Services**
- **ArgoCD**: GitOps continuous delivery
- **Kustomize**: Kubernetes native configuration management
- **Helm**: Kubernetes package manager
- **Velero**: Backup and disaster recovery
- **Prometheus**: Monitoring and alerting
- **Grafana**: Visualization and dashboards

---

*This document should be updated as the deployment strategy evolves and new requirements emerge.*
