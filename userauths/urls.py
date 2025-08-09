from django.urls import path
from . import views

app_name = 'userauths'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Two-Factor Authentication
    path('2fa/setup/', views.two_factor_setup, name='two_factor_setup'),
    path('2fa/configure/', views.two_factor_configure, name='two_factor_configure'),
    path('2fa/enable/', views.two_factor_enable, name='two_factor_enable'),
    path('2fa/disable/', views.two_factor_disable, name='two_factor_disable'),
    path('2fa/verify/', views.two_factor_verify_view, name='two_factor_verify'),
    path('2fa/backup/', views.two_factor_backup_code_view, name='two_factor_backup'),
    path('2fa/regenerate-backup/', views.regenerate_backup_codes, name='regenerate_backup_codes'),
    
    # Security Features
    path('security/dashboard/', views.security_dashboard, name='security_dashboard'),
    path('security/logs/', views.security_logs, name='security_logs'),
    path('security/settings/', views.security_settings, name='security_settings'),
    path('security/devices/', views.device_management, name='device_management'),
    
    # API Endpoints
    path('api/security/summary/', views.get_security_summary_api, name='security_summary_api'),
    path('api/security/events/', views.get_recent_security_events_api, name='security_events_api'),
] 