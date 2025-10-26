from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from review.models import Review
from django.db.models import Avg, Count
from event.models import Event
from event.forms import EventForm

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

    reviews = Review.objects.filter(event=event).aggregate(avg_rating=Avg('rating'),
                                                           total_reviews=Count('id'))
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(event=event, user=request.user).first()
    context = {
        'event': event,
        'reviews': reviews,
        'user_review': user_review,
        'is_admin': request.user.is_superuser,
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