from django.forms import ModelForm
from ticket.models import Ticket
from django.utils.html import strip_tags

class TicketForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ["category", "price", "stock"]