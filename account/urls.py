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
] 