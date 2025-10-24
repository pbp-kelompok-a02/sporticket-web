from django.test import TestCase, Client
from unicodedata import category

from .models import Event


# Create your tests here.
class MainTest(TestCase):
    def test_main_url_is_exist(self):
        response = self.client.get('events/')
        self.assertEqual(response.status_code, 200)

    def test_main_using_main_template(self):
        response = Client().get('')
        self.assertTemplateUsed(response, 'main.html')

    def test_nonexistent_page(self):
        response = Client().get('/randomlink/')
        self.assertEqual(response.status_code, 404)

    def test_event_creation(self):
        event = Event.objects.create(
            name = 'custom name 2',
            home_team = 'home team 1',
            away_team = 'away team 1',
            description = 'insert description lorem ipsum',
            venue = 'template venue',
            date = '2020-09-22',
            capacity = 727,
            category = 'football'
        )
        self.assertEqual(event.name, 'custom name 2')
        self.assertEqual(event.home_team, 'home team 1')
        self.assertEqual(event.away_team, 'away team 1')
        self.assertEqual(event.description, 'insert description lorem ipsum')
        self.assertEqual(event.venue, 'template venue')
        self.assertEqual(event.date, '2020-09-22')
        self.assertEqual(event.capacity, 727)
        self.assertEqual(event.category, 'football')
