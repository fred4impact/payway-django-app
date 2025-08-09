import hashlib
import json
import re
from typing import Dict, Any, Optional
from django.utils import timezone
from django.http import HttpRequest
from django.contrib.auth import get_user_model
from .models import SecurityLog, UserDevice, AccountLockout

User = get_user_model()


class SecurityService:
    """Central service for handling all security operations"""
    
    @staticmethod
    def get_client_ip(request: HttpRequest) -> str:
        """Extract client IP address from request"""
        try:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip or '0.0.0.0'
        except Exception as e:
            print(f"IP extraction failed: {e}")
            return '0.0.0.0'  # Return safe default

    @staticmethod
    def get_user_agent_info(request: HttpRequest) -> Dict[str, str]:
        """Extract and parse user agent information"""
        try:
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Basic device detection
            device_type = 'unknown'
            browser = 'Unknown'
            os = 'Unknown'
            
            if user_agent:
                user_agent_lower = user_agent.lower()
                
                # Device type detection
                if 'mobile' in user_agent_lower:
                    device_type = 'mobile'
                elif 'tablet' in user_agent_lower:
                    device_type = 'tablet'
                elif 'windows' in user_agent_lower or 'macintosh' in user_agent_lower or 'linux' in user_agent_lower:
                    device_type = 'desktop'
                
                # Browser detection
                if 'chrome' in user_agent_lower:
                    browser = 'Chrome'
                elif 'firefox' in user_agent_lower:
                    browser = 'Firefox'
                elif 'safari' in user_agent_lower:
                    browser = 'Safari'
                elif 'edge' in user_agent_lower:
                    browser = 'Edge'
                elif 'opera' in user_agent_lower:
                    browser = 'Opera'
                
                # OS detection
                if 'windows' in user_agent_lower:
                    os = 'Windows'
                elif 'macintosh' in user_agent_lower:
                    os = 'macOS'
                elif 'linux' in user_agent_lower:
                    os = 'Linux'
                elif 'android' in user_agent_lower:
                    os = 'Android'
                elif 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
                    os = 'iOS'
            
            return {
                'device_type': device_type,
                'browser': browser,
                'operating_system': os,
                'user_agent': user_agent
            }
        except Exception as e:
            print(f"User agent parsing failed: {e}")
            return {
                'device_type': 'unknown',
                'browser': 'Unknown',
                'operating_system': 'Unknown',
                'user_agent': ''
            }

    @staticmethod
    def generate_device_id(request: HttpRequest, user: User) -> str:
        """Generate unique device identifier"""
        try:
            # Create a hash from user-specific and request-specific data
            device_data = f"{user.id}:{user.email}:{SecurityService.get_client_ip(request)}"
            device_data += SecurityService.get_user_agent_info(request)['user_agent']
            
            # Generate hash
            device_hash = hashlib.sha256(device_data.encode()).hexdigest()
            return f"device_{device_hash[:16]}"
        except Exception as e:
            print(f"Device ID generation failed: {e}")
            # Return a fallback device ID
            return f"device_fallback_{user.id}_{int(timezone.now().timestamp())}"

    @staticmethod
    def log_security_event(
        user: Optional[User],
        event_type: str,
        request: HttpRequest,
        details: Optional[Dict[str, Any]] = None,
        risk_score: int = 0
    ) -> SecurityLog:
        """Log a security event"""
        try:
            ip_address = SecurityService.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Basic location detection (you can enhance this with GeoIP services)
            location = SecurityService.detect_location(ip_address)
            
            return SecurityLog.objects.create(
                user=user,
                event_type=event_type,
                ip_address=ip_address,
                user_agent=user_agent,
                location=location,
                risk_score=risk_score,
                details=details or {}
            )
        except Exception as e:
            print(f"Security logging failed: {e}")
            # Return a dummy SecurityLog to prevent failures
            class DummySecurityLog:
                def __init__(self):
                    self.id = None
                    self.user = user
                    self.event_type = event_type
                    self.ip_address = '0.0.0.0'
                    self.user_agent = ''
                    self.location = 'Unknown'
                    self.risk_score = risk_score
                    self.details = details or {}
                    self.timestamp = timezone.now()
            
            return DummySecurityLog()

    @staticmethod
    def detect_location(ip_address: str) -> str:
        """Detect location from IP address (basic implementation)"""
        try:
            # This is a basic implementation
            # In production, you'd use services like MaxMind GeoIP2, IP2Location, etc.
            
            # Local/private IPs
            if ip_address in ['127.0.0.1', 'localhost', '0.0.0.0']:
                return 'Local'
            
            # You can add more sophisticated location detection here
            # For now, return a placeholder
            return 'Unknown'
        except Exception as e:
            print(f"Location detection failed: {e}")
            return 'Unknown'  # Return safe default

    @staticmethod
    def assess_risk_score(request: HttpRequest, user: Optional[User] = None) -> int:
        """Assess risk score for a request (0-100)"""
        try:
            risk_score = 0
            ip_address = SecurityService.get_client_ip(request)
            
            # Check for suspicious IP patterns
            if ip_address in ['127.0.0.1', 'localhost']:
                risk_score += 10  # Local access might be suspicious in production
            
            # Check for VPN/Tor exit nodes (basic implementation)
            if SecurityService.is_suspicious_ip(ip_address):
                risk_score += 30
            
            # Check user agent anomalies
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            if not user_agent or len(user_agent) < 10:
                risk_score += 20  # Missing or suspicious user agent
            
            # Check for rapid requests (basic rate limiting check)
            if SecurityService.is_rapid_request(ip_address):
                risk_score += 25
            
            # Check user-specific risks
            if user:
                # Check if user has recent failed logins
                recent_failures = SecurityLog.objects.filter(
                    user=user,
                    event_type='login_failed',
                    timestamp__gte=timezone.now() - timezone.timedelta(hours=1)
                ).count()
                
                if recent_failures > 0:
                    risk_score += recent_failures * 10
                
                # Check if user is logging in from new location
                if SecurityService.is_new_location(user, ip_address):
                    risk_score += 15
            
            return min(risk_score, 100)  # Cap at 100
        except Exception as e:
            print(f"Risk assessment failed: {e}")
            return 0  # Return safe default

    @staticmethod
    def is_suspicious_ip(ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        try:
            # Basic implementation - you can enhance this with external services
            # Check for known VPN/Tor exit nodes, blacklisted IPs, etc.
            
            # For now, just check for obvious patterns
            suspicious_patterns = [
                r'^0\.0\.0\.',  # Invalid IPs
                r'^255\.255\.255\.',  # Broadcast IPs
            ]
            
            for pattern in suspicious_patterns:
                if re.match(pattern, ip_address):
                    return True
            
            return False
        except Exception as e:
            print(f"Suspicious IP check failed: {e}")
            return False  # Return safe default

    @staticmethod
    def is_rapid_request(ip_address: str) -> bool:
        """Check if IP is making rapid requests"""
        try:
            # Check for rapid requests in the last minute
            recent_requests = SecurityLog.objects.filter(
                ip_address=ip_address,
                timestamp__gte=timezone.now() - timezone.timedelta(minutes=1)
            ).count()
            
            return recent_requests > 10  # More than 10 requests per minute
        except Exception as e:
            print(f"Rapid request check failed: {e}")
            return False  # Return safe default

    @staticmethod
    def is_new_location(user: User, ip_address: str) -> bool:
        """Check if user is logging in from a new location"""
        try:
            # Check if this IP has been used by this user before
            existing_devices = UserDevice.objects.filter(
                user=user,
                ip_address=ip_address
            ).exists()
            
            return not existing_devices
        except Exception as e:
            print(f"New location check failed: {e}")
            return False  # Return safe default

    @staticmethod
    def track_user_device(request: HttpRequest, user: User) -> UserDevice:
        """Track or update user device information"""
        try:
            device_id = SecurityService.generate_device_id(request, user)
            user_agent_info = SecurityService.get_user_agent_info(request)
            ip_address = SecurityService.get_client_ip(request)
            
            # Try to get existing device
            device, created = UserDevice.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'user': user,
                    'device_name': f"{user_agent_info['operating_system']} - {user_agent_info['browser']}",
                    'device_type': user_agent_info['device_type'],
                    'browser': user_agent_info['browser'],
                    'operating_system': user_agent_info['operating_system'],
                    'ip_address': ip_address,
                    'user_agent': user_agent_info['user_agent'],
                    'location': SecurityService.detect_location(ip_address)
                }
            )
            
            if not created:
                # Update existing device
                device.last_used = timezone.now()
                device.ip_address = ip_address
                device.location = SecurityService.detect_location(ip_address)
                device.save()
            
            return device
        except Exception as e:
            # If device tracking fails, create a minimal device object
            print(f"Device tracking failed: {e}")
            # Return a dummy device to prevent login failure
            class DummyDevice:
                def __init__(self):
                    self.device_id = "dummy_device"
                    self.device_name = "Unknown Device"
                    self.location = "Unknown"
            
            return DummyDevice()

    @staticmethod
    def handle_failed_login(request: HttpRequest, email: str) -> None:
        """Handle failed login attempt"""
        try:
            # Log the failed attempt
            SecurityService.log_security_event(
                user=None,
                event_type='login_failed',
                request=request,
                details={'email': email},
                risk_score=SecurityService.assess_risk_score(request)
            )
            
            # Try to find user and increment failed attempts
            try:
                user = User.objects.get(email=email)
                user.increment_failed_login()
                
                # Log account lockout if applicable
                if user.is_account_locked():
                    SecurityService.log_security_event(
                        user=user,
                        event_type='account_locked',
                        request=request,
                        details={
                            'reason': 'Failed login attempts exceeded limit',
                            'failed_attempts': user.failed_login_attempts
                        },
                        risk_score=80
                    )
                    
                    # Create lockout record
                    try:
                        AccountLockout.objects.create(
                            user=user,
                            lockout_type='failed_login',
                            reason=f'Account locked due to {user.failed_login_attempts} failed login attempts',
                            locked_until=user.account_locked_until,
                            ip_address=SecurityService.get_client_ip(request)
                        )
                    except Exception as e:
                        print(f"Failed to create lockout record: {e}")
                        # Don't let lockout record creation failure break the process
                    
            except User.DoesNotExist:
                # User doesn't exist, just log the attempt
                pass
        except Exception as e:
            print(f"Failed login handling failed: {e}")
            # Don't let security failures break the login process

    @staticmethod
    def handle_successful_login(request: HttpRequest, user: User) -> None:
        """Handle successful login"""
        try:
            # Reset failed login attempts
            try:
                user.reset_failed_login()
            except Exception as e:
                print(f"Failed to reset failed login attempts: {e}")
                # Don't let reset failure break the login process
            
            # Update last login IP and location
            try:
                user.last_login_ip = SecurityService.get_client_ip(request)
                user.last_login_location = SecurityService.detect_location(user.last_login_ip)
                user.save()
            except Exception as e:
                print(f"Failed to update user login info: {e}")
                # Don't let user update failure break the login process
            
            # Track device
            device = SecurityService.track_user_device(request, user)
            
            # Log successful login
            SecurityService.log_security_event(
                user=user,
                event_type='login_success',
                request=request,
                details={
                    'device_id': device.device_id,
                    'device_name': device.device_name,
                    'location': device.location
                },
                risk_score=SecurityService.assess_risk_score(request, user)
            )
        except Exception as e:
            print(f"Successful login handling failed: {e}")
            # Don't let security failures break the login process

    @staticmethod
    def get_user_security_summary(user: User) -> Dict[str, Any]:
        """Get comprehensive security summary for a user"""
        try:
            # Get recent security events
            recent_events = SecurityLog.objects.filter(
                user=user
            ).order_by('-timestamp')[:10]
            
            # Get active devices
            active_devices = UserDevice.objects.filter(
                user=user,
                is_active=True
            ).order_by('-last_used')
            
            # Get recent lockouts
            recent_lockouts = AccountLockout.objects.filter(
                user=user,
                is_active=True
            ).order_by('-locked_at')
            
            # Calculate security score
            security_score = 100
            
            # Deduct points for various risk factors
            if user.failed_login_attempts > 0:
                security_score -= min(user.failed_login_attempts * 5, 30)
            
            if user.is_account_locked():
                security_score -= 50
            
            # Check for 2FA
            try:
                if user.twofactorauth.is_enabled:
                    security_score += 20
            except:
                pass  # No 2FA configured
            
            # Check for suspicious recent activity
            suspicious_events = SecurityLog.objects.filter(
                user=user,
                risk_score__gte=50,
                timestamp__gte=timezone.now() - timezone.timedelta(days=7)
            ).count()
            
            security_score -= min(suspicious_events * 10, 30)
            security_score = max(security_score, 0)  # Don't go below 0
            
            return {
                'security_score': security_score,
                'recent_events': recent_events,
                'active_devices': active_devices,
                'recent_lockouts': recent_lockouts,
                'failed_login_attempts': user.failed_login_attempts,
                'is_locked': user.is_account_locked(),
                'last_login_ip': user.last_login_ip,
                'last_login_location': user.last_login_location,
                'security_level': user.security_level
            }
        except Exception as e:
            print(f"Security summary generation failed: {e}")
            # Return safe default
            return {
                'security_score': 50,
                'recent_events': [],
                'active_devices': [],
                'recent_lockouts': [],
                'failed_login_attempts': 0,
                'is_locked': False,
                'last_login_ip': None,
                'last_login_location': None,
                'security_level': 'basic'
            }
