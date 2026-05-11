from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.conf import settings
import logging

from .forms import (
    UserRegisterForm, UserLoginForm, TwoFactorSetupForm, TwoFactorVerifyForm,
    TwoFactorBackupCodeForm, TwoFactorDisableForm, SecuritySettingsForm,
    DeviceTrustForm, SecurityLogFilterForm
)
from .services import SecurityService
from .models import User, TwoFactorAuth, UserDevice, SecurityLog, AccountLockout
from .forms import generate_totp_secret, generate_totp_qr_code, verify_totp_code, generate_backup_codes
import json

logger = logging.getLogger(__name__)


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                
                # Log successful registration
                try:
                    SecurityService.log_security_event(
                        user=user,
                        event_type='account_created',
                        request=request,
                        details={'registration_method': 'email'},
                        risk_score=SecurityService.assess_risk_score(request, user)
                    )
                except Exception as e:
                    logger.exception("Security logging failed after registration")
                
                messages.success(request, 'Account created successfully!')
                return redirect('core:dashboard')
            except Exception as e:
                logger.exception("Registration failed")
                messages.error(request, 'Registration failed. Please try again.')
                if settings.DEBUG:
                    raise
        else:
            # Log failed registration attempt
            try:
                SecurityService.log_security_event(
                    user=None,
                    event_type='registration_failed',
                    request=request,
                    details={'errors': dict(form.errors)},
                    risk_score=SecurityService.assess_risk_score(request)
                )
            except Exception as e:
                logger.exception("Security logging failed on registration_failed")
    else:
        form = UserRegisterForm()
    
    return render(request, 'userauths/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            
            # Check if user exists and is not locked
            try:
                from .models import User
                user = User.objects.get(email=email)
                
                # Check if account is locked
                if user.is_account_locked():
                    try:
                        SecurityService.log_security_event(
                            user=user,
                            event_type='login_blocked',
                            request=request,
                            details={'reason': 'Account locked'},
                            risk_score=90
                        )
                    except Exception as e:
                        print(f"Security logging failed: {e}")
                    messages.error(request, 'Account is temporarily locked due to multiple failed login attempts. Please try again later.')
                    return render(request, 'userauths/login.html', {'form': form})
                
            except User.DoesNotExist:
                user = None
            
            # Attempt authentication
            user = authenticate(username=email, password=password)
            
            if user is not None:
                # Check if account is locked after authentication
                if user.is_account_locked():
                    try:
                        SecurityService.log_security_event(
                            user=user,
                            event_type='login_blocked',
                            request=request,
                            details={'reason': 'Account locked'},
                            risk_score=90
                        )
                    except Exception as e:
                        print(f"Security logging failed: {e}")
                    messages.error(request, 'Account is temporarily locked due to multiple failed login attempts. Please try again later.')
                    return render(request, 'userauths/login.html', {'form': form})
                
                # Check if 2FA is required
                if hasattr(user, 'twofactorauth') and user.twofactorauth.is_enabled:
                    twofa = user.twofactorauth
                    # Store user ID in session for 2FA verification
                    request.session['2fa_user_id'] = user.id
                    request.session['2fa_method'] = twofa.method
                    
                    # Log 2FA required event
                    try:
                        SecurityService.log_security_event(
                            user=user,
                            event_type='2fa_required',
                            request=request,
                            details={'method': twofa.method},
                            risk_score=SecurityService.assess_risk_score(request, user)
                        )
                    except Exception as e:
                        print(f"Security logging failed: {e}")
                    
                    return redirect('userauths:two_factor_verify')
                
                # Successful login without 2FA
                login(request, user)
                
                # Handle successful login with security service
                try:
                    SecurityService.handle_successful_login(request, user)
                except Exception as e:
                    # Log the error but don't fail login
                    print(f"Security service failed: {e}")
                
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('core:dashboard')
            else:
                # Failed login
                try:
                    SecurityService.handle_failed_login(request, email)
                except Exception as e:
                    # Log the error but don't fail login
                    print(f"Security service failed: {e}")
                messages.error(request, 'Invalid email or password.')
        else:
            # Form validation failed
            try:
                SecurityService.log_security_event(
                    user=None,
                    event_type='login_validation_failed',
                    request=request,
                    details={'errors': form.errors},
                    risk_score=SecurityService.assess_risk_score(request)
                )
            except Exception as e:
                # Log the error but don't fail login
                print(f"Security service failed: {e}")
    else:
        form = UserLoginForm()
    
    return render(request, 'userauths/login.html', {'form': form})


def two_factor_verify_view(request):
    """Verify Two-Factor Authentication code"""
    user_id = request.session.get('2fa_user_id')
    method = request.session.get('2fa_method')
    
    if not user_id or not method:
        messages.error(request, 'Invalid 2FA session. Please login again.')
        return redirect('userauths:login')
    
    try:
        user = User.objects.get(id=user_id)
        twofa = user.twofactorauth
    except (User.DoesNotExist, TwoFactorAuth.DoesNotExist):
        messages.error(request, 'Invalid 2FA session. Please login again.')
        return redirect('userauths:login')
    
    if request.method == 'POST':
        form = TwoFactorVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data.get('code')
            
            # Verify the code
            if method == 'totp':
                if verify_totp_code(twofa.secret_key, code):
                    # Successful 2FA verification
                    login(request, user)
                    
                    # Update 2FA last used
                    twofa.last_used = timezone.now()
                    twofa.save()
                    
                    # Log successful 2FA
                    try:
                        SecurityService.log_security_event(
                            user=user,
                            event_type='2fa_used',
                            request=request,
                            details={'method': method},
                            risk_score=SecurityService.assess_risk_score(request, user)
                        )
                    except Exception as e:
                        print(f"Security logging failed: {e}")
                    
                    # Handle successful login
                    try:
                        SecurityService.handle_successful_login(request, user)
                    except Exception as e:
                        print(f"Security service failed: {e}")
                    
                    # Clear 2FA session
                    del request.session['2fa_user_id']
                    del request.session['2fa_method']
                    
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect('core:dashboard')
                else:
                    # Failed 2FA verification
                    try:
                        SecurityService.log_security_event(
                            user=user,
                            event_type='2fa_failed',
                            request=request,
                            details={'method': method, 'code_entered': code},
                            risk_score=80
                        )
                    except Exception as e:
                        print(f"Security logging failed: {e}")
                    messages.error(request, 'Invalid 2FA code. Please try again.')
            else:
                # SMS 2FA (placeholder for future implementation)
                messages.error(request, 'SMS 2FA not yet implemented.')
    else:
        form = TwoFactorVerifyForm()
    
    context = {
        'form': form,
        'method': method,
        'user': user
    }
    
    return render(request, 'userauths/two_factor_verify.html', context)


def two_factor_backup_code_view(request):
    """Use backup code for 2FA"""
    user_id = request.session.get('2fa_user_id')
    
    if not user_id:
        messages.error(request, 'Invalid 2FA session. Please login again.')
        return redirect('userauths:login')
    
    try:
        user = User.objects.get(id=user_id)
        twofa = user.twofactorauth
    except (User.DoesNotExist, TwoFactorAuth.DoesNotExist):
        messages.error(request, 'Invalid 2FA session. Please login again.')
        return redirect('userauths:login')
    
    if request.method == 'POST':
        form = TwoFactorBackupCodeForm(request.POST)
        if form.is_valid():
            backup_code = form.cleaned_data.get('backup_code')
            
            if twofa.verify_backup_code(backup_code):
                # Successful backup code verification
                login(request, user)
                
                # Log successful backup code usage
                try:
                    SecurityService.log_security_event(
                        user=user,
                        event_type='2fa_backup_used',
                        request=request,
                        details={'backup_code': backup_code},
                        risk_score=SecurityService.assess_risk_score(request, user)
                    )
                except Exception as e:
                    print(f"Security logging failed: {e}")
                
                # Handle successful login
                try:
                    SecurityService.handle_successful_login(request, user)
                except Exception as e:
                    print(f"Security service failed: {e}")
                
                # Clear 2FA session
                del request.session['2fa_user_id']
                del request.session['2fa_method']
                
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('core:dashboard')
            else:
                # Invalid backup code
                try:
                    SecurityService.log_security_event(
                        user=user,
                        event_type='2fa_backup_failed',
                        request=request,
                        details={'backup_code_entered': backup_code},
                        risk_score=90
                    )
                except Exception as e:
                    print(f"Security logging failed: {e}")
                messages.error(request, 'Invalid backup code. Please try again.')
    else:
        form = TwoFactorBackupCodeForm()
    
    context = {
        'form': form,
        'user': user
    }
    
    return render(request, 'userauths/two_factor_backup.html', context)


@login_required
def logout_view(request):
    # Log logout event
    try:
        SecurityService.log_security_event(
            user=request.user,
            event_type='logout',
            request=request,
            risk_score=SecurityService.assess_risk_score(request, request.user)
        )
    except Exception as e:
        print(f"Security logging failed: {e}")
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('userauths:login')


@login_required
def security_dashboard(request):
    """Security dashboard for users to view their security status"""
    from .services import SecurityService
    
    # Get user security summary
    try:
        security_summary = SecurityService.get_user_security_summary(request.user)
    except Exception as e:
        print(f"Security service failed: {e}")
        security_summary = {}
    
    context = {
        'security_summary': security_summary,
        'user': request.user
    }
    
    return render(request, 'userauths/security_dashboard.html', context)


@login_required
def two_factor_setup(request):
    """Setup Two-Factor Authentication"""
    try:
        twofa = request.user.twofactorauth
        if twofa.is_enabled:
            messages.info(request, 'Two-Factor Authentication is already enabled.')
            return redirect('userauths:security_dashboard')
    except:
        pass
    
    if request.method == 'POST':
        form = TwoFactorSetupForm(request.POST)
        if form.is_valid():
            method = form.cleaned_data.get('method')
            phone_number = form.cleaned_data.get('phone_number')
            
            # Create or update 2FA settings
            twofa, created = TwoFactorAuth.objects.get_or_create(
                user=request.user,
                defaults={
                    'method': method,
                    'phone_number': phone_number if method == 'sms' else '',
                    'secret_key': generate_totp_secret() if method == 'totp' else '',
                    'backup_codes': generate_backup_codes()
                }
            )
            
            if not created:
                twofa.method = method
                twofa.phone_number = phone_number if method == 'sms' else ''
                if method == 'totp':
                    twofa.secret_key = generate_totp_secret()
                twofa.backup_codes = generate_backup_codes()
                twofa.save()
            
            # Log 2FA setup
            SecurityService.log_security_event(
                user=request.user,
                event_type='2fa_setup',
                request=request,
                details={'method': method},
                risk_score=SecurityService.assess_risk_score(request, request.user)
            )
            
            messages.success(request, 'Two-Factor Authentication setup completed successfully!')
            return redirect('userauths:two_factor_configure')
    else:
        form = TwoFactorSetupForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'userauths/two_factor_setup.html', context)


@login_required
def two_factor_configure(request):
    """Configure Two-Factor Authentication (show QR code, etc.)"""
    try:
        twofa = request.user.twofactorauth
    except:
        messages.error(request, 'Two-Factor Authentication not configured.')
        return redirect('userauths:two_factor_setup')
    
    if twofa.method == 'totp':
        # Generate QR code for TOTP
        qr_code, provisioning_uri = generate_totp_qr_code(
            twofa.secret_key, 
            request.user.email
        )
        
        context = {
            'twofa': twofa,
            'qr_code': qr_code,
            'provisioning_uri': provisioning_uri,
            'backup_codes': twofa.backup_codes
        }
        
        return render(request, 'userauths/two_factor_configure.html', context)
    else:
        # SMS 2FA configuration
        context = {
            'twofa': twofa,
            'backup_codes': twofa.backup_codes
        }
        
        return render(request, 'userauths/two_factor_configure_sms.html', context)


@login_required
def two_factor_enable(request):
    """Enable Two-Factor Authentication"""
    try:
        twofa = request.user.twofactorauth
        if twofa.is_enabled:
            messages.info(request, 'Two-Factor Authentication is already enabled.')
            return redirect('userauths:security_dashboard')
        
        # Enable 2FA
        twofa.is_enabled = True
        twofa.save()
        
        # Log 2FA enabled
        SecurityService.log_security_event(
            user=request.user,
            event_type='2fa_enabled',
            request=request,
            details={'method': twofa.method},
            risk_score=SecurityService.assess_risk_score(request, request.user)
        )
        
        messages.success(request, 'Two-Factor Authentication has been enabled successfully!')
        
    except:
        messages.error(request, 'Two-Factor Authentication not configured.')
        return redirect('userauths:two_factor_setup')
    
    return redirect('userauths:security_dashboard')


@login_required
def two_factor_disable(request):
    """Disable Two-Factor Authentication"""
    if request.method == 'POST':
        form = TwoFactorDisableForm(request.user, request.POST)
        if form.is_valid():
            try:
                twofa = request.user.twofactorauth
                twofa.is_enabled = False
                twofa.save()
                
                # Log 2FA disabled
                SecurityService.log_security_event(
                    user=request.user,
                    event_type='2fa_disabled',
                    request=request,
                    details={'method': twofa.method},
                    risk_score=SecurityService.assess_risk_score(request, request.user)
                )
                
                messages.success(request, 'Two-Factor Authentication has been disabled.')
                
            except:
                messages.error(request, 'Two-Factor Authentication not found.')
            
            return redirect('userauths:security_dashboard')
    else:
        form = TwoFactorDisableForm(request.user)
    
    context = {
        'form': form
    }
    
    return render(request, 'userauths/two_factor_disable.html', context)


@login_required
def device_management(request):
    """Manage user devices and sessions"""
    if request.method == 'POST':
        form = DeviceTrustForm(request.POST)
        if form.is_valid():
            device_id = form.cleaned_data.get('device_id')
            action = form.cleaned_data.get('action')
            
            try:
                device = UserDevice.objects.get(device_id=device_id, user=request.user)
                
                if action == 'trust':
                    device.is_trusted = True
                    device.save()
                    
                    SecurityService.log_security_event(
                        user=request.user,
                        event_type='device_trusted',
                        request=request,
                        details={'device_id': device_id, 'device_name': device.device_name},
                        risk_score=SecurityService.assess_risk_score(request, request.user)
                    )
                    
                    messages.success(request, f'Device "{device.device_name}" marked as trusted.')
                    
                elif action == 'untrust':
                    device.is_trusted = False
                    device.save()
                    
                    SecurityService.log_security_event(
                        user=request.user,
                        event_type='device_untrusted',
                        request=request,
                        details={'device_id': device_id, 'device_name': device.device_name},
                        risk_score=SecurityService.assess_risk_score(request, request.user)
                    )
                    
                    messages.success(request, f'Device "{device.device_name}" marked as untrusted.')
                    
                elif action == 'remove':
                    device.is_active = False
                    device.save()
                    
                    SecurityService.log_security_event(
                        user=request.user,
                        event_type='device_removed',
                        request=request,
                        details={'device_id': device_id, 'device_name': device.device_name},
                        risk_score=SecurityService.assess_risk_score(request, request.user)
                    )
                    
                    messages.success(request, f'Device "{device.device_name}" removed.')
                    
            except UserDevice.DoesNotExist:
                messages.error(request, 'Device not found.')
    
    # Get user devices
    devices = UserDevice.objects.filter(user=request.user, is_active=True).order_by('-last_used')
    
    context = {
        'devices': devices,
        'user': request.user
    }
    
    return render(request, 'userauths/device_management.html', context)


@login_required
def security_logs(request):
    """View security logs for the user"""
    # Get filter parameters
    event_type = request.GET.get('event_type')
    risk_level = request.GET.get('risk_level')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    ip_address = request.GET.get('ip_address')
    
    # Build query
    logs = SecurityLog.objects.filter(user=request.user)
    
    if event_type:
        logs = logs.filter(event_type=event_type)
    
    if risk_level:
        if risk_level == 'low':
            logs = logs.filter(risk_score__lt=30)
        elif risk_level == 'medium':
            logs = logs.filter(risk_score__gte=30, risk_score__lt=70)
        elif risk_level == 'high':
            logs = logs.filter(risk_score__gte=70)
    
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    if ip_address:
        logs = logs.filter(ip_address__icontains=ip_address)
    
    # Order by timestamp
    logs = logs.order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'logs': page_obj,
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'user': request.user,
        'filter_form': SecurityLogFilterForm(request.GET)
    }
    
    return render(request, 'userauths/security_logs.html', context)


@login_required
def security_settings(request):
    """Update security settings"""
    if request.method == 'POST':
        form = SecuritySettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            current_password = form.cleaned_data.get('current_password')
            new_password = form.cleaned_data.get('new_password')
            security_level = form.cleaned_data.get('security_level')
            
            # Update security level
            if security_level != request.user.security_level:
                request.user.security_level = security_level
                
                SecurityService.log_security_event(
                    user=request.user,
                    event_type='security_settings_changed',
                    request=request,
                    details={'security_level': security_level},
                    risk_score=SecurityService.assess_risk_score(request, request.user)
                )
            
            # Change password if provided
            if new_password:
                request.user.set_password(new_password)
                
                SecurityService.log_security_event(
                    user=request.user,
                    event_type='password_change',
                    request=request,
                    risk_score=SecurityService.assess_risk_score(request, request.user)
                )
                
                messages.success(request, 'Password changed successfully. Please login again.')
                logout(request)
                return redirect('userauths:login')
            
            request.user.save()
            messages.success(request, 'Security settings updated successfully.')
            return redirect('userauths:security_dashboard')
    else:
        form = SecuritySettingsForm(instance=request.user)
    
    context = {
        'form': form
    }
    
    return render(request, 'userauths/security_settings.html', context)


@login_required
def regenerate_backup_codes(request):
    """Regenerate backup codes for 2FA"""
    try:
        twofa = request.user.twofactorauth
        if not twofa.is_enabled:
            messages.error(request, 'Two-Factor Authentication is not enabled.')
            return redirect('userauths:security_dashboard')
        
        # Generate new backup codes
        new_codes = twofa.generate_backup_codes()
        
        # Log backup codes regeneration
        SecurityService.log_security_event(
            user=request.user,
            event_type='2fa_backup_codes_regenerated',
            request=request,
            risk_score=SecurityService.assess_risk_score(request, request.user)
        )
        
        messages.success(request, 'Backup codes have been regenerated successfully.')
        
    except:
        messages.error(request, 'Two-Factor Authentication not configured.')
    
    return redirect('userauths:two_factor_configure')


# API endpoints for AJAX requests
@login_required
def get_security_summary_api(request):
    """API endpoint to get security summary"""
    from .services import SecurityService
    
    summary = SecurityService.get_user_security_summary(request.user)
    
    return JsonResponse({
        'security_score': summary['security_score'],
        'failed_login_attempts': summary['failed_login_attempts'],
        'is_locked': summary['is_locked'],
        'active_devices_count': len(summary['active_devices']),
        'recent_events_count': len(summary['recent_events'])
    })


@login_required
def get_recent_security_events_api(request):
    """API endpoint to get recent security events"""
    events = SecurityLog.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:5]
    
    events_data = []
    for event in events:
        events_data.append({
            'event_type': event.get_event_type_display(),
            'timestamp': event.timestamp.strftime('%Y-%m-%d %H:%M'),
            'risk_score': event.risk_score,
            'ip_address': event.ip_address,
            'location': event.location
        })
    
    return JsonResponse({'events': events_data})
