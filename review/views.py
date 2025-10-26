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
    # 1. Dapatkan event dulu. Jika tidak ada, biarkan 404.
    event = get_object_or_404(Event, match_id=match_id)
    
    try:
        # 2. Cek tiket
        if not Order.objects.filter(user=request.user, ticket__event=event, status='confirmed').exists():
            return JsonResponse({'success': False, 'message': 'Anda belum membeli tiket untuk event ini.'}, status=403)
        
        # 3. Validasi data
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
        
        review, created = Review.objects.update_or_create(
            user=request.user,
            event=event,
            defaults={'rating': rating, 'komentar': komentar}
        )
        
        try:
            html = render_to_string('review/card_review.html', {
                'review': review, 
                'user': request.user,
                'event': event
            }, request=request)
        except (TemplateDoesNotExist, Exception) as e:
            print(f"Template rendering error: {e}")
            # Fallback jika template error (seperti 'account:profile' tidak ada)
            html = f"<div>Review by {review.user.username}: {review.rating}/5 - {review.komentar}</div>"
        
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
    # 1. Dapatkan review dulu.
    review = get_object_or_404(Review, id=review_id)
    
    try:
        if review.event.match_id != match_id:
            return JsonResponse({'success': False, 'message': 'Review tidak ditemukan untuk event ini.'}, status=404)
        
        if review.user != request.user:
            return JsonResponse({'success': False, 'message': 'Anda tidak memiliki izin untuk mengedit review ini.'}, status=403)
        
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
        
        review.rating = rating
        review.komentar = komentar
        review.save()
        
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
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    try:
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
    event = get_object_or_404(Event, match_id=match_id)
    
    try:
        reviews = Review.objects.filter(event=event).select_related('user', 'user__profile').order_by('-created_at')
        
        user_has_ticket = False
        user_has_review = False
        
        if request.user.is_authenticated:
            user_has_ticket = request.user.orders.filter(
                ticket__event=event,
                status='confirmed'
            ).exists()
            
            user_has_review = Review.objects.filter(
                user=request.user,
                event=event
            ).exists()
            
            print(f"DEBUG - User: {request.user.username}")
            print(f"DEBUG - Has ticket: {user_has_ticket}")
            print(f"DEBUG - Has review: {user_has_review}")
            print(f"DEBUG - Reviews count: {reviews.count()}")

        return render(request, 'review/review_preview.html', {
            'event': event, 
            'reviews': reviews[:3],
            'user_has_ticket': user_has_ticket,
            'user_has_review': user_has_review,
            'reviews_count_all': reviews.count()
        })
        
    except Exception as e:
        print(f"Error in review_preview: {e}")
        raise Http404("Terjadi error saat memuat review")

def show_reviews(request, match_id):
    event = get_object_or_404(Event, match_id=match_id)
    
    try:
        reviews = Review.objects.filter(event=event).select_related('user', 'user__profile').order_by('-created_at')
        
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
            
        return render(request, "review/review_detail.html", {
            'event': event, 
            'reviews': reviews, 
            'user_has_ticket': user_has_ticket,
            'user_has_review': user_has_review,
        })
        
    except Exception as e:
        print(f"Error in show_reviews: {e}")
        raise Http404("Terjadi error saat memuat review")

@login_required(login_url='/login/')
def filter_reviews(request, match_id):
    # 1. Dapatkan event.
    event = get_object_or_404(Event, match_id=match_id)
    
    try:
        filter_type = request.GET.get("type", "all")
        
        if filter_type == "my":
            reviews = Review.objects.filter(event=event, user=request.user).select_related('user', 'user__profile').order_by("-created_at")
        else:
            reviews = Review.objects.filter(event=event).select_related('user', 'user__profile').order_by("-created_at")
            
        # 2. Render HTML
        try:
            html = render_to_string("review/partials/review_list.html", {
                "reviews": reviews, 
                "user": request.user,
                "event": event
            }, request=request)
        except Exception as e:
            print(f"Template rendering error in filter: {e}")
            html = f"<p>Error rendering review list: {e}</p>"
        
        return JsonResponse({"html": html})
        
    except Exception as e:
        print(f"Error in filter_reviews: {e}")
        return JsonResponse({"html": "<p>Error loading reviews</p>"}, status=500)