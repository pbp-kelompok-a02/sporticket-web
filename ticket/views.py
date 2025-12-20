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
import requests
from uuid import UUID

@login_required
def show_tickets(request, match_id):
    event = get_object_or_404(Event, match_id=match_id)
    ticket_list = Ticket.objects.filter(event=event).order_by('-id')
    first_ticket = ticket_list.first()
    event_list = Event.objects.all()

    context = {
        'event': event,
        'ticket_list': ticket_list,
        'first_ticket': first_ticket,
        'event_list': event_list
    }
    return render(request, "tickets.html", context)

@login_required
def create_ticket(request, match_id):
    form = TicketForm(request.POST or None)
    event = get_object_or_404(Event, match_id=match_id)

    if form.is_valid() and request.method == "POST":
        ticket = form.save(commit=False)
        ticket.event = event
        ticket.save()
        return redirect('ticket:show_tickets', match_id=event.match_id)

    context = {
        'form': form,
        'event': event
    }
    return render(request, "create_ticket.html", context)

@login_required
@csrf_exempt
def edit_ticket(request, id):
    ticket = get_object_or_404(Ticket, pk=id)
    event = ticket.event
    form = TicketForm(request.POST or None, instance=ticket)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                html = render_to_string("card_ticket.html", {"ticket": ticket}, request=request)
                return JsonResponse({"updated": True, "html": html})
            return redirect("ticket:show_tickets", match_id=event.match_id)
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"updated": False, "error": "Invalid data"})

    # === GET request for AJAX (show form in modal) ===
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "edit_ticket.html",
            {"form": form, "ticket": ticket, "event": event},
            request=request,
        )
        return HttpResponse(html)
    else:
        # fallback jika dibuka langsung
        return render(request, "edit_ticket.html", {"form": form, "ticket": ticket, "event": event})

@login_required
@csrf_exempt
@require_POST
def delete_ticket(request, id):
    ticket = get_object_or_404(Ticket, pk=id)
    ticket.delete()
    return HttpResponse(b"DELETED", status=201)

def show_json(request, match_id=None):
    if match_id:
        event = get_object_or_404(Event, match_id=match_id)
        ticket_list = Ticket.objects.filter(event=event).order_by('-id')
    else:
        ticket_list = Ticket.objects.all().order_by('-id')
    data = [
        {
            'id': ticket.id,
            'event_id': ticket.event.match_id if ticket.event else None,
            'category': ticket.category,
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
        try:
            data = json.loads(request.body)
            event = Event.objects.get(match_id=data['event_id'])
            ticket = Ticket.objects.create(
                event=event,
                category=data['category'],
                price=data['price'],
                stock=data['stock']
            )
            html = render_to_string('card_ticket.html', {'ticket': ticket, 'user': request.user}, request=request)
            html = f'<div id="ticket-{ticket.id}">{html}</div>'
            return JsonResponse({
                'id': ticket.id,
                'html': html
            }, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt  
@login_required
@require_POST
def edit_ticket_ajax(request, id):
    try:
        ticket = get_object_or_404(Ticket, pk=id)
        data = json.loads(request.body)
        
        ticket.category = data.get('category', ticket.category)
        ticket.price = data.get('price', ticket.price)
        ticket.stock = data.get('stock', ticket.stock)
        ticket.save()

        html = render_to_string('card_ticket.html', {'ticket': ticket, 'user': request.user}, request=request)
        # bungkus dengan id wrapper agar mudah replace
        html = f'<div id="ticket-{ticket.id}">{html}</div>'

        return JsonResponse({'updated': True, 'html': html})
    except Exception as e:
        return JsonResponse({'updated': False, 'error': str(e)}, status=400)
    
@csrf_exempt
def create_ticket_flutter(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        event_id = data.get("event_id")
        category = data.get("category")
        price = data.get("price")
        stock = data.get("stock")
        
        event= get_object_or_404(Event, match_id=event_id)
        
        new_ticket = Ticket(
            event=event,
            category=category,
            price=price,
            stock=stock,
        )
        new_ticket.save()
        
        return JsonResponse({"status": "success"}, status=200)
    else:
        return JsonResponse({"status": "error"}, status=401)
    
@csrf_exempt
def edit_ticket_flutter(request, id):
    if request.method == 'POST':
        ticket = Ticket.objects.get(pk=id)
        data = json.loads(request.body)

        ticket.category = data.get("category", ticket.category)
        ticket.price = data.get("price", ticket.price)
        ticket.stock = data.get("stock", ticket.stock)

        ticket.save()
        
        return JsonResponse({"status": "success"}, status=200)
    else:
        return JsonResponse({"status": "error"}, status=401)
    
@csrf_exempt
def delete_ticket_flutter(request, id):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        UUID(id)  
    except ValueError:
        return JsonResponse({"error": "Invalid UUID"}, status=400)

    try:
        ticket = Ticket.objects.get(pk=id)
        ticket.delete()
        return JsonResponse({"status": "success"}, status=200)
    except Ticket.DoesNotExist:
        return JsonResponse({"error": "Ticket not found"}, status=404)