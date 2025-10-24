from django.shortcuts import render, redirect, get_object_or_404
from ticket.models import Ticket
from event.models import Event
from ticket.forms import TicketForm
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.contrib.auth.decorators import user_passes_test
from django.template.loader import render_to_string

@login_required
def show_tickets(request):
    ticket_list = Ticket.objects.all()
    first_ticket = ticket_list.first()
    event_list = Event.objects.all()

    context = {
        'ticket_list': ticket_list,
        'first_ticket': first_ticket,
        'event_list': event_list
    }
    return render(request, "tickets.html", context)

@login_required
def create_ticket(request):
    form = TicketForm(request.POST or None)

    if form.is_valid() and request.method == "POST":
        form.save()
        return redirect('ticket:show_tickets')

    context = {'form': form}
    return render(request, "create_ticket.html", context)

@login_required
@csrf_exempt
def edit_ticket(request, id):
    ticket = get_object_or_404(Ticket, pk=id)
    form = TicketForm(request.POST or None, instance=ticket)

    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('ticket:show_tickets')
    
    context = {'form': form, 'ticket': ticket}
    return render(request, "edit_ticket.html", context)

@login_required
@csrf_exempt
@require_POST
def delete_ticket(request, id):
    ticket = get_object_or_404(Ticket, pk=id)
    ticket.delete()
    return HttpResponse(b"DELETED", status=201)

def show_json(request):
    ticket_list = Ticket.objects.all().order_by('-id')  # urut dari terbaru
    data = [
        {
            'id': ticket.id,
            'event_id': ticket.event.match_id if ticket.event else None,
            'category': ticket.event.category if ticket.event else None,
            'price': float(ticket.price),
            'stock': ticket.stock,
            'html': render_to_string('card_ticket.html', {'ticket': ticket, 'user': request.user}, request=request)
        }
        for ticket in ticket_list
    ]
    return JsonResponse(data, safe=False)

@csrf_exempt
def delete_ticket_ajax(request, id):
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, pk=id)
        ticket.delete()
        return JsonResponse({'deleted': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def add_ticket_ajax(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        event = Event.objects.get(match_id=data['event_id'])
        ticket = Ticket.objects.create(
            event=event,
            category=data['category'],
            price=data['price'],
            stock=data['stock']
        )
        return JsonResponse({
            'id': ticket.id,
            'event': ticket.event.match_id,
            'category': ticket.category,
            'price': float(ticket.price),
            'stock': ticket.stock
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)