import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from order.models import Order

User = get_user_model()

class Command(BaseCommand):
    help = "Load dummy orders from a CSV file in initial_dataset/ (default: football.csv)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='football.csv',
            help='CSV file name inside initial_dataset/ (e.g., football.csv, nba.csv)'
        )

    def handle(self, *args, **options):
        filename = options['file']
        filepath = os.path.join("initial_dataset", filename)

        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f"File {filepath} not found!"))
            return

        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                name="dummy",
                email="dummy@example.com",
                password="dummy123"
            )

        with open(filepath, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Order.objects.create(
                    user=user,
                    match_id=row["match_id"],
                    kategori=row["ticket_category"],
                    harga=row["ticket_price"],
                    quantity=1,
                    status=Order.STATUS_PENDING,
                )

        self.stdout.write(self.style.SUCCESS(f"✅ Dummy orders from {filename} loaded successfully!"))
