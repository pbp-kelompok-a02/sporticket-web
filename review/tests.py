from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from event.models import Event
from ticket.models import Ticket
from order.models import Order
from review.models import Review
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class ReviewTestCase(TestCase):
    def setUp(self):
        # Client setup
        self.client = Client()

        # Buat user buyer dan admin
        self.user_buyer = User.objects.create_user(email="buyer@example.com", password="buyer123", role="Buyer")
        self.user_admin = User.objects.create_admin(email="admin@example.com", password="admin123")

        # Buat event
        self.event = Event.objects.create(
            name="Final Match",
            home_team="Team A",
            away_team="Team B",
            description="Final Championship",
            venue="Main Stadium",
            date=timezone.now() + timedelta(days=3),
            capacity=1000
        )

        # Buat ticket
        self.ticket = Ticket.objects.create(
            event=self.event,
            category=Ticket.CATEGORY_REGULAR,
            price=100000,
            stock=50
        )

        # Buat order hanya untuk user_buyer
        self.order = Order.objects.create(
            user=self.user_buyer,
            ticket=self.ticket,
            quantity=2,
            status=Order.STATUS_CONFIRMED
        )

        # Review awal
        self.review = Review.objects.create(
            user=self.user_buyer,
            event=self.event,
            rating=4,
            komentar="Bagus banget pertandingannya!"
        )

    def test_model_str(self):
        """Pastikan string representation Review sesuai format"""
        self.assertIn("Review", str(self.review))
        self.assertIn("buyer", str(self.review))

    def test_user_can_create_review_if_has_ticket(self):
        """User dengan riwayat pembelian tiket bisa buat review"""
        self.client.login(email="buyer@example.com", password="buyer123")
        response = self.client.post(reverse('review:create', args=[self.event.id]), {
            "rating": 5,
            "komentar": "Keren banget!",
        })
        # Cek sukses dan review baru ada di DB
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Review.objects.filter(user=self.user_buyer, event=self.event, rating=5).exists())

    def test_user_cannot_create_review_without_ticket(self):
        """User tanpa riwayat pembelian tidak boleh buat review"""
        new_user = User.objects.create_user(email="noorder@example.com", password="test123", role="Buyer")
        self.client.login(email="noorder@example.com", password="test123")
        response = self.client.post(reverse('review:create', args=[self.event.id]), {
            "rating": 5,
            "komentar": "Ga punya tiket tapi mau review",
        })
        self.assertEqual(response.status_code, 403)

    def test_user_can_edit_own_review(self):
        """User hanya bisa edit review miliknya"""
        self.client.login(email="buyer@example.com", password="buyer123")
        response = self.client.post(reverse('review:edit', args=[self.review.id]), {
            "rating": 3,
            "komentar": "Update komentar",
        })
        self.assertEqual(response.status_code, 200)
        self.review.refresh_from_db()
        self.assertEqual(self.review.komentar, "Update komentar")

    def test_user_cannot_edit_others_review(self):
        """User lain tidak boleh edit review orang lain"""
        another_user = User.objects.create_user(email="other@example.com", password="test123", role="Buyer")
        self.client.login(email="other@example.com", password="test123")
        response = self.client.post(reverse('review:edit', args=[self.review.id]), {
            "rating": 1,
            "komentar": "Saya ubah komentar orang lain"
        })
        self.assertEqual(response.status_code, 403)

    def test_user_can_delete_own_review(self):
        """User bisa hapus review sendiri"""
        self.client.login(email="buyer@example.com", password="buyer123")
        response = self.client.post(reverse('review:delete', args=[self.review.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())


    def test_review_detail_page_loads(self):
        """Halaman semua review untuk event bisa diakses"""
        url = reverse('review:list', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Reviews for", response.content)
        print(response.content)
