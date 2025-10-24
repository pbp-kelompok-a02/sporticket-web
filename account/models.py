from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
	ROLE_CHOICES = (
		('Admin', 'Admin'),
		('Buyer', 'Buyer'),
	)

	# field email dan password sudah ada di model User
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	name = models.CharField(max_length=150, blank=True)
	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Buyer')
	phone_number = models.CharField(max_length=30, blank=True, null=True, unique=True)
	profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)

	def __str__(self):
		return f"{self.name or self.user.get_username()} ({getattr(self.user, 'email', '')})"

	@property
	def email(self):
		return getattr(self.user, 'email', '')

	def set_password(self, raw_password):
		self.user.set_password(raw_password)
		self.user.save(update_fields=['password'])

	def get_display_name(self):
		return self.name or getattr(self.user, 'get_full_name', lambda: '')()

	class Meta:
		verbose_name = 'Profile'
		verbose_name_plural = 'Profiles'

