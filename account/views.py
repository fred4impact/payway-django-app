from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import csv
from .forms import KYCForm, AccountSearchForm, MoneyTransferForm, PaymentRequestForm, TransactionFilterForm
from .models import KYC, Account, Transaction, PaymentRequest, Notification
from userauths.models import User


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


# Money Transfer Views
@login_required
def search_account_view(request):
    """Search for users by account number or email"""
    form = AccountSearchForm(request.GET or None)
    search_results = []
    
    if form.is_valid():
        query = form.cleaned_data['search_query']
        
        # Search by account number
        try:
            account = Account.objects.get(account_number=query, is_active=True)
            if account.user != request.user:
                search_results.append({
                    'account': account,
                    'user': account.user,
                    'match_type': 'account_number'
                })
        except Account.DoesNotExist:
            pass
        
        # Search by email
        try:
            user = User.objects.get(email__icontains=query)
            if user != request.user:
                try:
                    account = Account.objects.get(user=user, is_active=True)
                    search_results.append({
                        'account': account,
                        'user': user,
                        'match_type': 'email'
                    })
                except Account.DoesNotExist:
                    pass
        except User.DoesNotExist:
            pass
    
    context = {
        'form': form,
        'search_results': search_results,
    }
    return render(request, 'account/search_account.html', context)


@login_required
def money_transfer_view(request):
    """Handle money transfers"""
    if request.method == 'POST':
        form = MoneyTransferForm(request.POST)
        if form.is_valid():
            receiver_account = form.cleaned_data['receiver_account']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description']
            reference = form.cleaned_data['reference']
            
            # Get sender's account
            try:
                sender_account = Account.objects.get(user=request.user)
            except Account.DoesNotExist:
                messages.error(request, 'Your account not found.')
                return redirect('account:money_transfer')
            
            # Check if sender has sufficient balance
            if sender_account.account_balance < amount:
                messages.error(request, 'Insufficient balance for this transfer.')
                return redirect('account:money_transfer')
            
            # Check if trying to transfer to own account
            if sender_account == receiver_account:
                messages.error(request, 'You cannot transfer money to your own account.')
                return redirect('account:money_transfer')
            
            # Calculate transaction fee (simple 1% fee)
            transaction_fee = amount * Decimal('0.01')
            total_amount = amount + transaction_fee
            
            # Check if sender has enough balance including fee
            if sender_account.account_balance < total_amount:
                messages.error(request, f'Insufficient balance. You need ${total_amount:.2f} (including ${transaction_fee:.2f} fee).')
                return redirect('account:money_transfer')
            
            try:
                with transaction.atomic():
                    # Create the transaction
                    transfer = Transaction.objects.create(
                        sender=request.user,
                        receiver=receiver_account.user,
                        sender_account=sender_account,
                        receiver_account=receiver_account,
                        amount=amount,
                        transaction_fee=transaction_fee,
                        description=description,
                        reference=reference,
                        status='completed'
                    )
                    
                    # Update account balances
                    sender_account.account_balance -= total_amount
                    sender_account.save()
                    
                    receiver_account.account_balance += amount
                    receiver_account.save()
                    
                    # Create notifications
                    Notification.objects.create(
                        user=request.user,
                        notification_type='transaction',
                        title='Money Sent Successfully',
                        message=f'You sent ${amount:.2f} to {receiver_account.user.get_full_name() or receiver_account.user.email}',
                        transaction=transfer,
                        is_email_sent=True
                    )
                    
                    Notification.objects.create(
                        user=receiver_account.user,
                        notification_type='transaction',
                        title='Money Received',
                        message=f'You received ${amount:.2f} from {request.user.get_full_name() or request.user.email}',
                        transaction=transfer,
                        is_email_sent=True
                    )
                    
                    messages.success(request, f'Successfully sent ${amount:.2f} to {receiver_account.user.get_full_name() or receiver_account.user.email}')
                    return redirect('account:transaction_detail', transaction_id=transfer.transaction_id)
                    
            except Exception as e:
                messages.error(request, f'Transfer failed: {str(e)}')
                return redirect('account:money_transfer')
    else:
        form = MoneyTransferForm()
    
    context = {
        'form': form,
    }
    return render(request, 'account/money_transfer.html', context)


# Payment Request Views
@login_required
def create_payment_request_view(request):
    """Create a payment request"""
    if request.method == 'POST':
        form = PaymentRequestForm(request.POST)
        if form.is_valid():
            recipient_account = form.cleaned_data['recipient_account']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description']
            expires_in_days = int(form.cleaned_data['expires_in_days'])
            
            # Get requester's account
            try:
                requester_account = Account.objects.get(user=request.user)
            except Account.DoesNotExist:
                messages.error(request, 'Your account not found.')
                return redirect('account:create_payment_request')
            
            # Check if trying to request from own account
            if requester_account == recipient_account:
                messages.error(request, 'You cannot request money from your own account.')
                return redirect('account:create_payment_request')
            
            # Calculate expiration date
            expires_at = timezone.now() + timedelta(days=expires_in_days)
            
            try:
                # Create payment request
                payment_request = PaymentRequest.objects.create(
                    requester=request.user,
                    recipient=recipient_account.user,
                    requester_account=requester_account,
                    recipient_account=recipient_account,
                    amount=amount,
                    description=description,
                    expires_at=expires_at
                )
                
                # Create notification for recipient
                Notification.objects.create(
                    user=recipient_account.user,
                    notification_type='payment_request',
                    title='Payment Request Received',
                    message=f'{request.user.get_full_name() or request.user.email} is requesting ${amount:.2f} from you',
                    payment_request=payment_request,
                    is_email_sent=True
                )
                
                messages.success(request, f'Payment request sent to {recipient_account.user.get_full_name() or recipient_account.user.email}')
                return redirect('account:payment_request_detail', request_id=payment_request.request_id)
                
            except Exception as e:
                messages.error(request, f'Payment request failed: {str(e)}')
                return redirect('account:create_payment_request')
    else:
        form = PaymentRequestForm()
    
    context = {
        'form': form,
    }
    return render(request, 'account/create_payment_request.html', context)


@login_required
def payment_requests_view(request):
    """View all payment requests (sent and received)"""
    sent_requests = PaymentRequest.objects.filter(requester=request.user).order_by('-created_at')
    received_requests = PaymentRequest.objects.filter(recipient=request.user).order_by('-created_at')
    
    # Check expiration for all requests
    for payment_request in list(sent_requests) + list(received_requests):
        payment_request.check_expiration()
    
    context = {
        'sent_requests': sent_requests,
        'received_requests': received_requests,
    }
    return render(request, 'account/payment_requests.html', context)


@login_required
def settle_payment_request_view(request, request_id):
    """Settle a payment request"""
    payment_request = get_object_or_404(PaymentRequest, request_id=request_id, recipient=request.user)
    
    # Check expiration
    payment_request.check_expiration()
    
    if payment_request.status != 'pending':
        messages.error(request, 'This payment request cannot be settled.')
        return redirect('account:payment_requests')
    
    if payment_request.is_expired:
        messages.error(request, 'This payment request has expired.')
        return redirect('account:payment_requests')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get accounts
                recipient_account = payment_request.recipient_account
                requester_account = payment_request.requester_account
                
                # Check if recipient has sufficient balance
                if recipient_account.account_balance < payment_request.amount:
                    messages.error(request, 'Insufficient balance to settle this request.')
                    return redirect('account:payment_requests')
                
                # Create transaction
                transfer = Transaction.objects.create(
                    sender=request.user,
                    receiver=payment_request.requester,
                    sender_account=recipient_account,
                    receiver_account=requester_account,
                    amount=payment_request.amount,
                    transaction_type='payment_request',
                    description=payment_request.description,
                    status='completed'
                )
                
                # Update account balances
                recipient_account.account_balance -= payment_request.amount
                recipient_account.save()
                
                requester_account.account_balance += payment_request.amount
                requester_account.save()
                
                # Update payment request status
                payment_request.status = 'paid'
                payment_request.paid_at = timezone.now()
                payment_request.save()
                
                # Create notifications
                Notification.objects.create(
                    user=request.user,
                    notification_type='transaction',
                    title='Payment Request Settled',
                    message=f'You paid ${payment_request.amount:.2f} to {payment_request.requester.get_full_name() or payment_request.requester.email}',
                    transaction=transfer,
                    is_email_sent=True
                )
                
                Notification.objects.create(
                    user=payment_request.requester,
                    notification_type='transaction',
                    title='Payment Request Received',
                    message=f'You received ${payment_request.amount:.2f} from {request.user.get_full_name() or request.user.email}',
                    transaction=transfer,
                    is_email_sent=True
                )
                
                messages.success(request, f'Successfully paid ${payment_request.amount:.2f} to {payment_request.requester.get_full_name() or payment_request.requester.email}')
                return redirect('account:transaction_detail', transaction_id=transfer.transaction_id)
                
        except Exception as e:
            messages.error(request, f'Settlement failed: {str(e)}')
            return redirect('account:payment_requests')
    
    context = {
        'payment_request': payment_request,
    }
    return render(request, 'account/settle_payment_request.html', context)


# Transaction Management Views
@login_required
def transactions_view(request):
    """View all transactions with filtering and pagination"""
    form = TransactionFilterForm(request.GET or None)
    transactions = Transaction.objects.filter(
        models.Q(sender=request.user) | models.Q(receiver=request.user)
    ).order_by('-created_at')
    
    if form.is_valid():
        # Apply filters
        if form.cleaned_data.get('transaction_type'):
            transactions = transactions.filter(transaction_type=form.cleaned_data['transaction_type'])
        
        if form.cleaned_data.get('status'):
            transactions = transactions.filter(status=form.cleaned_data['status'])
        
        if form.cleaned_data.get('date_from'):
            transactions = transactions.filter(created_at__date__gte=form.cleaned_data['date_from'])
        
        if form.cleaned_data.get('date_to'):
            transactions = transactions.filter(created_at__date__lte=form.cleaned_data['date_to'])
        
        if form.cleaned_data.get('min_amount'):
            transactions = transactions.filter(amount__gte=form.cleaned_data['min_amount'])
        
        if form.cleaned_data.get('max_amount'):
            transactions = transactions.filter(amount__lte=form.cleaned_data['max_amount'])
        
        # Handle CSV export
        if 'export' in request.GET:
            return export_transactions_csv(request, transactions)
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'transactions': page_obj,
    }
    return render(request, 'account/transactions.html', context)


@login_required
def transaction_detail_view(request, transaction_id):
    """View detailed transaction information"""
    transaction_obj = get_object_or_404(
        Transaction.objects.filter(
            models.Q(sender=request.user) | models.Q(receiver=request.user)
        ),
        transaction_id=transaction_id
    )
    
    context = {
        'transaction': transaction_obj,
    }
    return render(request, 'account/transaction_detail.html', context)


@login_required
def payment_request_detail_view(request, request_id):
    """View detailed payment request information"""
    payment_request = get_object_or_404(
        PaymentRequest.objects.filter(
            models.Q(requester=request.user) | models.Q(recipient=request.user)
        ),
        request_id=request_id
    )
    
    # Check expiration
    payment_request.check_expiration()
    
    context = {
        'payment_request': payment_request,
    }
    return render(request, 'account/payment_request_detail.html', context)


# Notification Views
@login_required
def notifications_view(request):
    """View all notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark notifications as read
    unread_notifications = notifications.filter(status='unread')
    unread_notifications.update(status='read', read_at=timezone.now())
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
    }
    return render(request, 'account/notifications.html', context)


@login_required
def mark_notification_read_view(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.status = 'read'
    notification.read_at = timezone.now()
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('account:notifications')


@login_required
def notification_count_view(request):
    """Get notification count for real-time updates"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        unread_count = Notification.objects.filter(
            user=request.user, 
            status='unread'
        ).count()
        
        # Get latest notification for toast
        latest_notification = None
        if unread_count > 0:
            latest = Notification.objects.filter(
                user=request.user,
                status='unread'
            ).order_by('-created_at').first()
            
            if latest:
                latest_notification = {
                    'title': latest.title,
                    'message': latest.message,
                    'type': latest.notification_type
                }
        
        return JsonResponse({
            'count': unread_count,
            'latest_notification': latest_notification
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# Utility Views
def export_transactions_csv(request, transactions):
    """Export transactions to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Transaction ID', 'Date', 'Type', 'Amount', 'Currency', 
        'Sender', 'Receiver', 'Status', 'Description', 'Reference'
    ])
    
    for transaction in transactions:
        writer.writerow([
            transaction.transaction_id,
            transaction.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            transaction.get_transaction_type_display(),
            transaction.amount,
            transaction.currency,
            transaction.sender.email,
            transaction.receiver.email,
            transaction.get_status_display(),
            transaction.description,
            transaction.reference,
        ])
    
    return response
