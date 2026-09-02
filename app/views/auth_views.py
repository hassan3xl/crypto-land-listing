from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from app.forms.auth_forms import UserRegistrationForm, CustomLoginForm


def register_view(request):
    """User registration view supporting Buyer and Seller role selection."""
    if request.user.is_authenticated:
        return redirect('app:home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to MyApp, {user.first_name or user.username}! Your account is active.")
            if user.is_seller():
                return redirect('app:seller_dashboard')
            return redirect('app:buyer_dashboard')
        else:
            messages.error(request, "Registration failed. Please correct the highlighted errors.")
    else:
        role_param = request.GET.get('role', 'buyer')
        form = UserRegistrationForm(initial={'role': role_param})

    return render(request, 'app/register.html', {'form': form})


def login_view(request):
    """User authentication login view."""
    if request.user.is_authenticated:
        return redirect('app:home')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_admin_user():
                return redirect('app:admin_dashboard')
            elif user.is_seller():
                return redirect('app:seller_dashboard')
            return redirect('app:buyer_dashboard')
        else:
            messages.error(request, "Invalid username/email or password.")
    else:
        form = CustomLoginForm()

    return render(request, 'app/login.html', {'form': form})


def logout_view(request):
    """Logs out the current user session."""
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('app:home')
