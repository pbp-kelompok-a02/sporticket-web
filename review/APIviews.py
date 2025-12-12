from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404

from .models import Review
from event.models import Event
from order.models import Order

def get_reviews_json(request, match_id):
    print(f"DEBUG: View reached with ID: {match_id}")
    """
    API to fetch reviews for a specific event.
    Returns JSON containing review list and user status.
    """
    event = get_object_or_404(Event, match_id=match_id)
    reviews = Review.objects.filter(event=event).select_related('user').order_by('-created_at')
    
    # Check status for the current user
    user_has_ticket = False
    user_has_review = False
    
    if request.user.is_authenticated:
        user_has_ticket = Order.objects.filter(
            user=request.user, 
            ticket__event=event, 
            status='confirmed'
        ).exists()
        
        user_has_review = Review.objects.filter(
            user=request.user, 
            event=event
        ).exists()

    # Manual serialization to control exactly what data is sent
    data = []
    for review in reviews:
        data.append({
            "id": review.id,
            "user": review.user.username,
            "rating": review.rating,
            "komentar": review.komentar,
            "created_at": review.created_at.isoformat(),
            "is_current_user": request.user == review.user
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