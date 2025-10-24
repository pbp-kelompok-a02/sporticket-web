from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from event.models import Event
from event.forms import EventForm
from django.utils import timezone
from event import views


# 1. MODEL TESTS
class EventModelTest(TestCase):
    def test_event_creation(self):
        """Event creation test"""
        event = Event.objects.create(
            match_id="V20",
            name="Test Event",
            home_team="Team A",
            away_team="Team B",
            venue="Test Venue",
            date=timezone.now(),
            category="football"
        )
        self.assertEqual(event.name, "Test Event")
        self.assertEqual(event.match_id, "V20")

    def test_string_representation(self):
        """Test __str__ method"""
        event = Event.objects.create(
            match_id="V21",
            name="Test Event",
            home_team="Team A",
            away_team="Team B",
            venue="Test Venue",
            date=timezone.now(),
            category="football"
        )
        expected = "Test Event — Team A vs Team B @ Test Venue"
        self.assertEqual(str(event), expected)


# 2. FORM TESTS
class EventFormTest(TestCase):
    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {
            'name': 'Test Event',
            'category': 'football',
            'date': timezone.now(),
            'venue': 'Test Stadium',
            'capacity': 1000,
            'home_team': 'Home Team',
            'away_team': 'Away Team',
            'description': 'Test Description',
            'poster': 'test.jpg',
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        """Test form with missing name"""
        form_data = {
            'name': '',
            'category': 'football',
            'date': timezone.now(),
            'venue': 'Test Stadium',
            'capacity': 1000,
            'home_team': 'Home Team',
            'away_team': 'Away Team',
            'description': 'Test Description',
            'poster': 'test.jpg',
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())


# 3. VIEW TESTS
class EventViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create regular user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Create admin user (superuser)
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            password='adminpass123',
            email='admin@example.com'
        )

        self.event = Event.objects.create(
            match_id="V20",
            name="Test Event",
            home_team="Team A",
            away_team="Team B",
            venue="Test Venue",
            date=timezone.now(),
            category="football",
            capacity=1000,
            description="Test description"
        )


    def test_show_event_main(self):
        """Test main event page loads"""
        response = self.client.get(reverse('event:show_event_main'))
        self.assertEqual(response.status_code, 200)

    def test_show_event_main_with_filter(self):
        """Test main event page with filter"""
        response = self.client.get(reverse('event:show_event_main') + '?category=football')
        self.assertEqual(response.status_code, 200)

    def test_event_detail(self):
        """Test event detail page loads"""
        response = self.client.get(reverse('event:event_detail', args=[self.event.match_id]))
        self.assertEqual(response.status_code, 200)

    def test_event_detail_404(self):
        """Test event detail with invalid match_id"""
        response = self.client.get(reverse('event:event_detail', args=['nonexistent']))
        self.assertEqual(response.status_code, 404)

    def test_show_json(self):
        """Test JSON endpoint returns data"""
        response = self.client.get(reverse('event:show_json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')


# 4. URL TESTS

class URLTests(TestCase):
    def test_show_event_main_url_resolves(self):
        """Test show_event_main URL resolves to correct view"""
        url = reverse('event:show_event_main')
        self.assertEqual(resolve(url).func, views.show_event_main)

    def test_event_detail_url_resolves(self):
        """Test event_detail URL resolves to correct view"""
        url = reverse('event:event_detail', args=['V20'])
        self.assertEqual(resolve(url).func, views.event_detail)

    def test_show_json_url_resolves(self):
        """Test show_json URL resolves to correct view"""
        url = reverse('event:show_json')
        self.assertEqual(resolve(url).func, views.show_json)

    def test_add_event_url_resolves(self):
        """Test add_event URL resolves to correct view"""
        url = reverse('event:add_event')
        self.assertEqual(resolve(url).func, views.add_event)

    def test_add_event_ajax_url_resolves(self):
        """Test add_event_ajax URL resolves to correct view"""
        url = reverse('event:add_event_ajax')
        self.assertEqual(resolve(url).func, views.add_event_ajax)

    def test_edit_event_url_resolves(self):
        """Test edit_event URL resolves to correct view"""
        url = reverse('event:edit_event', args=['V20'])
        self.assertEqual(resolve(url).func, views.edit_event)

    def test_delete_event_url_resolves(self):
        """Test delete_event URL resolves to correct view"""
        url = reverse('event:delete_event', args=['V20'])
        self.assertEqual(resolve(url).func, views.delete_event)