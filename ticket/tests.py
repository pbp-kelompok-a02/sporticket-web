from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from event.models import Event
from ticket.models import Ticket
import json
import uuid


class TicketViewTest(TestCase):
    def setUp(self):
        # Buat user login
        self.user = User.objects.create_user(username="tester", password="12345")
        self.client = Client()
        self.client.login(username="tester", password="12345")

        # Buat event
        self.event = Event.objects.create(
            match_id="E001",
            name="Big Match",
            category="Tournament",
            home_team="A Team",
            away_team="B Team",
            date=timezone.now().date(),
            venue="Stadium A"
        )

        # Buat tiket
        self.ticket = Ticket.objects.create(
            event=self.event,
            category=Ticket.CATEGORY_VIP,
            price=100.00,
            stock=10
        )

    def test_str_method(self):
        self.assertIn("VIP", str(self.ticket))

    def test_is_available_true_false(self):
        self.assertTrue(self.ticket.is_available(5))
        self.assertFalse(self.ticket.is_available(20))

    def test_increase_stock_positive(self):
        initial = self.ticket.stock
        self.ticket.increase_stock(5)
        self.assertEqual(self.ticket.stock, initial + 5)

    def test_increase_stock_negative(self):
        with self.assertRaises(ValueError):
            self.ticket.increase_stock(-1)

    def test_decrease_stock_valid(self):
        initial = self.ticket.stock
        self.ticket.decrease_stock(3)
        self.assertEqual(self.ticket.stock, initial - 3)

    def test_decrease_stock_invalid_amount(self):
        with self.assertRaises(ValueError):
            self.ticket.decrease_stock(-5)

    def test_decrease_stock_overflow(self):
        with self.assertRaises(ValueError):
            self.ticket.decrease_stock(9999)

    def test_reserve_success_and_fail(self):
        # success
        self.assertTrue(self.ticket.reserve(2))
        # fail
        self.assertFalse(self.ticket.reserve(999))

    def test_show_tickets_view(self):
        url = reverse("ticket:show_tickets", args=[self.event.match_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tickets.html")
        self.assertIn("event", response.context)
        self.assertIn("ticket_list", response.context)

    def test_create_ticket_valid_post(self):
        url = reverse("ticket:create_ticket", args=[self.event.match_id])
        data = {
            "category": Ticket.CATEGORY_REGULAR,
            "price": 50.0,
            "stock": 30
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Ticket.objects.filter(category=Ticket.CATEGORY_REGULAR).exists())

    def test_create_ticket_get(self):
        url = reverse("ticket:create_ticket", args=[self.event.match_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create_ticket.html")

    def test_edit_ticket_get_ajax(self):
        url = reverse("ticket:edit_ticket", args=[self.ticket.id])
        response = self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"form", response.content)

    def test_edit_ticket_get_non_ajax(self):
        url = reverse("ticket:edit_ticket", args=[self.ticket.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_ticket.html")

    def test_edit_ticket_post_valid_ajax(self):
        url = reverse("ticket:edit_ticket", args=[self.ticket.id])
        data = {
            "category": Ticket.CATEGORY_REGULAR,
            "price": 75.0,
            "stock": 20
        }
        response = self.client.post(
            url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"updated": True, "html": response.json()["html"]})

    def test_edit_ticket_post_invalid_ajax(self):
        url = reverse("ticket:edit_ticket", args=[self.ticket.id])
        data = {"category": "", "price": "", "stock": ""}
        response = self.client.post(
            url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("updated", response.json())

    def test_delete_ticket_ajax_post(self):
        url = reverse("ticket:delete_ticket_ajax", args=[self.ticket.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"deleted": True})

    def test_delete_ticket_ajax_invalid_method(self):
        url = reverse("ticket:delete_ticket_ajax", args=[self.ticket.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_add_ticket_ajax_post(self):
        url = reverse("ticket:add_ticket_ajax")
        data = {
            "event_id": self.event.match_id,
            "category": Ticket.CATEGORY_VIP,
            "price": 250.0,
            "stock": 5
        }
        response = self.client.post(
            url, json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("html", response.json())

    def test_add_ticket_ajax_invalid_json(self):
        url = reverse("ticket:add_ticket_ajax")
        response = self.client.post(url, "invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 500)

    def test_add_ticket_ajax_invalid_method(self):
        url = reverse("ticket:add_ticket_ajax")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_edit_ticket_ajax_valid(self):
        url = reverse("ticket:edit_ticket_ajax", args=[self.ticket.id])
        data = {
            "category": Ticket.CATEGORY_REGULAR,
            "price": 99.9,
            "stock": 8
        }
        response = self.client.post(
            url, json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["updated"])

    def test_edit_ticket_ajax_exception(self):
        url = reverse("ticket:edit_ticket_ajax", args=["invalid-id"])
        response = self.client.post(
            url, json.dumps({}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_show_json_all(self):
        url = reverse("ticket:show_json")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_show_json_by_event(self):
        # tes endpoint /ticket/json/?match_id=E001
        response = self.client.get(reverse("ticket:show_json"), {"match_id": self.event.match_id})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertGreaterEqual(len(response.json()), 1)
