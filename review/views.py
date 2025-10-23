from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from .models import Review
from .forms import ReviewForm
from event.models import Event
from order.models import Order

# Create your views here.
@login_required
@require_POST
def add_review(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not Order.objects.filter(user=request.user, ticket__event=event, status='confirmed').exists():
        return JsonResponse({'success': False, 'message': 'Anda belum membeli tiket untuk event ini.'}, status=403)

    rating = request.POST.get('rating')
    komentar = request.POST.get('komentar', '')

    review, created = Review.objects.update_or_create(
        user=request.user,
        event=event,
        defaults={'rating': rating, 'komentar': komentar}
    )

    html = render_to_string('review/card_review.html', {'review': review}, request=request)
    return JsonResponse({'success': True, 'html': html, 'created': created})

@login_required
@require_POST
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    if review.user != request.user:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    review.rating = request.POST.get('rating')
    review.komentar = request.POST.get('komentar', '')
    review.save()

    html = render_to_string('review/card_review.html', {'review': review}, request=request)
    return JsonResponse({'success': True, 'html': html, 'review_id': review.id})

@login_required
@require_POST
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return JsonResponse({'success': True, 'message': 'Review is succesfully deleted.'})

def review_preview(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    reviews = event.reviews.order_by('-created_at')[:3]

    user_has_ticket = False
    if request.user.is_authenticated:
        user_has_ticket = Order.objects.filter(
            user=request.user,
            tiket__event=event,
            status='confirmed'
        ).exists()

    context = {
        'event': event,
        'reviews': reviews,
        'user_has_ticket': user_has_ticket
    }

    return render(request, 'review/review_preview.html', context)

def show_reviews(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    reviews = event.reviews.order_by('created_at')

    context = {
        'event': event,
        'reviews': reviews
    }
    print(">>> event", event)
    print(">>> reviews count", reviews.count())
    response = render(request, "review/review_detail.html", context)
    print("Render berhasil:", response.status_code if hasattr(response, 'status_code') else 'tidak ada status')
    return response

@login_required
def filter_reviews(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    filter_type = request.GET.get("type", "all")

    if filter_type == "my":
        reviews = Review.objects.filter(event=event, user=request.user).order_by("-created_at")
    else:
        reviews = Review.objects.filter(event=event).order_by("-created_at")

    html = render_to_string(
        "review/partials/review_list.html",
        {"reviews": reviews, "user": request.user},
        request=request,
    )

    return JsonResponse({"html": html})

from django.http import JsonResponse

