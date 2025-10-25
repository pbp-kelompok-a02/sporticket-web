from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from event.models import Event
from ticket.models import Ticket
from order.models import Order
from django.utils import timezone

User = get_user_model()

class OrderHistoryViewTests(TestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username="buyer",                   # ✅ required for default user
            email="buyer@example.com",
            password="buyer123",
            is_active=True,
        )
        self.event = Event.objects.create(
            name="Derby Day",
            home_team="A",
            away_team="B",
            venue="Stadium",
            date=timezone.now(),
            capacity=100
        )
        self.ticket_reg = Ticket.objects.create(event=self.event, category="REG", price=100, stock=50)
        self.ticket_vip = Ticket.objects.create(event=self.event, category="VIP", price=250, stock=10)

        self.history_url = reverse("order:history")

    def login(self):
        return self.client.login(username="buyer", password="buyer123")

    def test_redirects_if_not_logged_in(self):
        """Anonymous user should be redirected to login page."""
        self.client.logout()
        resp = self.client.get(self.history_url)
        self.assertEqual(resp.status_code, 302)
        # update to match your actual login URL name (commonly "account:login" or similar)
        self.assertIn("login", resp.url)

    def test_empty_history_shows_message(self):
        self.login()
        resp = self.client.get(self.history_url)
        self.assertContains(resp, "Belum ada pesanan")

    def test_pending_order_shows_edit_and_delete(self):
        self.login()
        order = Order.objects.create(
            user=self.user, ticket=self.ticket_reg,
            quantity=2, status=Order.STATUS_PENDING, harga=200
        )
        resp = self.client.get(self.history_url)
        self.assertContains(resp, order.ticket.event.name)
        self.assertContains(resp, "Edit")
        self.assertContains(resp, "Delete")

    def test_confirmed_order_shows_bought(self):
        self.login()
        order = Order.objects.create(
            user=self.user, ticket=self.ticket_vip,
            quantity=1, status=Order.STATUS_CONFIRMED, harga=250
        )
        resp = self.client.get(self.history_url)
        self.assertContains(resp, order.ticket.event.name)
        self.assertContains(resp, "Bought")

    def test_cancelled_order_shows_cancelled(self):
        self.login()
        order = Order.objects.create(
            user=self.user, ticket=self.ticket_reg,
            quantity=1, status=Order.STATUS_CANCELLED, harga=100
        )
        resp = self.client.get(self.history_url)
        self.assertContains(resp, order.ticket.event.name)
        self.assertContains(resp, "Cancelled")

    def test_history_only_shows_user_orders(self):
        self.login()
        other = User.objects.create_user(
            username="other",                   # ✅ username required
            email="other@example.com",
            password="other123",
        )
        Order.objects.create(user=other, ticket=self.ticket_reg,
                             quantity=1, status=Order.STATUS_CONFIRMED, harga=100)

        resp = self.client.get(self.history_url)
        # shouldn't show other user's orders
        self.assertNotContains(resp, "other@example.com")