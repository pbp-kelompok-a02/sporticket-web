from django.http import JsonResponse, Http404
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404

from .models import Review
from event.models import Event
from order.models import Order

def get_reviews_json(request, match_id):

    print(f"User yang sedang request: {request.user}")
    print(f"Apakah user authenticated? {request.user.is_authenticated}")
    event = get_object_or_404(Event, match_id=match_id)

    user_has_ticket = False
    user_has_review = False

    # Cek status tiket & review
    if request.user.is_authenticated:
        try:
            user_has_ticket = Order.objects.filter(user=request.user, ticket__event=event, status='confirmed').exists()
        except NameError:
            user_has_ticket = True 
            
        # Cek apakah user sudah pernah review
        user_has_review = Review.objects.filter(event=event, user=request.user).exists()
        
    reviews = Review.objects.filter(event=event).select_related('user', 'user__profile').order_by('-created_at')

    data = []
    for review in reviews:
        profile_photo_url = None
        
        # Check if user has a profile, and if that profile has an photo
        try:
            if review.user.profile.profile_photo:
                profile_photo_url = review.user.profile.profile_photo.url
        except AttributeError:
            profile_photo_url = None
        display_name = None
        try:
            prof = review.user.profile
            try:
                display_name = prof.get_display_name()
            except Exception:
                display_name = prof.name or ''
        except Exception:
            display_name = ''

        if not display_name:
            try:
                full_name = review.user.get_full_name()
                if full_name and full_name.strip():
                    display_name = full_name
                else:
                    display_name = review.user.username
            except Exception:
                display_name = review.user.username

        data.append({
            "id": review.id,
            "user": display_name,
            "user_id": review.user.id,
            "rating": review.rating,
            "komentar": review.komentar,
            "created_at": review.created_at.isoformat(),
            "is_current_user": request.user == review.user,
            "profile_photo": profile_photo_url,
        })

    return JsonResponse({
        "reviews": data,
        "user_has_ticket": user_has_ticket, 
        "user_has_review": user_has_review,
        "event_name": event.name 
    })

@csrf_exempt
def add_review_flutter(request, match_id):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Authentication required"}, status=401)

        event = get_object_or_404(Event, match_id=match_id)

        # Cek tiket (Server-side validation)
        if not Order.objects.filter(user=request.user, ticket__event=event, status='confirmed').exists():
            return JsonResponse({'status': 'error', 'message': 'You need to buy a ticket first.'}, status=403)

        try:
            data = json.loads(request.body)
            rating = int(data.get("rating"))
            komentar = data.get("komentar", "").strip()

            if not (1 <= rating <= 5):
                return JsonResponse({"status": "error", "message": "Rating must be between 1 and 5"}, status=400)
            
            if not komentar:
                return JsonResponse({"status": "error", "message": "Comment cannot be empty"}, status=400)

            review, created = Review.objects.update_or_create(
                user=request.user,
                event=event,
                defaults={'rating': rating, 'komentar': komentar}
            )

            return JsonResponse({"status": "success", "message": "Review saved successfully", "username": request.user.username})

        except ValueError:
            return JsonResponse({"status": "error", "message": "Invalid data format"}, status=400)
    
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

@csrf_exempt
def edit_review_flutter(request, match_id, review_id):
    if request.method == 'POST': # Use POST for simplicity in Flutter
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Authentication required"}, status=401)

        # Get the specific review and ensure it belongs to the user
        review = get_object_or_404(Review, id=review_id)

        if review.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

        try:
            data = json.loads(request.body)
            rating = int(data.get("rating"))
            komentar = data.get("komentar", "").strip()

            if not (1 <= rating <= 5):
                return JsonResponse({"status": "error", "message": "Rating must be between 1 and 5"}, status=400)

            review.rating = rating
            review.komentar = komentar
            review.save()

            return JsonResponse({"status": "success", "message": "Review updated successfully"})

        except ValueError:
            return JsonResponse({"status": "error", "message": "Invalid data format"}, status=400)
            
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

@csrf_exempt
def delete_review_flutter(request, match_id, review_id):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Authentication required"}, status=401)

        review = get_object_or_404(Review, id=review_id)
        
        # Security check
        if review.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
        review.delete()
        return JsonResponse({"status": "success", "message": "Review deleted successfully"})

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)