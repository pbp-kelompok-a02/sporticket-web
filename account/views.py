import base64
import uuid
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.contrib.auth import (
    login, logout, get_user_model, update_session_auth_hash, authenticate
)
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import RegistrationForm, EmailAuthenticationForm, ProfileUpdateForm
from django.core import serializers
from django.core.files.base import ContentFile
from django.urls import reverse
import datetime
from .models import Profile
import json
from django.views.decorators.csrf import csrf_exempt

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
    is_admin_viewer = False
    if viewer is not None:
        is_admin_viewer = viewer.is_superuser or (viewer_role == 'Admin')

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
    profiles = Profile.objects.select_related('user').all()
    data = [
        {
            'id': profile.id,
            'user_id': profile.user.id,
            'username': profile.user.username,
            'email': profile.email,
            'name': profile.name,
            'role': profile.role,
            'phone_number': profile.phone_number,
            'profile_photo': profile.profile_photo.url if profile.profile_photo else None,
        }
        for profile in profiles
    ]
    return JsonResponse(data, safe=False)

def show_xml_by_id_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    data = serializers.serialize('xml', [user])
    return HttpResponse(data, content_type='application/xml')

def show_json_by_id_user(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        profile = user.profile
        data = {
            'id': profile.id,
            'user_id': user.id,
            'username': user.username,
            'email': profile.email,
            'name': profile.name,
            'role': profile.role,
            'phone_number': profile.phone_number,
            'profile_photo': profile.profile_photo.url if profile.profile_photo else None,
        }
        return JsonResponse(data)
    except (User.DoesNotExist, Profile.DoesNotExist):
        return JsonResponse({'detail': 'Not found'}, status=404)

@csrf_exempt
def login_mobile(request):
    if request.method == 'POST':
        username = None
        password = None
        remember_me = False

        try:
            # coba ambil dari POST dulu
            if 'username' in request.POST or 'password' in request.POST:
                username = request.POST.get('username')
                password = request.POST.get('password')
                remember_me = request.POST.get('remember_me') == 'true'
            
            # kalo ga ada di POST, coba ambil dari JSON body
            else:
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
                rm_val = data.get('remember_me')
                remember_me = rm_val == True or rm_val == 'true'

            # validasi credentials
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    if remember_me:
                        request.session.set_expiry(1209600)  # 14 hari
                    else:
                        request.session.set_expiry(0) # saat browser ditutup
                    
                    response = JsonResponse({
                        "status": True,
                        "message": "Login successful!",
                        "username": user.username,
                    }, status=200)
                    response.set_cookie('last_login', str(datetime.datetime.now()))
                    return response
                else:
                    return JsonResponse({
                        "status": False,
                        "message": "Account is not active."
                    }, status=401)
            else:
                return JsonResponse({
                    "status": False,
                    "message": "Email or password is wrong."
                }, status=401)

        except Exception as e:
            return JsonResponse({"status": False, "message": f"Server Error: {str(e)}"}, status=500)
            
    return JsonResponse({"status": False, "message": "Method not allowed"}, status=405)

@csrf_exempt
def register_mobile(request):
    if request.method == 'POST':
        try:            
            # handle JSON body atau form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                name = data.get('name', '')
                email = data.get('email', '')
                password = data.get('password', '')
                password2 = data.get('password2', '')
                phone_number = data.get('phone_number', '')
                image_base64 = data.get('profile_photo', '')
            else:
                name = request.POST.get('name', '')
                email = request.POST.get('email', '')
                password = request.POST.get('password', '')
                password2 = request.POST.get('password2', '')
                phone_number = request.POST.get('phone_number', '')
                image_base64 = request.POST.get('profile_photo', '')

            # validasi input
            if not email or not password or not name:
                return JsonResponse({'success': False, 'message': 'All fields (name, email, password) are required.'}, status=400)
            
            if '@' not in email:
                 return JsonResponse({'success': False, 'message': 'Invalid email address.'}, status=400)

            if password != password2:
                return JsonResponse({'success': False, 'message': 'Passwords do not match.'}, status=400)
            
            if User.objects.filter(username=email).exists():
                return JsonResponse({'success': False, 'message': 'Email is already registered.'}, status=400)

            # handle foto profile
            profile_photo_file = None
            if image_base64:
                try:
                    if ';base64,' in image_base64:
                        format, imgstr = image_base64.split(';base64,') 
                        ext = format.split('/')[-1] 
                        image_bytes = base64.b64decode(imgstr)
                    else:
                        imgstr = image_base64
                        ext = "jpg"
                        image_bytes = base64.b64decode(imgstr)
                    
                    filename = f"profile_{uuid.uuid4()}.{ext}"
                    profile_photo_file = ContentFile(image_bytes, name=filename)
                except Exception as e:
                    return JsonResponse({'success': False, 'message': f'Error processing image: {str(e)}'}, status=400)

            # handle empty phone number
            if not phone_number:
                phone_number = None

            # buat user dan profile
            try:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password
                )
                
                Profile.objects.create(
                    user=user,
                    name=name,
                    role='Buyer', 
                    phone_number=phone_number,
                    profile_photo=profile_photo_file
                )
            except IntegrityError as e:
                # handle unique constraint failures
                if 'phone_number' in str(e):
                    # hapus user yg baru dibuat karena gagal buat profile
                    user.delete()
                    return JsonResponse({'success': False, 'message': 'Phone number is already in use.'}, status=400)
                else:
                    user.delete()
                    return JsonResponse({'success': False, 'message': f'Database error: {str(e)}'}, status=500)

            return JsonResponse({
                "success": True,
                "message": "Registration successful! Please login.",
            }, status=200)

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

@csrf_exempt
def profile_mobile(request, user_id=None):
    try:
        # tentukan user target
        if user_id:
            target_user = get_object_or_404(User, pk=user_id)
        else:
            target_user = request.user

        # cek hak akses viewer
        viewer = request.user
        viewer_is_admin = viewer.is_superuser or (
            hasattr(viewer, 'profile') and viewer.profile.role == 'Admin'
        )
        is_own_profile = (viewer.pk == target_user.pk)
        can_see_sensitive_data = is_own_profile or viewer_is_admin

        # ambil data profile (handle jika profile tidak ada)
        if hasattr(target_user, 'profile'):
            profile = target_user.profile
            profile_id = profile.id
            user_pk = target_user.pk
            name = profile.name
            role = profile.role
            phone_number = profile.phone_number
            profile_photo = profile.profile_photo.url if profile.profile_photo else None
        else:
            # fallback jika superuser/user tanpa profile
            profile_id = None 
            user_pk = target_user.pk
            name = None
            role = 'Admin' if target_user.is_superuser else 'User'
            phone_number = None
            profile_photo = None

        data = {
            'id': profile_id,
            'user_id': user_pk,
            'username': target_user.username,
            'email': target_user.email,
            'name': name,
            'role': role,
            'phone_number': phone_number,
            'profile_photo': profile_photo,
            'is_superuser': target_user.is_superuser,
            'is_own_profile': is_own_profile,
            'can_see_sensitive_data': can_see_sensitive_data,
        }
        return JsonResponse({'status': True, 'data': data}, status=200)
    except Exception as e:
        return JsonResponse({'status': False, 'message': str(e)}, status=500)

@csrf_exempt
@login_required
def edit_profile_mobile(request):
    if request.method == 'POST':
        try:
            user = request.user
            profile = user.profile
            
            # handle JSON body
            data = json.loads(request.body)
            
            # update fields kalo ada di data
            if 'name' in data:
                profile.name = data['name']
            if 'phone_number' in data:
                phone_number = data['phone_number']
                # set to None kalo empty string untuk hindari unique constraint
                profile.phone_number = phone_number if phone_number else None
                
            # handle profile photo update
            image_base64 = data.get('profile_photo')
            if image_base64:
                try:
                    # decode base64 image
                    if ';base64,' in image_base64:
                        format, imgstr = image_base64.split(';base64,') 
                        ext = format.split('/')[-1] 
                        image_bytes = base64.b64decode(imgstr)
                    else:
                        imgstr = image_base64
                        ext = "jpg"
                        image_bytes = base64.b64decode(imgstr)
                    
                    filename = f"profile_{uuid.uuid4()}.{ext}"
                    profile_photo_file = ContentFile(image_bytes, name=filename)
                    
                    # hapus foto lama kalo ada
                    if profile.profile_photo:
                        profile.profile_photo.delete(save=False)
                        
                    profile.profile_photo = profile_photo_file
                except Exception as e:
                    return JsonResponse({'status': False, 'message': f'Error processing image: {str(e)}'}, status=400)
            
            profile.save()
            
            return JsonResponse({'status': True, 'message': 'Profile updated successfully!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'status': False, 'message': 'Invalid method'}, status=405)

@csrf_exempt
@login_required
def change_password_mobile(request):
    if request.method == 'POST':
        try:
            # coba ambil dari POST dulu
            if 'current_password' in request.POST:
                current_password = request.POST.get('current_password')
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
            
            # kalo ga ada di POST, coba ambil dari JSON body
            else:
                data = json.loads(request.body)
                current_password = data.get('current_password')
                new_password = data.get('new_password')
                confirm_password = data.get('confirm_password')

            # validasi input
            if not all([current_password, new_password, confirm_password]):
                return JsonResponse({'status': False, 'message': 'All fields are required'}, status=400)

            user = request.user
            
            # cek current password
            if not user.check_password(current_password):
                return JsonResponse({'status': False, 'message': 'Current password is incorrect'}, status=400)
            
            # current password ga boleh sama dengan new password
            if current_password == new_password:
                return JsonResponse({'status': False, 'message': 'New password must be different from current password'}, status=400)
            
            # cek kecocokan new password dan confirm password
            if new_password != confirm_password:
                return JsonResponse({'status': False, 'message': 'New passwords do not match'}, status=400)
                
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # buat session tetap valid setelah ganti password
            
            return JsonResponse({'status': True, 'message': 'Password changed successfully!'}, status=200)
            
        except json.JSONDecodeError:
            return JsonResponse({'status': False, 'message': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, status=500)

    return JsonResponse({'status': False, 'message': 'Invalid method'}, status=405)

@csrf_exempt
def logout_mobile(request):
    logout(request)
    return JsonResponse({"status": True, "message": "Logout successful!"}, status=200)

# delete account mobile
@csrf_exempt
@require_POST
def delete_account_mobile(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': False, 'message': 'Login required.'}, status=401)
    
    user = request.user
    try:
        user.delete()
        request.session.flush()
        logout(request)
        return JsonResponse({'status': True, 'message': 'Account deleted successfully.'}, status=200)
    except Exception as e:
        return JsonResponse({'status': False, 'message': f'Failed to delete account: {e}'}, status=500)