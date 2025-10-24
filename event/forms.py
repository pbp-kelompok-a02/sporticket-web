from django.forms import ModelForm
from event.models import Event
from django.utils.html import strip_tags

class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = [
            'name',
            'category',
            'date',
            'venue',
            'capacity',
            'home_team',
            'away_team',
            'description',
            'poster',
        ]

    def clean_description(self):
        description = self.cleaned_data['description']
        return strip_tags(description)