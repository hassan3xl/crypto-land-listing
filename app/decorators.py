from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from app.models import UserRole


def buyer_required(view_func):
    """Decorator to restrict view access to buyers only."""
    @wraps(view_func)
    @login_required(login_url='app:login')
    def wrapper(request, *args, **kwargs):
        if request.user.is_buyer() or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'This action is reserved for Buyers.')
        return redirect('app:home')
    return wrapper


def seller_required(view_func):
    """Decorator to restrict view access to sellers and admins."""
    @wraps(view_func)
    @login_required(login_url='app:login')
    def wrapper(request, *args, **kwargs):
        if request.user.is_seller() or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'You must be a registered Seller to access this section.')
        return redirect('app:home')
    return wrapper


def admin_required(view_func):
    """Decorator to restrict view access to administrators only."""
    @wraps(view_func)
    @login_required(login_url='app:login')
    def wrapper(request, *args, **kwargs):
        if request.user.is_admin_user():
            return view_func(request, *args, **kwargs)
        messages.error(request, 'This area is restricted to Platform Administrators.')
        return redirect('app:home')
    return wrapper
