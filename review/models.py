from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='reviews'
	)
	event = models.ForeignKey(
		'event.Event',
		on_delete=models.CASCADE,
		related_name='reviews'
	)
	rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
	komentar = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']
		unique_together = ('user', 'event')  # satu review per user per event

	def __str__(self):
		return f'Review {self.rating} by {self.user} for {self.event}'

	def is_owner(self, user):
		return self.user_id == getattr(user, 'id', None)
