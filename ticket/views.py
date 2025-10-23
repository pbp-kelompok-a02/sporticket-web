from django.shortcuts import render, redirect, get_object_or_404
from ticket.models import Ticket
from ticket.forms import TicketForm
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and user.role == 'Admin'

# @user_passes_test(is_admin)
# @login_required
def show_tickets(request):
    ticket_list = Ticket.objects.all()

    context = {
        'ticket_list': ticket_list,
    }
    return render(request, "tickets.html", context)

# @user_passes_test(is_admin)
# @login_required
def create_ticket(request):
    form = TicketForm(request.POST or None)

    if form.is_valid() and request.method == "POST":
        form.save()
        return redirect('ticket:show_tickets')

    context = {'form': form}
    return render(request, "create_ticket.html", context)

# @user_passes_test(is_admin)
# @login_required
def ticket_detail(request, id):
    ticket = get_object_or_404(Ticket, pk=id)

    context = {'ticket': ticket}
    return render(request, "ticket_detail.html", context)

# @user_passes_test(is_admin)
# @login_required
# @csrf_exempt
def edit_ticket(request, id):
    ticket = get_object_or_404(Ticket, pk=id)
    form = TicketForm(request.POST or None, instance=ticket)

    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('ticket:show_tickets')
    
    context = {'form': form}
    return render(request, "edit_ticket.html", context)

# @user_passes_test(is_admin)
# @login_required
# @csrf_exempt
# @require_POST
def delete_ticket(request, id):
    ticket = get_object_or_404(Ticket, pk=id)
    ticket.delete()
    return HttpResponse(b"DELETED", status=201)

def show_json(request):
    ticket_list = Ticket.objects.all()
    data = [
        {
            'id': str(ticket.id),
            'category': ticket.category,
            'price': ticket.price,
            'stock': ticket.stock,
        }
        for ticket in ticket_list
    ]

    return JsonResponse(data, safe=False)