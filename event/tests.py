from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from event.models import Event
from event.forms import EventForm
from django.utils import timezone
from event import views
import json
from datetime import datetime, timedelta


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
        # Check if __str__ returns correct string
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

        # Create events for different categories
        self.basketball_event = Event.objects.create(
            match_id="N1",
            name="Basketball Game",
            home_team="Lakers",
            away_team="Warriors",
            venue="Arena",
            date=timezone.now(),
            category="basketball",
            capacity=2000,
            description="Basketball game"
        )

    def test_show_event_main(self):
        """Test main event page loads"""
        response = self.client.get(reverse('event:show_event_main'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('event_list', response.context)
        self.assertIn('categories', response.context)

    def test_show_event_main_with_filter(self):
        """Test main event page with filter"""
        response = self.client.get(reverse('event:show_event_main') + '?category=football')
        self.assertEqual(response.status_code, 200)
        # Check only football events are returned
        events = response.context['event_list']
        for event in events:
            self.assertEqual(event.category, 'football')

    def test_show_event_main_with_all_filter(self):
        """Test main event page with 'all' filter"""
        response = self.client.get(reverse('event:show_event_main') + '?category=all')
        self.assertEqual(response.status_code, 200)
        # Check if all events are returned
        self.assertEqual(len(response.context['event_list']), 2)

    def test_show_event_main_is_admin_context(self):
        """Test is_admin context for regular user and admin"""
        # Regular user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('event:show_event_main'))
        self.assertFalse(response.context['is_admin'])

        # Admin user
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get(reverse('event:show_event_main'))
        self.assertTrue(response.context['is_admin'])

    def test_event_detail(self):
        """Test event detail page loads"""
        response = self.client.get(reverse('event:event_detail', args=[self.event.match_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['event'], self.event)

    def test_event_detail_authenticated_user(self):
        """Test event detail for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('event:event_detail', args=[self.event.match_id]))
        self.assertEqual(response.status_code, 200)
        # Check user_review
        self.assertIn('user_review', response.context)

    def test_event_detail_404(self):
        """Test event detail with invalid match_id"""
        response = self.client.get(reverse('event:event_detail', args=['nonexistent']))
        self.assertEqual(response.status_code, 404)

    def test_show_json(self):
        """Test JSON endpoint returns data"""
        response = self.client.get(reverse('event:show_json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)  # 2 events in database

    # ADD EVENT TESTS
    def test_add_event_get_as_admin(self):
        """Test GET request to add_event as admin"""
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get(reverse('event:add_event'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_add_event_get_as_non_admin(self):
        """Test GET request to add_event as non-admin (should redirect)"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('event:add_event'))
        # Redirect to login or deny access
        self.assertNotEqual(response.status_code, 200)

    def test_add_event_post_as_admin(self):
        """Test POST request to add_event as admin"""
        self.client.login(username='adminuser', password='adminpass123')
        initial_count = Event.objects.count()
        form_data = {
            'match_id': 'F99',
            'name': 'New Event',
            'category': 'football',
            'date': timezone.now(),
            'venue': 'New Stadium',
            'capacity': 1500,
            'home_team': 'Home',
            'away_team': 'Away',
            'description': 'New Description',
        }
        response = self.client.post(reverse('event:add_event'), data=form_data)
        # Redirect after creation
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Event.objects.count(), initial_count + 1)
        self.assertTrue(Event.objects.filter(name='New Event').exists())

    # EDIT EVENT TESTS
    def test_edit_event_get_as_admin(self):
        """Test GET request to edit_event as admin"""
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get(reverse('event:edit_event', args=[self.event.match_id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_edit_event_get_as_non_admin(self):
        """Test GET request to edit_event as non-admin"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('event:edit_event', args=[self.event.match_id]))
        self.assertNotEqual(response.status_code, 200)

    def test_edit_event_post_as_admin(self):
        """Test POST request to edit_event as admin"""
        self.client.login(username='adminuser', password='adminpass123')
        form_data = {
            'match_id': self.event.match_id,
            'name': 'Updated Event Name',
            'category': 'football',
            'date': self.event.date,
            'venue': self.event.venue,
            'capacity': 2000,
            'home_team': self.event.home_team,
            'away_team': self.event.away_team,
            'description': 'Updated description',
        }
        response = self.client.post(
            reverse('event:edit_event', args=[self.event.match_id]),
            data=form_data
        )
        self.assertEqual(response.status_code, 302)
        # Refresh from database
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, 'Updated Event Name')
        self.assertEqual(self.event.capacity, 2000)

    # DELETE EVENT TESTS
    def test_delete_event_as_admin(self):
        """Test delete_event as admin"""
        self.client.login(username='adminuser', password='adminpass123')
        event_id = self.event.match_id
        response = self.client.post(reverse('event:delete_event', args=[event_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Event.objects.filter(match_id=event_id).exists())

    def test_delete_event_as_non_admin(self):
        """Test delete_event as non-admin"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('event:delete_event', args=[self.event.match_id]))
        self.assertNotEqual(response.status_code, 200)
        # Event still exists
        self.assertTrue(Event.objects.filter(match_id=self.event.match_id).exists())

    # AJAX TESTS
    def test_add_event_ajax_success(self):
        """Test successful AJAX event creation"""
        self.client.login(username='adminuser', password='adminpass123')
        event_data = {
            'name': 'AJAX Event',
            'category': 'basketball',
            'date': timezone.now().isoformat(),
            'venue': 'AJAX Venue',
            'capacity': 1000,
            'home_team': 'Home',
            'away_team': 'Away',
            'description': 'AJAX Description',
            'poster': 'poster.jpg'
        }
        response = self.client.post(
            reverse('event:add_event_ajax'),
            data=json.dumps(event_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('event', data)
        self.assertEqual(data['event']['name'], 'AJAX Event')

    def test_add_event_ajax_get_method(self):
        """Test AJAX endpoint with GET method (should fail)"""
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get(reverse('event:add_event_ajax'))
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_add_event_ajax_invalid_json(self):
        """Test AJAX endpoint with invalid JSON"""
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.post(
            reverse('event:add_event_ajax'),
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_add_event_ajax_match_id_generation(self):
        """Test that match_id is generated correctly for different categories"""
        self.client.login(username='adminuser', password='adminpass123')

        categories = ['basketball', 'badminton', 'football', 'tennis', 'volleyball']
        prefixes = ['N', 'B', 'F', 'T', 'V']

        for category, prefix in zip(categories, prefixes):
            event_data = {
                'name': f'{category.title()} Event',
                'category': category,
                'date': timezone.now().isoformat(),
                'venue': 'Venue',
                'capacity': 1000,
                'home_team': 'Home',
                'away_team': 'Away',
                'description': 'Description',
            }
            response = self.client.post(
                reverse('event:add_event_ajax'),
                data=json.dumps(event_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)
            data = json.loads(response.content)
            # Check that match_id starts with correct prefix
            self.assertTrue(data['event']['match_id'].startswith(prefix))

    def test_add_event_ajax_as_non_admin(self):
        """Test AJAX endpoint as non-admin user"""
        self.client.login(username='testuser', password='testpass123')
        event_data = {
            'name': 'Event',
            'category': 'football',
            'date': timezone.now().isoformat(),
            'venue': 'Venue',
            'capacity': 1000,
            'home_team': 'Home',
            'away_team': 'Away',
            'description': 'Description',
        }
        response = self.client.post(
            reverse('event:add_event_ajax'),
            data=json.dumps(event_data),
            content_type='application/json'
        )
        # Deny access
        self.assertNotEqual(response.status_code, 201)

    def test_add_event_ajax_duplicate_match_id_handling(self):
        """Test that duplicate match_id is handled correctly"""
        self.client.login(username='adminuser', password='adminpass123')

        # Create first event
        event_data = {
            'name': 'First Event',
            'category': 'tennis',
            'date': timezone.now().isoformat(),
            'venue': 'Venue',
            'capacity': 1000,
            'home_team': 'Home',
            'away_team': 'Away',
            'description': 'Description',
        }
        response1 = self.client.post(
            reverse('event:add_event_ajax'),
            data=json.dumps(event_data),
            content_type='application/json'
        )
        self.assertEqual(response1.status_code, 201)

        # Create second event in same category
        event_data['name'] = 'Second Event'
        response2 = self.client.post(
            reverse('event:add_event_ajax'),
            data=json.dumps(event_data),
            content_type='application/json'
        )
        self.assertEqual(response2.status_code, 201)

        # Different match id for both events
        data1 = json.loads(response1.content)
        data2 = json.loads(response2.content)
        self.assertNotEqual(data1['event']['match_id'], data2['event']['match_id'])


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