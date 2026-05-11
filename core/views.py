from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from account.models import Account, KYC


def _database_check():
    """Return (ok, error_message). Used for readiness / actuator DB component."""
    try:
        connection.ensure_connection()
        return True, None
    except Exception as exc:
        return False, str(exc)


@require_GET
def health_liveness(request):
    """
    Kubernetes liveness probe — process is up; does not touch the database.
    Same idea as Spring Boot Actuator livenessState.
    """
    return JsonResponse({'status': 'UP'})


@require_GET
def health_readiness(request):
    """
    Kubernetes readiness probe — verifies the app can serve traffic (DB reachable).
    Returns 503 when the database is unavailable so the pod is removed from Service endpoints.
    """
    ok, err = _database_check()
    body = {
        'status': 'UP' if ok else 'DOWN',
        'checks': {'database': 'UP' if ok else 'DOWN'},
    }
    if not ok and err:
        body['checks']['database_error'] = err
    return JsonResponse(body, status=200 if ok else 503)


@require_GET
def actuator_health(request):
    """
    Spring Boot Actuator–style aggregated health JSON for tooling and optional probes.
    """
    db_ok, db_err = _database_check()
    components = {
        'db': {
            'status': 'UP' if db_ok else 'DOWN',
            **({} if db_ok else {'details': {'error': db_err}}),
        },
    }
    overall = 'UP' if db_ok else 'DOWN'
    return JsonResponse(
        {'status': overall, 'components': components},
        status=200 if db_ok else 503,
    )


@require_GET
def api_discovery(request):
    """
    Lightweight index of HTTP-facing routes useful for curl/Postman.
    Most business routes are session/HTML; JSON APIs are called out explicitly.
    """
    base = request.build_absolute_uri('/').rstrip('/')
    return JsonResponse({
        'service': 'payway',
        'documentation': f'{base}/admin/',
        'health': {
            'liveness': f'{base}/health/',
            'readiness': f'{base}/ready/',
            'actuator_style': f'{base}/actuator/health/',
        },
        'json_apis': [
            {
                'path': '/auth/api/security/summary/',
                'methods': ['GET'],
                'auth': 'session',
                'description': 'Security summary for the logged-in user',
            },
            {
                'path': '/auth/api/security/events/',
                'methods': ['GET'],
                'auth': 'session',
                'description': 'Recent security events for the logged-in user',
            },
            {
                'path': '/account/notifications/count/',
                'methods': ['GET'],
                'auth': 'session',
                'headers': {'X-Requested-With': 'XMLHttpRequest'},
                'description': 'Unread notification count and latest unread (AJAX)',
            },
            {
                'path': '/account/notification/<id>/read/',
                'methods': ['GET'],
                'auth': 'session',
                'headers': {'X-Requested-With': 'XMLHttpRequest'},
                'description': 'Mark notification read; JSON if AJAX header',
            },
            {
                'path': '/account/fee-calculator/',
                'methods': ['POST'],
                'auth': 'session',
                'body': 'application/x-www-form-urlencoded: amount, currency',
                'description': 'Transfer fee estimate JSON on successful POST',
            },
        ],
        'note': 'Full human-readable guide: api-doc.md in the project root (not served as a URL). Log in via /auth/login/ (HTML form with CSRF) for a session cookie.',
    })


def home_view(request):
    """Home page view"""
    return render(request, 'core/home.html')


@login_required
def dashboard_view(request):
    """Dashboard view for authenticated users"""
    try:
        account = Account.objects.get(user=request.user)
        kyc = KYC.objects.filter(user=request.user).first()
        
        context = {
            'account': account,
            'kyc': kyc,
            'kyc_completed': kyc is not None,
        }
    except Account.DoesNotExist:
        context = {
            'account': None,
            'kyc': None,
            'kyc_completed': False,
        }
    
    return render(request, 'core/dashboard.html', context)
