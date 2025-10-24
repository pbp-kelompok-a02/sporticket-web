import csv
from django.core.management.base import BaseCommand
from ticket.models import Ticket
from event.models import Event

class Command(BaseCommand):
    help = 'Import tickets from CSV'

    def handle(self, *args, **kwargs):
        import os
        dataset_dir = 'initial_dataset'
        csv_files = [
            'football.csv',
            'badminton.csv',
            'nba.csv',
            'tennis.csv',
            'volleyball.csv',
        ]
        total_imported = 0
        total_skipped = 0
        for csv_name in csv_files:
            path = os.path.join(dataset_dir, csv_name)
            if not os.path.exists(path):
                self.stdout.write(self.style.WARNING(f"File not found: {path}"))
                continue
            with open(path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    match_id = row['match_id']
                    try:
                        event = Event.objects.get(match_id=match_id)
                    except Event.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Event with match_id '{match_id}' not found for {csv_name}, skipping ticket."))
                        total_skipped += 1
                        continue
                    category = row['ticket_category'].strip().upper()
                    if category == 'REGULAR':
                        category = Ticket.CATEGORY_REGULAR
                    elif category == 'VIP':
                        category = Ticket.CATEGORY_VIP
                    else:
                        self.stdout.write(self.style.WARNING(f"Unknown category '{row['ticket_category']}' for match_id '{match_id}' in {csv_name}, skipping ticket."))
                        total_skipped += 1
                        continue
                    Ticket.objects.update_or_create(
                        event=event,
                        category=category,
                        defaults={
                            'price': int(row['ticket_price']),
                            'stock': int(row['ticket_stock']),
                        }
                    )
                    total_imported += 1
        self.stdout.write(self.style.SUCCESS(f'Tickets imported! Imported: {total_imported}, Skipped: {total_skipped}'))