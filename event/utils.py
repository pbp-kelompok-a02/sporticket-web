from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.http import HttpResponseForbidden

def is_admin(user):
    """Check if user has Admin role"""
    return hasattr(user, 'profile') and user.profile.role == 'Admin'

def admin_required(view_func):
    """Decorator to require admin role"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('account:login')
        if not is_admin(request.user):
            return HttpResponseForbidden("You don't have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view