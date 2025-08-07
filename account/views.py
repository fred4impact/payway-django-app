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
from .forms import KYCForm, AccountSearchForm, MoneyTransferForm, PaymentRequestForm, TransactionFilterForm, CreditCardForm, CardFundingForm, CardWithdrawalForm, InternationalTransferForm, SwiftCodeSearchForm, CurrencyConverterForm
from .models import KYC, Account, Transaction, PaymentRequest, Notification, CreditCard, Currency, Bank, InternationalTransfer
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


# Credit Card Views
@login_required
def credit_cards_view(request):
    """View and manage credit cards"""
    cards = CreditCard.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'cards': cards,
    }
    return render(request, 'account/credit_cards.html', context)


@login_required
def add_credit_card_view(request):
    """Add a new credit card"""
    if request.method == 'POST':
        form = CreditCardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.user = request.user
            
            # Process card data
            card_number = form.cleaned_data['card_number'].replace(' ', '').replace('-', '')
            cvv = form.cleaned_data['cvv']
            
            # Detect card type
            card_type, card_brand = card.detect_card_type(card_number)
            card.card_type = card_type
            card.card_brand = card_brand
            
            # Set display fields
            card.last_four_digits = card.get_last_four_digits(card_number)
            card.masked_number = card.mask_card_number(card_number)
            
            # Encrypt sensitive data
            card.encrypt_card_data(card_number, cvv)
            
            card.save()
            
            messages.success(request, f'{card_brand} card ending in {card.last_four_digits} added successfully!')
            return redirect('account:credit_cards')
    else:
        form = CreditCardForm()
    
    context = {
        'form': form,
    }
    return render(request, 'account/add_credit_card.html', context)


@login_required
def edit_credit_card_view(request, card_id):
    """Edit credit card details"""
    card = get_object_or_404(CreditCard, id=card_id, user=request.user)
    
    if request.method == 'POST':
        form = CreditCardForm(request.POST, instance=card)
        if form.is_valid():
            card = form.save(commit=False)
            
            # Process card data if provided
            if 'card_number' in form.cleaned_data and form.cleaned_data['card_number']:
                card_number = form.cleaned_data['card_number'].replace(' ', '').replace('-', '')
                cvv = form.cleaned_data['cvv']
                
                # Update card type and brand
                card_type, card_brand = card.detect_card_type(card_number)
                card.card_type = card_type
                card.card_brand = card_brand
                
                # Update display fields
                card.last_four_digits = card.get_last_four_digits(card_number)
                card.masked_number = card.mask_card_number(card_number)
                
                # Re-encrypt sensitive data
                card.encrypt_card_data(card_number, cvv)
            
            card.save()
            
            messages.success(request, f'{card.card_brand} card updated successfully!')
            return redirect('account:credit_cards')
    else:
        form = CreditCardForm(instance=card)
    
    context = {
        'form': form,
        'card': card,
    }
    return render(request, 'account/edit_credit_card.html', context)


@login_required
def delete_credit_card_view(request, card_id):
    """Delete a credit card"""
    card = get_object_or_404(CreditCard, id=card_id, user=request.user)
    
    if request.method == 'POST':
        card.delete()
        messages.success(request, f'{card.card_brand} card deleted successfully!')
        return redirect('account:credit_cards')
    
    context = {
        'card': card,
    }
    return render(request, 'account/delete_credit_card.html', context)


@login_required
def card_funding_view(request):
    """Fund account from credit card"""
    if request.method == 'POST':
        form = CardFundingForm(request.user, request.POST)
        if form.is_valid():
            card = form.cleaned_data['card']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description', '')
            
            # Check if card can be used for funding
            if not card.can_fund(amount):
                messages.error(request, 'Card cannot be used for this amount. Check daily/monthly limits.')
                return redirect('account:card_funding')
            
            try:
                with transaction.atomic():
                    # Create transaction record
                    funding_transaction = Transaction.objects.create(
                        transaction_type='card_funding',
                        amount=amount,
                        currency='USD',
                        sender=request.user,
                        receiver=request.user,
                        sender_account=request.user.account,
                        receiver_account=request.user.account,
                        status='completed',
                        description=f'Card funding: {description}' if description else 'Card funding',
                        reference=f'CARD_FUND_{card.last_four_digits}',
                        transaction_fee=Decimal('0.00'),
                        total_amount=amount,
                        is_verified=True,
                        completed_at=timezone.now()
                    )
                    
                    # Update account balance
                    request.user.account.account_balance += amount
                    request.user.account.save()
                    
                    # Update card usage
                    card.total_funded += amount
                    card.last_used = timezone.now()
                    card.save()
                    
                    # Create notification
                    Notification.objects.create(
                        user=request.user,
                        notification_type='transaction',
                        title='Account Funded',
                        message=f'Your account has been funded with ${amount:.2f} from your {card.card_brand} card ending in {card.last_four_digits}.',
                        transaction=funding_transaction
                    )
                    
                    messages.success(request, f'Account funded successfully with ${amount:.2f}!')
                    return redirect('account:transaction_detail', transaction_id=funding_transaction.transaction_id)
                    
            except Exception as e:
                messages.error(request, f'Funding failed: {str(e)}')
                return redirect('account:card_funding')
    else:
        form = CardFundingForm(request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'account/card_funding.html', context)


@login_required
def card_withdrawal_view(request):
    """Withdraw money to credit card"""
    if request.method == 'POST':
        form = CardWithdrawalForm(request.user, request.POST)
        if form.is_valid():
            card = form.cleaned_data['card']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description', '')
            
            # Check if withdrawal is possible
            if not card.can_withdraw(amount):
                messages.error(request, 'Insufficient balance or card cannot be used for withdrawal.')
                return redirect('account:card_withdrawal')
            
            try:
                with transaction.atomic():
                    # Create transaction record
                    withdrawal_transaction = Transaction.objects.create(
                        transaction_type='withdrawal',
                        amount=amount,
                        currency='USD',
                        sender=request.user,
                        receiver=request.user,
                        sender_account=request.user.account,
                        receiver_account=request.user.account,
                        status='completed',
                        description=f'Card withdrawal: {description}' if description else 'Card withdrawal',
                        reference=f'CARD_WITHDRAW_{card.last_four_digits}',
                        transaction_fee=Decimal('0.00'),
                        total_amount=amount,
                        is_verified=True,
                        completed_at=timezone.now()
                    )
                    
                    # Update account balance
                    request.user.account.account_balance -= amount
                    request.user.account.save()
                    
                    # Update card usage
                    card.total_withdrawn += amount
                    card.last_used = timezone.now()
                    card.save()
                    
                    # Create notification
                    Notification.objects.create(
                        user=request.user,
                        notification_type='transaction',
                        title='Withdrawal Completed',
                        message=f'${amount:.2f} has been withdrawn to your {card.card_brand} card ending in {card.last_four_digits}.',
                        transaction=withdrawal_transaction
                    )
                    
                    messages.success(request, f'Withdrawal of ${amount:.2f} completed successfully!')
                    return redirect('account:transaction_detail', transaction_id=withdrawal_transaction.transaction_id)
                    
            except Exception as e:
                messages.error(request, f'Withdrawal failed: {str(e)}')
                return redirect('account:card_withdrawal')
    else:
        form = CardWithdrawalForm(request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'account/card_withdrawal.html', context)


# International Transfer Views
@login_required
def international_transfers_view(request):
    """View for listing international transfers"""
    transfers = InternationalTransfer.objects.filter(sender=request.user).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        transfers = transfers.filter(status=status_filter)
    
    context = {
        'transfers': transfers,
        'status_choices': InternationalTransfer.TRANSFER_STATUS,
        'current_status': status_filter,
    }
    return render(request, 'account/international_transfers.html', context)


@login_required
def create_international_transfer_view(request):
    """View for creating international transfers"""
    if request.method == 'POST':
        form = InternationalTransferForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Get the validated bank from the form
                    bank = form.bank
                    
                    # Calculate transfer fee
                    fee = form.calculate_transfer_fee(
                        form.cleaned_data['amount'], 
                        form.cleaned_data['currency'].code
                    )
                    
                    # Create the international transfer
                    international_transfer = form.save(commit=False)
                    international_transfer.sender = request.user
                    international_transfer.sender_account = request.user.account
                    international_transfer.recipient_bank = bank
                    international_transfer.recipient_swift_code = bank.swift_code
                    international_transfer.transfer_fee = fee
                    international_transfer.exchange_rate = form.cleaned_data['currency'].exchange_rate_to_usd
                    international_transfer.estimated_delivery = timezone.now() + timedelta(days=3)
                    international_transfer.save()
                    
                    # Deduct amount from sender's account
                    sender_account = request.user.account
                    sender_account.account_balance -= (international_transfer.amount + fee)
                    sender_account.save()
                    
                    # Create notification
                    Notification.objects.create(
                        user=request.user,
                        notification_type='transaction',
                        title='International Transfer Initiated',
                        message=f'Your international transfer of {international_transfer.currency.symbol}{international_transfer.amount} to {international_transfer.recipient_name} has been initiated. Transfer ID: {international_transfer.transfer_id}',
                        transaction=None
                    )
                    
                    messages.success(request, f'International transfer initiated successfully! Transfer ID: {international_transfer.transfer_id}')
                    return redirect('account:international_transfer_detail', transfer_id=international_transfer.transfer_id)
                    
            except Exception as e:
                messages.error(request, f'Error creating transfer: {str(e)}')
    else:
        form = InternationalTransferForm()
    
    context = {
        'form': form,
        'currencies': Currency.objects.filter(is_active=True),
    }
    return render(request, 'account/create_international_transfer.html', context)


@login_required
def international_transfer_detail_view(request, transfer_id):
    """View for international transfer details"""
    try:
        transfer = InternationalTransfer.objects.get(
            transfer_id=transfer_id, 
            sender=request.user
        )
    except InternationalTransfer.DoesNotExist:
        messages.error(request, 'Transfer not found.')
        return redirect('account:international_transfers')
    
    context = {
        'transfer': transfer,
    }
    return render(request, 'account/international_transfer_detail.html', context)


@login_required
def swift_code_search_view(request):
    """View for searching SWIFT codes"""
    form = SwiftCodeSearchForm(request.GET)
    banks = Bank.objects.filter(is_active=True)
    
    if form.is_valid():
        search = form.cleaned_data.get('search', '').strip()
        country = form.cleaned_data.get('country', '').strip()
        
        if search:
            banks = banks.filter(
                models.Q(bank_name__icontains=search) |
                models.Q(swift_code__icontains=search) |
                models.Q(country__icontains=search) |
                models.Q(city__icontains=search)
            )
        
        if country:
            banks = banks.filter(country=country)
    
    # Paginate results
    paginator = Paginator(banks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_banks': banks.count(),
    }
    return render(request, 'account/swift_code_search.html', context)


@login_required
def currency_converter_view(request):
    """View for currency conversion"""
    form = CurrencyConverterForm(request.GET)
    conversion_result = None
    
    if form.is_valid():
        try:
            conversion_result = form.convert_currency()
        except Exception as e:
            messages.error(request, f'Error converting currency: {str(e)}')
    
    context = {
        'form': form,
        'conversion_result': conversion_result,
        'currencies': Currency.objects.filter(is_active=True),
    }
    return render(request, 'account/currency_converter.html', context)


@login_required
def transfer_fee_calculator_view(request):
    """View for calculating transfer fees"""
    if request.method == 'POST':
        amount = request.POST.get('amount')
        currency_code = request.POST.get('currency')
        
        if amount and currency_code:
            try:
                amount = Decimal(amount)
                currency = Currency.objects.get(code=currency_code)
                
                # Calculate fee using the same logic as the form
                fee_structure = {
                    'USD': {'percentage': 0.02, 'min_fee': 5.00, 'max_fee': 50.00},
                    'EUR': {'percentage': 0.025, 'min_fee': 5.00, 'max_fee': 60.00},
                    'GBP': {'percentage': 0.03, 'min_fee': 5.00, 'max_fee': 75.00},
                    'JPY': {'percentage': 0.025, 'min_fee': 500.00, 'max_fee': 5000.00},
                    'CAD': {'percentage': 0.025, 'min_fee': 6.00, 'max_fee': 60.00},
                    'AUD': {'percentage': 0.025, 'min_fee': 6.00, 'max_fee': 65.00},
                    'CHF': {'percentage': 0.025, 'min_fee': 5.00, 'max_fee': 55.00},
                    'SGD': {'percentage': 0.025, 'min_fee': 6.00, 'max_fee': 65.00},
                    'HKD': {'percentage': 0.025, 'min_fee': 40.00, 'max_fee': 400.00},
                    'NZD': {'percentage': 0.025, 'min_fee': 7.00, 'max_fee': 70.00},
                }
                
                structure = fee_structure.get(currency_code, fee_structure['USD'])
                percentage_fee = amount * Decimal(str(structure['percentage']))
                fee = max(structure['min_fee'], min(percentage_fee, structure['max_fee']))
                total_amount = amount + fee
                
                return JsonResponse({
                    'success': True,
                    'amount': float(amount),
                    'fee': float(fee),
                    'total_amount': float(total_amount),
                    'currency': currency_code,
                    'currency_symbol': currency.symbol,
                })
                
            except (ValueError, Currency.DoesNotExist):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid amount or currency'
                })
    
    context = {
        'currencies': Currency.objects.filter(is_active=True),
    }
    return render(request, 'account/transfer_fee_calculator.html', context)


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
