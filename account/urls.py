from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('kyc/', views.kyc_view, name='kyc'),
    path('kyc/detail/', views.kyc_detail_view, name='kyc_detail'),
    path('info/', views.account_info_view, name='account_info'),
] 