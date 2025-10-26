import csv
from django.core.management.base import BaseCommand
from event.models import Event
from datetime import datetime
from django.utils import timezone

class Command(BaseCommand):
    help = 'Import events from CSV'

    def handle(self, *args, **kwargs):
        with open('initial_dataset/event_dataset.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                date_str = f"{row['date']} {row['time']}"
                date_obj = datetime.strptime(date_str, "%Y-%m-%d %I:%M%p")
                date_obj = timezone.make_aware(date_obj)
                category = row['name'].split()[0].lower()
                Event.objects.update_or_create(
                    match_id=row['match_id'],
                    defaults={
                        'name': row['name'],
                        'home_team': row['home_team'],
                        'away_team': row['away_team'],
                        'description': row['description'],
                        'venue': row['venue'],
                        'date': date_obj,
                        'capacity': row['capacity'],
                        'category': category,
                        'poster' : row['poster'],
                    }
                )
        self.stdout.write(self.style.SUCCESS('Events imported!'))