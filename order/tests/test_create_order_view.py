from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from event.models import Event
from ticket.models import Ticket
from order.models import Order


class CreateOrderViewTests(TestCase):
    def setUp(self):
        # --- Users ---
        User = get_user_model()
        self.buyer = User.objects.create_user(
            username="buyer1",                   # ✅ required for default Django user
            email="buyer1@example.com",
            password="buyer123",
            is_active=True,
        )

        # --- Event & Tickets ---
        self.event = Event.objects.create(
            name="Derby Day",
            home_team="Home FC",
            away_team="Away FC",
            description="Big match",
            venue="Grand Stadium",
            date=timezone.now() + timezone.timedelta(days=7),
            capacity=50000,
        )

        self.ticket_reg = Ticket.objects.create(
            event=self.event,
            category=Ticket.CATEGORY_REGULAR,
            price=Decimal("100.00"),
            stock=100,
        )
        self.ticket_vip = Ticket.objects.create(
            event=self.event,
            category=Ticket.CATEGORY_VIP,
            price=Decimal("250.00"),
            stock=10,
        )

        self.create_url = reverse("order:create", args=[self.ticket_reg.id])
        self.history_url = reverse("order:history")

    # ---------- Helpers ----------
    def login(self):
        # login must use username, not email
        self.client.login(username="buyer1", password="buyer123")

    # ---------- Tests ----------
    def test_login_required_redirects_for_anonymous(self):
        resp = self.client.get(self.create_url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.post(self.create_url, {
            "quantity": 1,
            "ticket_id": str(self.ticket_reg.id),
            "action": "purchase",
        })
        self.assertEqual(resp.status_code, 302)

    def test_get_create_order_renders_ok(self):
        self.login()
        resp = self.client.get(self.create_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.event.name)
        self.assertContains(resp, "Seating Location")

    def test_purchase_confirms_and_decrements_stock_and_redirects(self):
        self.login()
        original_stock = self.ticket_vip.stock
        payload = {"quantity": "2", "ticket_id": str(self.ticket_vip.id), "action": "purchase"}
        resp = self.client.post(self.create_url, data=payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, self.history_url)

        order = Order.objects.get(user=self.buyer)
        self.assertEqual(order.ticket_id, self.ticket_vip.id)
        self.assertEqual(order.quantity, 2)
        self.assertEqual(order.status, Order.STATUS_CONFIRMED)
        self.assertEqual(order.harga, Decimal("250.00") * 2)

        self.ticket_vip.refresh_from_db()
        self.assertEqual(self.ticket_vip.stock, original_stock - 2)

    def test_save_ticket_pending_does_not_decrement_stock_and_redirects(self):
        self.login()
        original_stock = self.ticket_reg.stock
        payload = {"quantity": "3", "ticket_id": str(self.ticket_reg.id), "action": "pending"}
        resp = self.client.post(self.create_url, data=payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, self.history_url)

        order = Order.objects.get(user=self.buyer)
        self.assertEqual(order.ticket_id, self.ticket_reg.id)
        self.assertEqual(order.quantity, 3)
        self.assertEqual(order.status, Order.STATUS_PENDING)
        self.assertEqual(order.harga, Decimal("100.00") * 3)

        self.ticket_reg.refresh_from_db()
        self.assertEqual(self.ticket_reg.stock, original_stock)

    def test_quantity_exceeds_stock_shows_error_and_no_order_created(self):
        self.login()
        payload = {"quantity": "999", "ticket_id": str(self.ticket_vip.id), "action": "purchase"}
        resp = self.client.post(self.create_url, data=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Stok tidak mencukupi")
        self.assertFalse(Order.objects.filter(user=self.buyer).exists())

        self.ticket_vip.refresh_from_db()
        self.assertEqual(self.ticket_vip.stock, 10)

    def test_invalid_quantity_shows_error_and_no_order_created(self):
        self.login()
        for bad in ["0", "-5", ""]:
            payload = {"quantity": bad, "ticket_id": str(self.ticket_reg.id), "action": "pending"}
            resp = self.client.post(self.create_url, data=payload)
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, "Jumlah tiket tidak valid.")
            self.assertFalse(Order.objects.filter(user=self.buyer).exists())

    def test_select_ticket_from_form_not_url(self):
        self.login()
        payload = {"quantity": "1", "ticket_id": str(self.ticket_vip.id), "action": "pending"}
        resp = self.client.post(self.create_url, data=payload)
        self.assertEqual(resp.status_code, 302)
        order = Order.objects.get(user=self.buyer)
        self.assertEqual(order.ticket_id, self.ticket_vip.id)

    def test_edit_pending_order_updates(self):
        self.login()
        order = Order.objects.create(
            user=self.buyer, ticket=self.ticket_reg, quantity=2,
            status=Order.STATUS_PENDING, harga=self.ticket_reg.price * 2,
        )
        edit_url = reverse("order:edit", args=[self.ticket_reg.id, order.id])
        payload = {"quantity": "4", "ticket_id": str(self.ticket_vip.id), "action": "purchase"}
        vip_stock_before = self.ticket_vip.stock
        resp = self.client.post(edit_url, data=payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, self.history_url)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_CONFIRMED)
        self.assertEqual(order.ticket_id, self.ticket_vip.id)
        self.assertEqual(order.quantity, 4)
        self.assertEqual(order.harga, Decimal("250.00") * 4)

        self.ticket_vip.refresh_from_db()
        self.assertEqual(self.ticket_vip.stock, vip_stock_before - 4)

    def test_edit_non_pending_order_redirects_history(self):
        self.login()
        confirmed = Order.objects.create(
            user=self.buyer, ticket=self.ticket_reg, quantity=1,
            status=Order.STATUS_CONFIRMED, harga=self.ticket_reg.price * 1,
        )
        edit_url = reverse("order:edit", args=[self.ticket_reg.id, confirmed.id])
        resp = self.client.get(edit_url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, self.history_url)