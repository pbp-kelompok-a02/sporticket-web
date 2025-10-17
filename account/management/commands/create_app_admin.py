from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()


class Command(BaseCommand):
    # Membuat admin aplikasi tunggal (bukan superuser).
    # Menggunakan variabel env APP_ADMIN_EMAIL dan APP_ADMIN_PASSWORD
    # atau opsi --email/--password (python manage.py create_app_admin --email ... --password ...)

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Admin email (overrides env var)')
        parser.add_argument('--password', type=str, help='Admin password (overrides env var)')

    def handle(self, *args, **options):
        email = options.get('email') or os.getenv('APP_ADMIN_EMAIL')
        password = options.get('password') or os.getenv('APP_ADMIN_PASSWORD')

        if not email or not password:
            self.stdout.write(self.style.ERROR('Please provide admin email and password via --email/--password or APP_ADMIN_EMAIL/APP_ADMIN_PASSWORD environment variables'))
            return

        if User.objects.filter(email__iexact=email).exists():
            self.stdout.write(self.style.WARNING('Admin user already exists'))
            return

        User.objects.create_admin(email=email, name='App Admin', password=password)
        self.stdout.write(self.style.SUCCESS(f'Admin created: {email}'))
