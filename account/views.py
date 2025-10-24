from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.contrib.auth import (
    login, logout, get_user_model, update_session_auth_hash
)
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import RegistrationForm, EmailAuthenticationForm, ProfileUpdateForm
from django.core import serializers
from django.urls import reverse
import datetime

User = get_user_model()

def get_user_role(user):
    if hasattr(user, 'profile') and user.profile:
        return user.profile.role
    return 'Buyer'

def register(request):
    if request.user.is_authenticated:
        return redirect('event:show_event_main')
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                
                # handle request AJAX
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'message': 'Registration successful!'
                    })
                else:
                    # submission form normal
                    messages.success(request, 'Registration successful!')
                    return redirect('account:login')
                    
            except Exception as e:
                error_msg = f'Registration failed: {str(e)}'
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_msg}, status=400)
                else:
                    messages.error(request, error_msg)
        else:
            # handle validation errors
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({
                    'success': False,
                    'message': 'Please correct the errors below.',
                    'errors': errors
                }, status=400)
            else:
                # untuk yang bukan AJAX, render form dengan error
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    
    else:
        form = RegistrationForm()

    context = {'form': form}
    return render(request, 'account/register.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('event:show_event_main')
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)        
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # handle fungsi remember me
            remember_me = request.POST.get('remember') == 'on'
            if remember_me:
                # set session agar bertahan 2 minggu
                request.session.set_expiry(1209600)  # 14 hari dalam detik
            else:
                # session berakhir saat browser ditutup
                request.session.set_expiry(0)
            
            # handle request AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                response = JsonResponse({
                    'success': True, 
                    'message': 'Login successful!',
                    'redirect_url': reverse('event:show_event_main')
                })
                response.set_cookie('last_login', str(datetime.datetime.now()))
                return response
            else:
                # submission form normal
                response = HttpResponseRedirect(reverse('event:show_event_main'))
                response.set_cookie('last_login', str(datetime.datetime.now()))
                return response
        else:
            # handle invalid credentials
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': 'Invalid email or password'
                }, status=400)
            else:
                for error in form.non_field_errors():
                    messages.error(request, error)
    else:
        form = EmailAuthenticationForm(request)

    context = {'form': form}
    return render(request, 'account/login.html', context)

def logout_view(request):
    logout(request)
    response = HttpResponseRedirect(reverse('event:show_event_main'))
    response.delete_cookie('last_login')
    return response

def profile_view(request, user_id=None):
    if user_id:
        target_user = get_object_or_404(User, pk=user_id)
    else:
        if not request.user.is_authenticated:
            return redirect('account:login')
        target_user = request.user

    viewer = request.user if request.user.is_authenticated else None
    viewer_profile = getattr(viewer, 'profile', None) if viewer else None
    viewer_role = getattr(viewer_profile, 'role', None) if viewer_profile else None

    is_own_profile = (viewer is not None and viewer.pk == target_user.pk)
    is_admin_viewer = (viewer is not None and viewer_role == 'Admin')

    context = {
        'profile_user': target_user,
        'is_own_profile': is_own_profile,
        'is_admin_viewer': is_admin_viewer,
        'can_edit': is_own_profile,
        'can_see_sensitive_data': is_own_profile or is_admin_viewer,
    }

    return render(request, 'account/profile.html', context)

@login_required
@require_POST
def profile_update(request):
    # fungsi ini meng-handle update profile baik untuk AJAX maupun non-AJAX
    form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
    
    if form.is_valid():
        try:
            profile = form.save()
            
            # AJAX response
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Profile updated successfully!',
                    'data': {
                        'name': profile.name,
                        'phone_number': profile.phone_number or '',
                        'email': profile.user.email,
                        'profile_photo_url': profile.profile_photo.url if profile.profile_photo else ''
                    }
                })
            else:
                # Normal form submission
                messages.success(request, 'Profile updated successfully!')
                return redirect('account:profile')
                
        except Exception as e:
            error_msg = f'Error updating profile: {str(e)}'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=400)
            else:
                messages.error(request, error_msg)
                return redirect('account:profile')
    else:
        # form validation errors
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors below.',
                'errors': errors
            }, status=400)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return redirect('account:profile')

@login_required
@require_POST
def change_password(request):
    current = request.POST.get('current_password')
    new = request.POST.get('new_password')
    new2 = request.POST.get('new_password2')

    # validasi
    if not all([current, new, new2]):
        msg = 'All password fields are required.'
        return handle_password_response(request, msg, False)

    if new != new2:
        msg = 'New passwords do not match.'
        return handle_password_response(request, msg, False)

    user = request.user
    if not user.check_password(current):
        msg = 'Current password is incorrect.'
        return handle_password_response(request, msg, False)

    try:
        user.set_password(new)
        user.save(update_fields=['password'])
        update_session_auth_hash(request, user)
        msg = 'Password changed successfully!'
        return handle_password_response(request, msg, True)
    except Exception as e:
        msg = f'Failed to change password: {e}'
        return handle_password_response(request, msg, False)

def handle_password_response(request, message, success):
    # helper function untuk handle ajax dan non-ajax response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        status = 200 if success else 400
        return JsonResponse({'success': success, 'message': message}, status=status)
    else:
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        return redirect('account:profile')

@login_required
@require_POST
def delete_account(request):
    user = request.user
    try:
        user.delete()
        request.session.flush()
        logout(request)
        messages.success(request, 'Account deleted successfully.')
        return redirect('event:show_event_main')
    except Exception as e:
        messages.error(request, f'Failed to delete account: {e}')
        return redirect('account:profile')
    
def show_xml_user(request):
    users = User.objects.all()
    data = serializers.serialize('xml', users)
    return HttpResponse(data, content_type='application/xml')

def show_json_user(request):
    users = User.objects.all()
    data = serializers.serialize('json', users)
    return HttpResponse(data, content_type='application/json')

def show_xml_by_id_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    data = serializers.serialize('xml', [user])
    return HttpResponse(data, content_type='application/xml')

def show_json_by_id_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    data = serializers.serialize('json', [user])
    return HttpResponse(data, content_type='application/json')