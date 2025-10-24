from django.urls import path
from ticket.views import *

app_name = 'ticket'

urlpatterns = [
	path('', show_tickets, name='show_tickets'),
    path('create-ticket/', create_ticket, name='create_ticket'),
    path('tickets/<str:id>/edit', edit_ticket, name='edit_ticket'),
    path('tickets/<str:id>/delete', delete_ticket_ajax, name='delete_ticket_ajax'),
    path('json/', show_json, name='show_json'),
    path('add-ticket/', add_ticket_ajax, name='add_ticket_ajax'),
]