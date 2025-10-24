from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from review.models import Review
from django.db.models import Avg, Count

from .utils import admin_required, is_admin

import event
from event.models import Event
from event.forms import EventForm

def show_event_main(request):
    event_list = Event.objects.all()

    raw_categories = Event.objects.values_list('category', flat=True)
    categories = sorted(set(raw_categories))
    filter_category = request.GET.get('category', '').lower()
    if filter_category and filter_category != 'all':
        event_list = event_list.filter(category=filter_category)

    is_user_admin = request.user.is_authenticated and is_admin(request.user)

    context = {
        'event_list': event_list,
        'filter_category': filter_category,
        'categories': categories,
        'is_admin': is_user_admin,
    }
    return render(request, 'event_main.html', context)

@admin_required
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
    review_form = None #TODO: ADD REVIEW FORM
    context = {
        'event': event,
        'reviews': reviews,
        'user_review': user_review,
        'review_form': review_form,
        'is_admin': request.user.is_authenticated and hasattr(request.user,
                                                              'profile') and request.user.profile.role == 'Admin',
    }
    return render(request, 'event_detail.html', context)

@admin_required
def edit_event(request, id):
    event = get_object_or_404(Event, pk=id)
    form = EventForm(request.POST or None, instance=event)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('event:show_event_main')
    context = {'form': form}

    return render(request, 'edit_event.html', context)

@admin_required
def delete_event(request, id):
    event = get_object_or_404(Event, pk=id)
    event.delete()
    return redirect('event:show_event_main')

@admin_required
@csrf_exempt
def add_event_ajax(request):
    name = strip_tags(request.POST.get('name'))
    category = request.POST.get('category')
    date = request.POST.get('date')
    venue = strip_tags(request.POST.get('venue'))
    capacity = request.POST.get('capacity')
    home_team = strip_tags(request.POST.get('home_team'))
    away_team = strip_tags(request.POST.get('away_team'))
    description = strip_tags(request.POST.get('description'))
    poster = request.POST.get('poster')

    new_event = Event(
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

    return HttpResponse(b"CREATED", status=201)


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
            'date': event.date.isoformat() if event.date else None,  # Convert datetime to string
            'capacity': event.capacity,
            'category': event.category,
        }
        for event in event_list
    ]

    return JsonResponse(data, safe=False)