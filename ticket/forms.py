from django.forms import ModelForm
from ticket.models import Ticket
from django.utils.html import strip_tags

class TicketForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ["event", "category", "price", "stock"]

    def clean_title(self):
        event = self.cleaned_data["event"]
        return strip_tags(event)