from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    path('', views.loans_home_view, name='loans_home'),
    path('apply/', views.loan_application_view, name='loan_application'),
    path('my-loans/', views.my_loans_view, name='my_loans'),
    path('loan/<uuid:loan_id>/', views.loan_detail_view, name='loan_detail'),
    path('collateral/', views.collateral_management_view, name='collateral_management'),
    path('api/supported-crypto/', views.SupportedCryptocurrencyAPIView.as_view(), name='api_supported_crypto'),
    path('api/loan-products/', views.LoanProductAPIView.as_view(), name='api_loan_products'),
    path('api/loan-applications/', views.LoanApplicationAPIView.as_view(), name='api_loan_applications'),
    path('api/loans/', views.LoanAPIView.as_view(), name='api_loans'),
]
