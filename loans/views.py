from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import LoanProduct, LoanApplication, Loan, SupportedCryptocurrency

def loans_home_view(request):
    """Crypto loans home page"""
    loan_products = LoanProduct.objects.filter(is_active=True)
    supported_crypto = SupportedCryptocurrency.objects.filter(is_active=True)
    
    context = {
        'loan_products': loan_products,
        'supported_crypto': supported_crypto,
    }
    
    return render(request, 'loans/home.html', context)

@login_required
def loan_application_view(request):
    """Apply for a crypto loan"""
    if request.method == 'POST':
        product_id = request.POST.get('loan_product')
        crypto_id = request.POST.get('collateral_cryptocurrency')
        requested_amount = request.POST.get('requested_amount')
        collateral_amount = request.POST.get('collateral_amount')
        term_days = request.POST.get('requested_term_days')
        
        try:
            product = LoanProduct.objects.get(id=product_id)
            crypto = SupportedCryptocurrency.objects.get(id=crypto_id)
            
            # Calculate collateral value (mock calculation)
            collateral_value_usd = float(collateral_amount) * float(crypto.current_price_usd)
            ltv_ratio = float(requested_amount) / collateral_value_usd
            
            application = LoanApplication.objects.create(
                user=request.user,
                loan_product=product,
                requested_amount=requested_amount,
                requested_term_days=term_days,
                collateral_cryptocurrency=crypto,
                collateral_amount=collateral_amount,
                collateral_value_usd=collateral_value_usd,
                loan_to_value_ratio=ltv_ratio,
            )
            
            messages.success(request, 'Loan application submitted successfully!')
            return redirect('loans:my_loans')
            
        except Exception as e:
            messages.error(request, f'Application failed: {str(e)}')
    
    loan_products = LoanProduct.objects.filter(is_active=True)
    supported_crypto = SupportedCryptocurrency.objects.filter(is_active=True)
    
    context = {
        'loan_products': loan_products,
        'supported_crypto': supported_crypto,
    }
    
    return render(request, 'loans/application.html', context)

@login_required
def my_loans_view(request):
    """User's loan applications and active loans"""
    applications = LoanApplication.objects.filter(user=request.user).order_by('-created_at')
    active_loans = Loan.objects.filter(user=request.user, status='active')
    
    context = {
        'applications': applications,
        'active_loans': active_loans,
    }
    
    return render(request, 'loans/my_loans.html', context)

@login_required
def loan_detail_view(request, loan_id):
    """Detailed view of a specific loan"""
    loan = get_object_or_404(Loan, id=loan_id, user=request.user)
    
    # Get payment history
    payments = loan.payments.all().order_by('-created_at')
    
    # Get collateral transactions
    collateral_transactions = loan.collateral_transactions.all().order_by('-created_at')
    
    context = {
        'loan': loan,
        'payments': payments,
        'collateral_transactions': collateral_transactions,
    }
    
    return render(request, 'loans/loan_detail.html', context)

@login_required
def collateral_management_view(request):
    """Manage collateral for loans"""
    from .models import CryptoWallet
    wallets = CryptoWallet.objects.filter(user=request.user)
    
    context = {
        'wallets': wallets,
    }
    
    return render(request, 'loans/collateral.html', context)

# API Views
class SupportedCryptocurrencyAPIView(generics.ListAPIView):
    """API for supported cryptocurrencies"""
    queryset = SupportedCryptocurrency.objects.filter(is_active=True)
    
    def list(self, request, *args, **kwargs):
        cryptos = self.get_queryset()
        
        data = [{
            'id': crypto.id,
            'name': crypto.name,
            'symbol': crypto.symbol,
            'network': crypto.network,
            'min_collateral_amount': str(crypto.min_collateral_amount),
            'loan_to_value_ratio': crypto.loan_to_value_ratio,
            'current_price_usd': str(crypto.current_price_usd),
        } for crypto in cryptos]
        
        return Response(data)

class LoanProductAPIView(generics.ListAPIView):
    """API for loan products"""
    queryset = LoanProduct.objects.filter(is_active=True)
    
    def list(self, request, *args, **kwargs):
        products = self.get_queryset()
        
        data = [{
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'min_loan_amount': str(product.min_loan_amount),
            'max_loan_amount': str(product.max_loan_amount),
            'annual_interest_rate': product.annual_interest_rate,
            'min_term_days': product.min_term_days,
            'max_term_days': product.max_term_days,
        } for product in products]
        
        return Response(data)

class LoanApplicationAPIView(generics.ListCreateAPIView):
    """API for loan applications"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LoanApplication.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        try:
            product = LoanProduct.objects.get(id=request.data.get('loan_product_id'))
            crypto = SupportedCryptocurrency.objects.get(id=request.data.get('crypto_id'))
            
            # Calculate values
            collateral_amount = float(request.data.get('collateral_amount'))
            requested_amount = float(request.data.get('requested_amount'))
            collateral_value_usd = collateral_amount * float(crypto.current_price_usd)
            ltv_ratio = requested_amount / collateral_value_usd
            
            application = LoanApplication.objects.create(
                user=request.user,
                loan_product=product,
                requested_amount=requested_amount,
                requested_term_days=request.data.get('term_days'),
                collateral_cryptocurrency=crypto,
                collateral_amount=collateral_amount,
                collateral_value_usd=collateral_value_usd,
                loan_to_value_ratio=ltv_ratio,
            )
            
            return Response({
                'success': True,
                'application_id': str(application.id),
                'message': 'Application submitted successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)

class LoanAPIView(generics.ListAPIView):
    """API for active loans"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Loan.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        loans = self.get_queryset()
        
        data = [{
            'id': str(loan.id),
            'principal_amount': str(loan.principal_amount),
            'interest_rate': loan.interest_rate,
            'outstanding_balance': str(loan.outstanding_balance),
            'status': loan.status,
            'current_ltv_ratio': loan.current_ltv_ratio,
            'next_payment_due': loan.next_payment_due.isoformat(),
            'maturity_date': loan.maturity_date.isoformat(),
        } for loan in loans]
        
        return Response(data)
