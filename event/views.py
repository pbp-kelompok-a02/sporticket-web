import json

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from review.models import Review
from order.models import Order
from django.db.models import Avg, Count
from event.models import Event
from event.forms import EventForm
import requests

def is_admin(user):
    return user.is_authenticated and user.is_superuser

def show_event_main(request):
    event_list = Event.objects.all()

    raw_categories = Event.objects.values_list('category', flat=True)
    categories = sorted(set(raw_categories))
    filter_category = request.GET.get('category', '').lower()
    if filter_category and filter_category != 'all':
        event_list = event_list.filter(category=filter_category)



    context = {
        'event_list': event_list,
        'filter_category': filter_category,
        'categories': categories,
        'is_admin': request.user.is_superuser,
    }
    return render(request, 'event_main.html', context)

@user_passes_test(is_admin)
def add_event(request):
    form = EventForm(request.POST or None)

    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('event:show_event_main')

    context = {'form': form}
    return render(request, 'add_event.html', context)

def event_detail(request, match_id):
    event = get_object_or_404(Event, match_id=match_id)
    # Provide both an aggregate and a full queryset for reviews.
    # The included template `review/review_preview.html` expects `reviews` to be
    # an iterable queryset (so it can slice/loop and get correct length), while
    # other parts of this view might want aggregates.
    reviews_qs = Review.objects.filter(event=event).select_related('user', 'user__profile').order_by('-created_at')
    reviews_agg = reviews_qs.aggregate(avg_rating=Avg('rating'), total_reviews=Count('id'))

    user_review = None
    user_has_ticket = False
    user_has_review = False

    if request.user.is_authenticated:
        user_review = Review.objects.filter(event=event, user=request.user).first()
        # Check whether the user has a confirmed ticket for this event.
        try:
            # Use the user's related orders manager to avoid any potential
            # cross-app model resolution issues and to be explicit about the owner.
            user_has_ticket = request.user.orders.filter(
                ticket__event=event,
                status='confirmed'
            ).exists()
        except Exception:
            # If the Order lookup fails for any reason, default to False
            user_has_ticket = False

        user_has_review = Review.objects.filter(event=event, user=request.user).exists()

        # Debug prints to the server console to help during development
        print(f"DEBUG event_detail - User: {request.user.username}")
        print(f"DEBUG event_detail - Has ticket: {user_has_ticket}")
        print(f"DEBUG event_detail - Has review: {user_has_review}")
        print(f"DEBUG event_detail - Reviews count: {reviews_qs.count()}")

    context = {
        'event': event,
        # Expose a queryset named `reviews` so the included preview template works.
        'reviews': reviews_qs,
        # Also provide aggregates under a different name in case other logic needs it.
        'reviews_agg': reviews_agg,
        'user_review': user_review,
        'is_admin': request.user.is_superuser,
        'user_has_ticket': user_has_ticket,
        'user_has_review': user_has_review,
    }
    return render(request, 'event_detail.html', context)

@user_passes_test(is_admin)
def edit_event(request, match_id):
    event = get_object_or_404(Event, match_id=match_id)
    form = EventForm(request.POST or None, instance=event)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('event:show_event_main')
    context = {'form': form}

    return render(request, 'edit_event.html', context)

@user_passes_test(is_admin)
def delete_event(request, match_id):
    event = get_object_or_404(Event, match_id=match_id)
    event.delete()
    return redirect('event:show_event_main')


@user_passes_test(is_admin)
@csrf_exempt
def add_event_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    try:
        import json
        data = json.loads(request.body)

        name = strip_tags(data.get('name', ''))
        category = data.get('category', '').lower()
        date = data.get('date', '')
        venue = strip_tags(data.get('venue', ''))
        capacity = data.get('capacity', 0)
        home_team = strip_tags(data.get('home_team', ''))
        away_team = strip_tags(data.get('away_team', ''))
        description = strip_tags(data.get('description', ''))
        poster = data.get('poster', '')

        # Generate match_id based on category
        category_prefixes = {
            'basketball': 'N',
            'badminton': 'B',
            'football': 'F',
            'tennis': 'T',
            'volleyball': 'V'
        }

        prefix = category_prefixes.get(category, 'X')  # 'X' as fallback


        event_count = Event.objects.filter(category=category).count()
        next_number = event_count + 1
        # Generate the match_id
        match_id = f"{prefix}{next_number}"

        # Check if match_id already exists (safety check)
        while Event.objects.filter(match_id=match_id).exists():
            next_number += 1
            match_id = f"{prefix}{next_number}"

        new_event = Event(
            match_id=match_id,
            name=name,
            category=category,
            date=date,
            venue=venue,
            capacity=capacity,
            home_team=home_team,
            away_team=away_team,
            description=description,
            poster=poster,
        )
        new_event.save()

        # Return the event data in the expected format
        event_data = {
            'match_id': str(new_event.match_id),
            'name': new_event.name,
            'home_team': new_event.home_team,
            'away_team': new_event.away_team,
            'description': new_event.description,
            'poster': str(new_event.poster) if new_event.poster else None,
            'venue': new_event.venue,
            'date': new_event.date,
            'capacity': new_event.capacity,
            'category': new_event.category,
        }

        return JsonResponse({
            'success': True,
            'event': event_data,
            'message': 'Event added successfully'
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def show_json(request):
    event_list = Event.objects.all()
    data = [
        {
            'match_id': str(event.match_id),
            'name': event.name,
            'home_team': event.home_team,
            'away_team': event.away_team,
            'description': event.description,
            'poster': str(event.poster) if event.poster else None,
            'venue': event.venue,
            'date': event.date.isoformat() if event.date else None,
            'capacity': event.capacity,
            'category': event.category,
        }
        for event in event_list
    ]

    return JsonResponse(data, safe=False)


def proxy_image(request):
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)

    try:
        # Fetch image from external source
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        # Return the image with proper content type
        return HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except requests.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)


@csrf_exempt
def create_event_flutter(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = strip_tags(data.get('name', ''))
        category = data.get('category', '').lower()
        date = data.get('date', '')
        venue = strip_tags(data.get('venue', ''))
        capacity = data.get('capacity', 0)
        home_team = strip_tags(data.get('home_team', ''))
        away_team = strip_tags(data.get('away_team', ''))
        description = strip_tags(data.get('description', ''))
        poster = data.get('poster', '')

        # Generate match_id based on category
        category_prefixes = {
            'basketball': 'N',
            'badminton': 'B',
            'football': 'F',
            'tennis': 'T',
            'volleyball': 'V'
        }

        prefix = category_prefixes.get(category, 'X')  # 'X' as fallback

        event_count = Event.objects.filter(category=category).count()
        next_number = event_count + 1
        # Generate the match_id
        match_id = f"{prefix}{next_number}"

        # Check if match_id already exists (safety check)
        while Event.objects.filter(match_id=match_id).exists():
            next_number += 1
            match_id = f"{prefix}{next_number}"

        new_event = Event(
            match_id=match_id,
            name=name,
            category=category,
            date=date,
            venue=venue,
            capacity=capacity,
            home_team=home_team,
            away_team=away_team,
            description=description,
            poster=poster,
        )
        new_event.save()

        return JsonResponse({"status": "success"}, status=200)
    else:
        return JsonResponse({"status": "error"}, status=401)


@csrf_exempt
def update_event_flutter(request, match_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Get the existing event
            try:
                event = Event.objects.get(match_id=match_id)
            except Event.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Event not found"}, status=404)


            event.name = strip_tags(data.get('name', event.name))

            new_date = data.get('date')
            if new_date:
                event.date = new_date

            event.venue = strip_tags(data.get('venue', event.venue))


            new_capacity = data.get('capacity')
            if new_capacity:
                event.capacity = new_capacity

            event.home_team = strip_tags(data.get('home_team', event.home_team))
            event.away_team = strip_tags(data.get('away_team', event.away_team))
            event.description = strip_tags(data.get('description', event.description))
            event.poster = data.get('poster', event.poster)

            event.save()

            return JsonResponse({
                "status": "success",
                "message": "Event updated successfully"
            }, status=200)

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)

    else:
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)


@csrf_exempt
def delete_event_flutter(request, match_id):
    if request.method == 'POST':
        try:
            event = Event.objects.get(match_id=match_id)

            # Check if event has any tickets that have been ordered
            from ticket.models import Ticket
            from order.models import Order

            # Get all tickets for this event
            event_tickets = Ticket.objects.filter(event=event)

            # Check if ticket has order
            has_orders = Order.objects.filter(ticket__in=event_tickets).exists()

            if has_orders:
                return JsonResponse({
                    "status": "error",
                    "message": "Cannot delete event. Tickets have already been purchased for this event."
                }, status=200)

            # If no orders, proceed with deletion
            event.delete()

            return JsonResponse({
                "status": "success",
                "message": "Event deleted successfully"
            }, status=200)

        except Event.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": "Event not found"
            }, status=200)
        except Exception as e:
            print(f"Error deleting event: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                "status": "error",
                "message": f"Failed to delete event: {str(e)}"
            }, status=200)
    else:
        return JsonResponse({
            "status": "error",
            "message": "Invalid method"
        }, status=200)