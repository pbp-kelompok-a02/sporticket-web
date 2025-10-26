import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.http import Http404
from event.models import Event
from ticket.models import Ticket
from order.models import Order
from review.models import Review
from account.models import Profile 

User = get_user_model()


class ReviewViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # --- User dan Profil ---
        self.user_buyer = User.objects.create_user(
            username='buyer', 
            email="buyer@example.com", 
            password="buyer123"
        )
        Profile.objects.create(user=self.user_buyer, name="Buyer User", role="Buyer")

        self.user_buyer_no_review = User.objects.create_user(
            username='buyer2', 
            email="buyer2@example.com", 
            password="buyer123"
        )
        Profile.objects.create(user=self.user_buyer_no_review, name="Buyer 2", role="Buyer")
        
        self.user_other = User.objects.create_user(
            username='other', 
            email="other@example.com", 
            password="other123"
        )
        Profile.objects.create(user=self.user_other, name="Other User", role="Buyer")

        # --- Event ---
        self.event = Event.objects.create(
            name="Final Match",
            match_id="test-match-1",
            home_team="Team A",
            away_team="Team B",
            date=timezone.now() + timedelta(days=3),
        )
        self.event_other = Event.objects.create(
            name="Other Match",
            match_id="test-match-2",
            home_team="Team C",
            away_team="Team D",
            date=timezone.now() + timedelta(days=5),
        )

        # --- Tiket dan Order ---
        self.ticket = Ticket.objects.create(
            event=self.event,
            category=Ticket.CATEGORY_REGULAR,
            price=100000,
            stock=50
        )
        Order.objects.create(
            user=self.user_buyer,
            ticket=self.ticket,
            quantity=1,
            status=Order.STATUS_CONFIRMED
        )
        Order.objects.create(
            user=self.user_buyer_no_review,
            ticket=self.ticket,
            quantity=1,
            status=Order.STATUS_CONFIRMED
        )

        # --- Review ---
        self.review = Review.objects.create(
            user=self.user_buyer,
            event=self.event,
            rating=4,
            komentar="Great match!"
        )

        # --- URL ---
        self.url_preview = reverse('review:preview', args=[self.event.match_id])
        self.url_list = reverse('review:list', args=[self.event.match_id])
        self.url_create = reverse('review:create', args=[self.event.match_id])
        self.url_edit = reverse('review:edit', args=[self.event.match_id, self.review.id])
        self.url_delete = reverse('review:delete', args=[self.event.match_id, self.review.id])
        self.url_filter = reverse('review:filter', args=[self.event.match_id])
        self.valid_data = {'rating': 5, 'komentar': 'Awesome!'}

    # --- Tes Model ---
    def test_model_str(self):
        """Test: Review.__str__()"""
        expected_str = f'Review 4 by {self.user_buyer.username} for {self.event.name}'
        self.assertIn(expected_str, str(self.review))

    def test_model_is_owner(self):
        """Test: Review.is_owner()"""
        self.assertTrue(self.review.is_owner(self.user_buyer))
        self.assertFalse(self.review.is_owner(self.user_other))
        self.assertFalse(self.review.is_owner(None))

    # --- Tes Tampilan Halaman (GET) ---
    def test_view_pages_load_ok(self):
        """Test: Halaman preview dan list (GET 200)"""
        resp_preview = self.client.get(self.url_preview)
        resp_list = self.client.get(self.url_list)
        
        self.assertEqual(resp_preview.status_code, 200)
        self.assertEqual(resp_list.status_code, 200)
        self.assertTemplateUsed(resp_list, 'review/review_detail.html')
        self.assertTemplateUsed(resp_preview, 'review/review_preview.html')

    def test_view_pages_not_found(self):
        """Test: Halaman preview dan list (GET 404) untuk match_id yang salah"""
        url_preview_404 = reverse('review:preview', args=['bad-id'])
        url_list_404 = reverse('review:list', args=['bad-id'])
        resp_preview = self.client.get(url_preview_404)
        resp_list = self.client.get(url_list_404)
        self.assertEqual(resp_preview.status_code, 404)
        self.assertEqual(resp_list.status_code, 404)

    # --- Tes Konteks Tampilan ---
    def test_context_data_authenticated_with_ticket_and_review(self):
        """Test: Konteks untuk user login (punya tiket dan review)"""
        self.client.force_login(self.user_buyer)
        resp = self.client.get(self.url_list)
        
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['user_has_ticket'])
        self.assertTrue(resp.context['user_has_review'])
        self.assertEqual(resp.context['event'], self.event)

    def test_context_data_authenticated_no_ticket(self):
        """Test: Konteks untuk user login (tidak punya tiket)"""
        self.client.force_login(self.user_other)
        resp = self.client.get(self.url_list)
        
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['user_has_ticket'])
        self.assertFalse(resp.context['user_has_review'])

    def test_context_data_anonymous_user(self):
        """Test: Konteks untuk user anonim (semua False)"""
        resp = self.client.get(self.url_list)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['user_has_ticket'])
        self.assertFalse(resp.context['user_has_review'])

    # --- Tes add_review ---
    def test_add_review_get_not_allowed(self):
        """Test: add_review (GET 405) - @require_POST"""
        self.client.force_login(self.user_buyer)
        resp = self.client.get(self.url_create)
        self.assertEqual(resp.status_code, 405)

    def test_add_review_not_logged_in(self):
        """Test: add_review (POST 302) - @login_required"""
        resp = self.client.post(self.url_create, self.valid_data)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_add_review_no_ticket(self):
        """Test: add_review (POST 403) - Tidak punya tiket"""
        self.client.force_login(self.user_other)
        resp = self.client.post(self.url_create, self.valid_data)
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(json.loads(resp.content)['success'])

    def test_add_review_validation_errors(self):
        """Test: add_review (POST 400) - Error validasi data"""
        self.client.force_login(self.user_buyer)
        
        resp = self.client.post(self.url_create, {'komentar': 'Komentar saja'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Rating harus diisi', resp.content.decode())

        resp = self.client.post(self.url_create, {'rating': 'abc', 'komentar': 'Test'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Rating harus berupa angka', resp.content.decode())
        
        resp = self.client.post(self.url_create, {'rating': 6, 'komentar': 'Test'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Rating harus antara 1-5', resp.content.decode())

        resp = self.client.post(self.url_create, {'rating': 5, 'komentar': ''})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Komentar harus diisi', resp.content.decode())

    def test_add_review_success_create(self):
        """Test: add_review (POST 200) - Sukses membuat review baru"""
        self.client.force_login(self.user_buyer_no_review)
        
        resp = self.client.post(self.url_create, self.valid_data)
        self.assertEqual(resp.status_code, 200)
        
        data = json.loads(resp.content)
        self.assertTrue(data['success'])
        self.assertTrue(data['created'])
        
        self.assertIn("Awesome!", data['html'])
        self.assertIn("Buyer 2", data['html'])
        self.assertTrue(Review.objects.filter(user=self.user_buyer_no_review, event=self.event).exists())

    def test_add_review_success_update(self):
        """Test: add_review (POST 200) - Sukses update review (created=False)"""
        self.client.force_login(self.user_buyer)
        
        resp = self.client.post(self.url_create, {'rating': 1, 'komentar': 'Updated comment'})
        self.assertEqual(resp.status_code, 200)
        
        data = json.loads(resp.content)
        self.assertTrue(data['success'])
        self.assertFalse(data['created'])
        
        self.assertIn("Updated comment", data['html'])
        self.assertIn("Buyer User", data['html'])
        
        self.review.refresh_from_db()
        self.assertEqual(self.review.komentar, 'Updated comment')
        self.assertEqual(self.review.rating, 1)

    # --- Tes edit_review ---
    def test_edit_review_get_not_allowed(self):
        """Test: edit_review (GET 405) - @require_POST"""
        self.client.force_login(self.user_buyer)
        resp = self.client.get(self.url_edit)
        self.assertEqual(resp.status_code, 405)

    def test_edit_review_not_logged_in(self):
        """Test: edit_review (POST 302) - @login_required"""
        resp = self.client.post(self.url_edit, self.valid_data)
        self.assertEqual(resp.status_code, 302)

    def test_edit_review_not_found(self):
        """Test: edit_review (POST 404) - Review ID salah"""
        self.client.force_login(self.user_buyer)
        url_404 = reverse('review:edit', args=[self.event.match_id, 9999])
        resp = self.client.post(url_404, self.valid_data)
        # PERBAIKAN: Sekarang view melempar 404 dengan benar
        self.assertEqual(resp.status_code, 404)

    def test_edit_review_wrong_match_id(self):
        """Test: edit_review (POST 404) - match_id salah"""
        self.client.force_login(self.user_buyer)
        url_wrong_match = reverse('review:edit', args=[self.event_other.match_id, self.review.id])
        resp = self.client.post(url_wrong_match, self.valid_data)
        self.assertEqual(resp.status_code, 404)
        self.assertIn('Review tidak ditemukan', resp.content.decode())

    def test_edit_review_not_owner(self):
        """Test: edit_review (POST 403) - Bukan pemilik review"""
        self.client.force_login(self.user_other)
        resp = self.client.post(self.url_edit, self.valid_data)
        self.assertEqual(resp.status_code, 403)
        self.assertIn('Anda tidak memiliki izin', resp.content.decode())

    def test_edit_review_validation_errors(self):
        """Test: edit_review (POST 400) - Error validasi data"""
        self.client.force_login(self.user_buyer)
        
        resp = self.client.post(self.url_edit, {'rating': '', 'komentar': 'Test'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Rating harus diisi', resp.content.decode())

        resp = self.client.post(self.url_edit, {'rating': 5, 'komentar': ''})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Komentar harus diisi', resp.content.decode())

    # --- Tes delete_review ---
    def test_delete_review_get_not_allowed(self):
        """Test: delete_review (GET 405) - @require_POST"""
        self.client.force_login(self.user_buyer)
        resp = self.client.get(self.url_delete)
        self.assertEqual(resp.status_code, 405)

    def test_delete_review_not_logged_in(self):
        """Test: delete_review (POST 302) - @login_required"""
        resp = self.client.post(self.url_delete)
        self.assertEqual(resp.status_code, 302)

    def test_delete_review_not_found(self):
        """Test: delete_review (POST 404) - Review ID salah"""
        self.client.force_login(self.user_buyer)
        url_404 = reverse('review:delete', args=[self.event.match_id, 9999])
        resp = self.client.post(url_404)
        self.assertEqual(resp.status_code, 404)

    def test_delete_review_not_owner(self):
        """Test: delete_review (POST 404) - Bukan pemilik review"""
        self.client.force_login(self.user_other)
        resp = self.client.post(self.url_delete)
        self.assertEqual(resp.status_code, 404)

    def test_delete_review_wrong_match_id(self):
        """Test: delete_review (POST 404) - match_id salah"""
        self.client.force_login(self.user_buyer)
        url_wrong_match = reverse('review:delete', args=[self.event_other.match_id, self.review.id])
        resp = self.client.post(url_wrong_match)
        self.assertEqual(resp.status_code, 404)
        self.assertIn('Review tidak ditemukan', resp.content.decode())

    def test_delete_review_success(self):
        """Test: delete_review (POST 200) - Sukses menghapus"""
        self.client.force_login(self.user_buyer)
        review_id = self.review.id
        
        resp = self.client.post(self.url_delete)
        self.assertEqual(resp.status_code, 200)
        
        data = json.loads(resp.content)
        self.assertTrue(data['success'])
        self.assertIn('Review berhasil dihapus', data['message'])
        self.assertFalse(Review.objects.filter(id=review_id).exists())

    # --- Tes filter_reviews ---
    def test_filter_reviews_not_logged_in(self):
        """Test: filter_reviews (GET 302) - @login_required"""
        resp = self.client.get(self.url_filter + '?type=my')
        self.assertEqual(resp.status_code, 302)

    def test_filter_reviews_not_found(self):
        """Test: filter_reviews (GET 404) - match_id salah"""
        self.client.force_login(self.user_buyer)
        url_404 = reverse('review:filter', args=['bad-id'])
        resp = self.client.get(url_404 + '?type=my')
        self.assertEqual(resp.status_code, 404)

    def test_filter_reviews_all_my_default(self):
        """Test: filter_reviews (GET 200) - Cek filter 'all', 'my', dan default"""
        self.client.force_login(self.user_buyer)
        
        Review.objects.create(
            user=self.user_other, 
            event=self.event, 
            rating=1, 
            komentar="Not mine"
        )
        
        # Filter 'all'
        resp_all = self.client.get(self.url_filter + '?type=all')
        self.assertEqual(resp_all.status_code, 200)
        data_all = json.loads(resp_all.content)
        self.assertIn("Great match!", data_all['html'])
        self.assertIn("Not mine", data_all['html'])

        # Filter 'my'
        resp_my = self.client.get(self.url_filter + '?type=my')
        self.assertEqual(resp_my.status_code, 200)
        data_my = json.loads(resp_my.content)
        self.assertIn("Great match!", data_my['html'])
        self.assertNotIn("Not mine", data_my['html'])
        
        # Filter default (tanpa parameter type)
        resp_default = self.client.get(self.url_filter)
        self.assertEqual(resp_default.status_code, 200)
        data_default = json.loads(resp_default.content)
        self.assertIn("Great match!", data_default['html'])
        self.assertIn("Not mine", data_default['html'])