from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import KYCForm
from .models import KYC, Account


@login_required
def kyc_view(request):
    """Handle KYC form submission and display"""
    try:
        kyc = KYC.objects.get(user=request.user)
        # If KYC already exists, show the details
        return render(request, 'account/kyc_detail.html', {'kyc': kyc})
    except KYC.DoesNotExist:
        # If KYC doesn't exist, show the form
        if request.method == 'POST':
            form = KYCForm(request.POST, request.FILES)
            if form.is_valid():
                kyc = form.save(commit=False)
                kyc.user = request.user
                kyc.save()
                messages.success(request, 'KYC submitted successfully! We will review your documents.')
                return redirect('account:kyc_detail')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = KYCForm()
        
        return render(request, 'account/kyc.html', {'form': form})


@login_required
def kyc_detail_view(request):
    """Display KYC details"""
    try:
        kyc = KYC.objects.get(user=request.user)
        return render(request, 'account/kyc_detail.html', {'kyc': kyc})
    except KYC.DoesNotExist:
        messages.warning(request, 'Please complete your KYC first.')
        return redirect('account:kyc')


@login_required
def account_info_view(request):
    """Display account and KYC information"""
    try:
        account = Account.objects.get(user=request.user)
        kyc = KYC.objects.get(user=request.user)
        context = {
            'account': account,
            'kyc': kyc,
        }
    except Account.DoesNotExist:
        messages.error(request, 'Account not found.')
        return redirect('core:dashboard')
    except KYC.DoesNotExist:
        messages.warning(request, 'Please complete your KYC.')
        context = {
            'account': account,
            'kyc': None,
        }
    
    return render(request, 'account/account_info.html', context)
