from django.db import models
from django.conf import settings
from django.utils import timezone

class Order(models.Model):
	STATUS_PENDING = 'pending'
	STATUS_CONFIRMED = 'confirmed'
	STATUS_CANCELLED = 'cancelled'

	STATUS_CHOICES = [
		(STATUS_PENDING, 'Pending'),
		(STATUS_CONFIRMED, 'Confirmed'),
		(STATUS_CANCELLED, 'Cancelled'),
	]

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
	ticket = models.ForeignKey('ticket.Ticket', on_delete=models.PROTECT, related_name='orders')
	quantity = models.PositiveIntegerField(default=1)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"Order #{self.pk} by {self.user} ({self.quantity}x) - {self.status}"

	def can_modify(self):
		return self.status == self.STATUS_PENDING

	def cancel(self):
		# batalkan order saat masih pending atau confirmed
		self.status = self.STATUS_CANCELLED
		self.save(update_fields=['status', 'updated_at'])