from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    # KYC and Account Info
    path('kyc/', views.kyc_view, name='kyc'),
    path('kyc/detail/', views.kyc_detail_view, name='kyc_detail'),
    path('info/', views.account_info_view, name='account_info'),
    
    # Money Transfer System
    path('search/', views.search_account_view, name='search_account'),
    path('transfer/', views.money_transfer_view, name='money_transfer'),
    
    # Payment Requests
    path('request/create/', views.create_payment_request_view, name='create_payment_request'),
    path('requests/', views.payment_requests_view, name='payment_requests'),
    path('request/<str:request_id>/', views.payment_request_detail_view, name='payment_request_detail'),
    path('request/<str:request_id>/settle/', views.settle_payment_request_view, name='settle_payment_request'),
    
    # Transaction Management
    path('transactions/', views.transactions_view, name='transactions'),
    path('transaction/<str:transaction_id>/', views.transaction_detail_view, name='transaction_detail'),
    
    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/count/', views.notification_count_view, name='notification_count'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read_view, name='mark_notification_read'),
    
    # Credit Cards
    path('cards/', views.credit_cards_view, name='credit_cards'),
    path('cards/add/', views.add_credit_card_view, name='add_credit_card'),
    path('cards/<int:card_id>/edit/', views.edit_credit_card_view, name='edit_credit_card'),
    path('cards/<int:card_id>/delete/', views.delete_credit_card_view, name='delete_credit_card'),
    path('cards/fund/', views.card_funding_view, name='card_funding'),
    path('cards/withdraw/', views.card_withdrawal_view, name='card_withdrawal'),

    # International Transfer URLs
    path('international/', views.international_transfers_view, name='international_transfers'),
    path('international/create/', views.create_international_transfer_view, name='create_international_transfer'),
    path('international/<str:transfer_id>/', views.international_transfer_detail_view, name='international_transfer_detail'),
    path('swift-search/', views.swift_code_search_view, name='swift_code_search'),
    path('currency-converter/', views.currency_converter_view, name='currency_converter'),
    path('fee-calculator/', views.transfer_fee_calculator_view, name='transfer_fee_calculator'),
] 