from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from account.models import Account, KYC


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
