"""
URL configuration for payway project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Kubernetes / observability (see docs/k8s.md and docker-compose healthcheck)
    path('health/', core_views.health_liveness, name='health_liveness'),
    path('ready/', core_views.health_readiness, name='health_readiness'),
    path('actuator/health/', core_views.actuator_health, name='actuator_health'),
    path('actuator/health/liveness/', core_views.health_liveness, name='actuator_health_liveness'),
    path('actuator/health/readiness/', core_views.health_readiness, name='actuator_health_readiness'),
    path('api/', core_views.api_discovery, name='api_discovery'),
    path('', include('core.urls')),
    path('auth/', include('userauths.urls')),
    path('account/', include('account.urls')),
    # Handle favicon.ico requests
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.svg', permanent=True)),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
