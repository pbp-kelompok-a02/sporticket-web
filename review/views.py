from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from .models import Review
from event.models import Event
from order.models import Order

@login_required(login_url='/login/')
@require_POST
def add_review(request, match_id):
    try:
        event = get_object_or_404(Event, match_id=match_id)
        
        # Check if user has confirmed ticket
        if not Order.objects.filter(user=request.user, ticket__event=event, status='confirmed').exists():
            return JsonResponse({'success': False, 'message': 'Anda belum membeli tiket untuk event ini.'}, status=403)
        
        # Validate data
        rating = request.POST.get('rating')
        komentar = request.POST.get('komentar', '').strip()
        
        if not rating:
            return JsonResponse({'success': False, 'message': 'Rating harus diisi.'}, status=400)
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return JsonResponse({'success': False, 'message': 'Rating harus antara 1-5.'}, status=400)
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'message': 'Rating harus berupa angka.'}, status=400)
        
        if not komentar:
            return JsonResponse({'success': False, 'message': 'Komentar harus diisi.'}, status=400)
        
        # Create or update review
        review, created = Review.objects.update_or_create(
            user=request.user,
            event=event,
            defaults={'rating': rating, 'komentar': komentar}
        )
        
        # Render template - handle potential template errors
        try:
            html = render_to_string('review/card_review.html', {
                'review': review, 
                'user': request.user,
                'event': event
            }, request=request)
        except TemplateDoesNotExist:
            html = f"<div>Review by {review.user.username}: {review.rating}/5 - {review.komentar}</div>"
        except Exception as e:
            print(f"Template rendering error: {e}")
            html = f"<div>Review by {review.user.username}</div>"
        
        return JsonResponse({
            'success': True, 
            'html': html, 
            'created': created,
            'message': 'Review berhasil ditambahkan.' if created else 'Review berhasil diperbarui.'
        })
        
    except Exception as e:
        print(f"Error in add_review: {e}")
        return JsonResponse({'success': False, 'message': 'Terjadi kesalahan server.'}, status=500)

@login_required(login_url='/login/')
@require_POST
def edit_review(request, match_id, review_id):
    try:
        # Get review and validate
        review = get_object_or_404(Review, id=review_id)
        
        # Ensure review belongs to the correct event
        if review.event.match_id != match_id:
            return JsonResponse({'success': False, 'message': 'Review tidak ditemukan untuk event ini.'}, status=404)
        
        # Ensure user owns the review
        if review.user != request.user:
            return JsonResponse({'success': False, 'message': 'Anda tidak memiliki izin untuk mengedit review ini.'}, status=403)
        
        # Validate data
        rating = request.POST.get('rating')
        komentar = request.POST.get('komentar', '').strip()
        
        if not rating:
            return JsonResponse({'success': False, 'message': 'Rating harus diisi.'}, status=400)
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return JsonResponse({'success': False, 'message': 'Rating harus antara 1-5.'}, status=400)
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'message': 'Rating harus berupa angka.'}, status=400)
        
        if not komentar:
            return JsonResponse({'success': False, 'message': 'Komentar harus diisi.'}, status=400)
        
        # Update review
        review.rating = rating
        review.komentar = komentar
        review.save()
        
        # Render template with error handling
        try:
            html = render_to_string('review/card_review.html', {
                'review': review, 
                'user': request.user,
                'event': review.event
            }, request=request)
        except Exception as e:
            print(f"Template rendering error in edit: {e}")
            html = f"<div>Updated review: {review.rating}/5 - {review.komentar}</div>"
        
        return JsonResponse({
            'success': True, 
            'html': html, 
            'review_id': review.id,
            'message': 'Review berhasil diperbarui.'
        })
        
    except Exception as e:
        print(f"Error in edit_review: {e}")
        return JsonResponse({'success': False, 'message': 'Terjadi kesalahan server.'}, status=500)

@login_required(login_url='/login/')
@require_POST
def delete_review(request, match_id, review_id):
    try:
        # Get review and validate ownership - FIXED: use filter to avoid MultipleObjectsReturned
        review = Review.objects.filter(id=review_id, user=request.user).first()
        if not review:
            return JsonResponse({'success': False, 'message': 'Review tidak ditemukan atau Anda tidak memiliki akses.'}, status=404)
        
        # Ensure review belongs to the correct event
        if review.event.match_id != match_id:
            return JsonResponse({'success': False, 'message': 'Review tidak ditemukan untuk event ini.'}, status=404)
        
        review.delete()
        return JsonResponse({
            'success': True, 
            'message': 'Review berhasil dihapus.'
        })
        
    except Exception as e:
        print(f"Error in delete_review: {e}")
        return JsonResponse({'success': False, 'message': 'Terjadi kesalahan server.'}, status=500)

def review_preview(request, match_id):
    try:
        event = get_object_or_404(Event, match_id=match_id)
        # FIX: Use Review.objects.filter instead of event.reviews
        reviews = Review.objects.filter(event=event).order_by('-created_at')[:3]
        
        user_has_ticket = True
        user_has_review = False  # Add this
        
        if request.user.is_authenticated:
            # user_has_ticket = Order.objects.filter(
            #     user=request.user, 
            #     ticket__event=event, 
            #     status='confirmed'
            # ).exists()
            # Check if user already has a review
            user_has_review = Review.objects.filter(
                user=request.user, 
                event=event
            ).exists()
            
        return render(request, 'review/review_preview.html', {
            'event': event, 
            'reviews': reviews, 
            'user_has_ticket': user_has_ticket,
            'user_has_review': user_has_review  # Add this
        })
        
    except Exception as e:
        print(f"Error in review_preview: {e}")
        raise Http404("Event tidak ditemukan")

def show_reviews(request, match_id):
    try:
        print(f"Accessing show_reviews with match_id: {match_id}")
        event = get_object_or_404(Event, match_id=match_id)
        print(f"Found event: {event}")
        
        reviews = Review.objects.filter(event=event).order_by('-created_at')
        
        user_has_ticket = False
        user_has_review = False 
        
        if request.user.is_authenticated:
            user_has_ticket = Order.objects.filter(
                user=request.user, 
                ticket__event=event, 
                status='confirmed'
            ).exists()
            # Check if user already has a review
            user_has_review = Review.objects.filter(
                user=request.user, 
                event=event
            ).exists()
            
        return render(request, "review/review_detail.html", {
            'event': event, 
            'reviews': reviews, 
            'user_has_ticket': user_has_ticket,
            'user_has_review': user_has_review
        })
        
    except Exception as e:
        print(f"Error in show_reviews: {e}")
        raise Http404("Event tidak ditemukan")

@login_required(login_url='/login/')
def filter_reviews(request, match_id):
    try:
        event = get_object_or_404(Event, match_id=match_id)
        filter_type = request.GET.get("type", "all")
        
        if filter_type == "my":
            reviews = Review.objects.filter(event=event, user=request.user).order_by("-created_at")
        else:
            reviews = Review.objects.filter(event=event).order_by("-created_at")
            
        html = render_to_string("review/partials/review_list.html", {
            "reviews": reviews, 
            "user": request.user,
            "event": event
        }, request=request)
        
        return JsonResponse({"html": html})
        
    except Exception as e:
        print(f"Error in filter_reviews: {e}")
        return JsonResponse({"html": "<p>Error loading reviews</p>"}, status=500)