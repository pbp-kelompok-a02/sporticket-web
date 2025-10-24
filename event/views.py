from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import strip_tags

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


    context = {
        'event_list': event_list,
        'filter_category': filter_category,
        'categories': categories,
    }
    return render(request, 'event_main.html', context)


def add_event(request):
    form = EventForm(request.POST or None)

    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('event:show_event_main')

    context = {'form': form}
    return render(request, 'add_event.html', context)

def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    context = {'event': event}

    return render(request, 'event_detail.html', context)

def edit_event(request, id):
    event = get_object_or_404(Event, pk=id)
    form = EventForm(request.POST or None, instance=event)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('event:show_event_main')
    context = {'form': form}

    return render(request, 'edit_event.html', context)

def delete_event(request, id):
    event = get_object_or_404(Event, pk=id)
    event.delete()
    return redirect('event:show_event_main')

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
            'id': str(event.id),
            'name': event.name,
            'home_team': event.home_team,
            'away_team': event.away_team,
            'description': event.description,
            'poster': event.poster,
            'venue': event.venue,
            'date': event.date,
            'capacity': event.capacity,
            'category': event.category,

        }
        for event in event_list
    ]

    return JsonResponse(data, safe=False)
