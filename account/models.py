from django.db import models
from django.contrib.auth.models import (
	AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.utils import timezone


class UserManager(BaseUserManager):
	def create_user(self, email, name=None, password=None, role='Buyer', phone_number=None, **extra_fields):
		if not email:
			raise ValueError('User must have a valid email')
		email = self.normalize_email(email) # normalisasi email, yaitu mengubah domain menjadi lowercase
		# buat instance user
		user = self.model(email=email, name=name or '', role=role, phone_number=phone_number, **extra_fields)
		user.set_password(password) # set password dengan hashing
		user.save(using=self._db) # simpan user ke database
		return user

	def create_admin(self, email, name=None, password=None, phone_number=None, **extra_fields):
		# application-level admin, bukan Django superuser		
		extra_fields.setdefault('is_active', True)
		return self.create_user(email=email, name=name, password=password, role='Admin', phone_number=phone_number, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin): 
	ROLE_CHOICES = (
		('Admin', 'Admin'),
		('Buyer', 'Buyer'),
	)

	email = models.EmailField(unique=True)
	name = models.CharField(max_length=150, blank=True)
	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Buyer')
	phone_number = models.CharField(max_length=30, blank=True, null=True)
	profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)

	is_active = models.BooleanField(default=True) # apakah akun aktif
	is_staff = models.BooleanField(default=False) # akses ke admin site (tidak digunakan karena pakai custom admin UI)
	date_joined = models.DateTimeField(default=timezone.now)

	objects = UserManager() # custom user manager untuk membuat user dan admin

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []

	def __str__(self):
		return f"{self.email} ({self.role})"

	def get_full_name(self):
		return self.name or self.email

	def get_short_name(self):
		return self.name or self.email

	@property
	def is_app_admin(self):
		"""Application-level admin check (role == 'Admin').
		Digunakan di views/decorators untuk melindungi halaman admin dari akses non-admin.
		"""
		return self.role == 'Admin'