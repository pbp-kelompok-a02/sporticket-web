from django.test import TestCase, Client
from .models import Ticket
from event.models import Event
from django.test import LiveServerTestCase
from django.contrib.auth.models import User
from datetime import date

class MainTest(TestCase):
    def test_main_url_is_exist(self):
        response = Client().get('')
        self.assertEqual(response.status_code, 200)

    def test_main_using_main_template(self):
        response = Client().get('')
        self.assertTemplateUsed(response, 'tickets.html')

    def test_nonexistent_page(self):
        response = Client().get('/burhan_always_exists/')
        self.assertEqual(response.status_code, 404)

    def test_news_creation(self):
        event = Event.objects.create(
            nama = 'Olim UI',
            home_team = 'Fasilkom',
            away_team = 'FK',
            description = 'Fasilkom juara',
            # poster = 
            venue = 'SOR',
            date = date(2025, 10, 23),
            capacity = 500
        )

        ticket = Ticket.objects.create(
            event = event,
            category = "VIP",
            price = 5,
            stock = 150
        )

        self.assertEqual(ticket.event, event)
        self.assertEqual(ticket.category, "VIP")
        self.assertEqual(ticket.price, 5)
        self.assertEqual(ticket.stock, 150)
        
    def test_increase_stock(self):
        event = Event.objects.create(
            nama = 'Olim UI',
            home_team = 'Fasilkom',
            away_team = 'FK',
            description = 'Fasilkom juara',
            # poster = 
            venue = 'SOR',
            date = date(2025, 10, 23),
            capacity = 500
        )

        ticket = Ticket.objects.create(
            event = event,
            category = "VIP",
            price = 5,
            stock = 150
        )

        ticket.increase_stock(5)
        self.assertEqual(ticket.stock, 155)
    
    def test_decrease_stock(self):
        event = Event.objects.create(
            nama = 'Olim UI',
            home_team = 'Fasilkom',
            away_team = 'FK',
            description = 'Fasilkom juara',
            # poster = 
            venue = 'SOR',
            date = date(2025, 10, 23),
            capacity = 500
        )

        ticket = Ticket.objects.create(
            event = event,
            category = "VIP",
            price = 5,
            stock = 150
        )

        ticket.decrease_stock(5)
        self.assertEqual(ticket.stock, 145)

    def test_reserve(self):
        event = Event.objects.create(
            nama = 'Olim UI',
            home_team = 'Fasilkom',
            away_team = 'FK',
            description = 'Fasilkom juara',
            # poster = 
            venue = 'SOR',
            date = date(2025, 10, 23),
            capacity = 500
        )

        ticket = Ticket.objects.create(
            event = event,
            category = "VIP",
            price = 5,
            stock = 150
        )

        ticket.reserve(5)
        self.assertEqual(ticket.stock, 145)

