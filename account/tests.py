from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


class AccountFlowTests(TestCase):
	def setUp(self):
		self.register_url = reverse('account:register')
		self.login_url = reverse('account:login')
		self.profile_url = reverse('account:profile')
		self.profile_update_url = reverse('account:profile_update')
		self.change_password_url = reverse('account:change_password')
		self.delete_account_url = reverse('account:delete_account')

	def test_registration_creates_user_and_profile(self):
		data = {
			'email': 'alice@example.com',
			'name': 'Alice',
			'password': 's3cr3tpass',
			'password2': 's3cr3tpass',
			'phone_number': '08123456789',
			'role': 'Buyer',
		}
		resp = self.client.post(self.register_url, data)
		# registrasi berhasil jika redirect ke login
		self.assertEqual(resp.status_code, 302)
		user = User.objects.filter(email__iexact='alice@example.com').first()
		self.assertIsNotNone(user)
		# profile dibuat
		self.assertTrue(hasattr(user, 'profile'))
		self.assertEqual(user.profile.name, 'Alice')

	def test_login_with_email(self):
		user = User.objects.create_user(username='bob@example.com', email='bob@example.com', password='pw')
		Profile.objects.create(user=user, name='Bob')
		resp = self.client.post(self.login_url, {'username': 'bob@example.com', 'password': 'pw'})
		# terima redirect atau sukses
		self.assertIn(resp.status_code, (302, 200))
		# session harus memiliki user yang terautentikasi
		self.assertIn('_auth_user_id', self.client.session)

	def test_profile_update_changes_email_and_requires_new_login(self):
		# register dan login
		reg = {
			'email': 'carol@example.com',
			'name': 'Carol',
			'password': 'oldpass',
			'password2': 'oldpass',
		}
		# buat user
		user = User.objects.create_user(username='carol@example.com', email='carol@example.com', password='oldpass')
		Profile.objects.create(user=user, name='Carol')
		# login
		logged = self.client.login(username='carol@example.com', password='oldpass')
		self.assertTrue(logged)

		# update profile email
		resp = self.client.post(self.profile_update_url, {'email': 'carol.new@example.com', 'name': 'Carol New', 'role': 'Buyer'})
		# redirect kembali ke profile
		self.assertIn(resp.status_code, (302, 200))
		user = User.objects.get(email__iexact='carol.new@example.com')
		self.assertIsNotNone(user)

		# logout, lalu coba login dengan email lama harus gagal
		self.client.get(reverse('account:logout'))
		resp_old = self.client.post(self.login_url, {'username': 'carol@example.com', 'password': 'oldpass'})
		# login dengan email lama harus gagal (no auth id set)
		self.assertNotIn('_auth_user_id', self.client.session)

		# login dengan email baru harus berhasil
		resp_new = self.client.post(self.login_url, {'username': 'carol.new@example.com', 'password': 'oldpass'})
		self.assertIn('_auth_user_id', self.client.session)

	def test_change_password_requires_new_password_after_logout(self):
		user = User.objects.create_user(username='dan@example.com', email='dan@example.com', password='initial')
		Profile.objects.create(user=user, name='Dan')
		# login
		self.client.post(self.login_url, {'username': 'dan@example.com', 'password': 'initial'})
		self.assertTrue('_auth_user_id' in self.client.session)

		# ubah password
		resp = self.client.post(self.change_password_url, {
			'current_password': 'initial',
			'new_password': 'newsecure',
			'new_password2': 'newsecure',
		})
		# pastikan logout untuk testing login ulang
		self.client.get(reverse('account:logout'))

		# password lama harus gagal
		resp_old = self.client.post(self.login_url, {'username': 'dan@example.com', 'password': 'initial'})
		self.assertNotIn('_auth_user_id', self.client.session)

		# password baru harus berhasil
		resp_new = self.client.post(self.login_url, {'username': 'dan@example.com', 'password': 'newsecure'})
		self.assertIn('_auth_user_id', self.client.session)

	def test_delete_account_removes_user(self):
		user = User.objects.create_user(username='eve@example.com', email='eve@example.com', password='pw')
		Profile.objects.create(user=user, name='Eve')
		# login
		self.client.post(self.login_url, {'username': 'eve@example.com', 'password': 'pw'})
		# delete
		resp = self.client.post(self.delete_account_url)
		# harusnya redirect
		self.assertIn(resp.status_code, (302, 200))
		self.assertFalse(User.objects.filter(email__iexact='eve@example.com').exists())

	def test_profile_public_visibility_anonymous(self):
		# buat user dengan info sensitif
		user = User.objects.create_user(username='frank@example.com', email='frank@example.com', password='pw')
		Profile.objects.create(user=user, name='Frank', phone_number='0811999')
		# visitor anonim melihat detail profil
		resp = self.client.get(reverse('account:profile_detail', args=[user.pk]))
		self.assertEqual(resp.status_code, 200)
		# harus menampilkan nama, tapi tidak nomor telepon
		self.assertContains(resp, 'Frank')
		# nomor telepon tidak muncul
		content = resp.content.decode()
		self.assertNotIn('>0811999<', content)

	def test_profile_visibility_non_owner_logged_in(self):
		# buat 2 user
		owner = User.objects.create_user(username='gina@example.com', email='gina@example.com', password='pw')
		Profile.objects.create(user=owner, name='Gina', phone_number='0813000')
		viewer = User.objects.create_user(username='harry@example.com', email='harry@example.com', password='pw')
		Profile.objects.create(user=viewer, name='Harry')
		# login sebagai viewer (harry)
		self.client.login(username='harry@example.com', password='pw')
		# lihat profil owner (gina)
		resp = self.client.get(reverse('account:profile_detail', args=[owner.pk]))
		self.assertEqual(resp.status_code, 200) # harusnya sukses
		# harus menampilkan nama, tapi tidak nomor telepon
		self.assertContains(resp, 'Gina')
		# nomor telepon tidak muncul
		content = resp.content.decode()
		self.assertNotIn('>0813000<', content)

	def test_profile_visibility_owner_and_admin(self):
		# owner liat data sensitifnya sendiri
		owner = User.objects.create_user(username='ivy@example.com', email='ivy@example.com', password='pw')
		Profile.objects.create(user=owner, name='Ivy', phone_number='0814000')
		self.client.login(username='ivy@example.com', password='pw')
		resp = self.client.get(reverse('account:profile'))
		self.assertEqual(resp.status_code, 200)
		# ada nomor teleponnya
		self.assertContains(resp, '0814000')
		self.client.logout()

		# admin melihat data sensitif milik orang lain
		admin = User.objects.create_user(username='admin@example.com', email='admin@example.com', password='pw')
		Profile.objects.create(user=admin, name='Admin', role='Admin')
		self.client.login(username='admin@example.com', password='pw')
		resp2 = self.client.get(reverse('account:profile_detail', args=[owner.pk]))
		self.assertEqual(resp2.status_code, 200)
		self.assertContains(resp2, '0814000')
		self.client.logout()

	def test_login_sets_session_and_logout_clears(self):
		user = User.objects.create_user(username='jack@example.com', email='jack@example.com', password='pw')
		Profile.objects.create(user=user, name='Jack', role='Buyer')
		resp = self.client.post(self.login_url, {'username': 'jack@example.com', 'password': 'pw'})
		# login harus set session keys
		s = self.client.session
		# views set authentication id, login view juga set cookie 'last_login'
		self.assertIn('_auth_user_id', s)
		# cek cookie set
		self.assertIn('last_login', self.client.cookies)
		# logout akan clear authentication
		self.client.get(reverse('account:logout'))
		s2 = self.client.session
		self.assertNotIn('_auth_user_id', s2)


	def test_profile_update_ajax_returns_user_email(self):
		user = User.objects.create_user(username='kate@example.com', email='kate@example.com', password='pw')
		profile = Profile.objects.create(user=user, name='Kate')
		self.client.login(username='kate@example.com', password='pw')
		new_email = 'kate.new@example.com'
		resp = self.client.post(self.profile_update_url, {
			'email': new_email,
			'name': 'Kate New',
			'role': 'Buyer'
		}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data.get('success'))
		# cek email di database, bukan di response JSON
		user.refresh_from_db()
		self.assertEqual(user.email, new_email)

	def test_register_ajax_creates_user(self):
		resp = self.client.post(self.register_url, {
			'email': 'ajax@example.com',
			'name': 'Ajax',
			'password': 'pass1234',
			'password2': 'pass1234'
		}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data.get('success'))
		self.assertTrue(User.objects.filter(email__iexact='ajax@example.com').exists())

	def test_change_password_ajax_works_and_requires_new_password(self):
		user = User.objects.create_user(username='chg@example.com', email='chg@example.com', password='start')
		Profile.objects.create(user=user, name='Changer')
		self.client.login(username='chg@example.com', password='start')
		resp = self.client.post(self.change_password_url, {
			'current_password': 'start',
			'new_password': 'newpass1',
			'new_password2': 'newpass1'
		}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data.get('success'))
		self.client.get(reverse('account:logout'))
		self.client.post(self.login_url, {'username': 'chg@example.com', 'password': 'start'})
		self.assertNotIn('_auth_user_id', self.client.session)
		self.client.post(self.login_url, {'username': 'chg@example.com', 'password': 'newpass1'})
		self.assertIn('_auth_user_id', self.client.session)
