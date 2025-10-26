from django.db import models
from django.core.validators import MinValueValidator
import uuid

class Ticket(models.Model):
	CATEGORY_VIP = 'VIP'
	CATEGORY_REGULAR = 'REG'
	CATEGORY_CHOICES = [
		(CATEGORY_VIP, 'VIP'),
		(CATEGORY_REGULAR, 'Reguler'),
	]

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	event = models.ForeignKey(
		'event.Event',
		on_delete=models.CASCADE,
		related_name='tickets'
	)
	category = models.CharField(max_length=4, choices=CATEGORY_CHOICES)
	price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
	stock = models.PositiveIntegerField(default=0)

	def __str__(self):
		return f'{self.event}: {self.get_category_display()}'

	def is_available(self, quantity=1):
		return self.stock >= quantity

	def increase_stock(self, amount):
		if amount < 0:
			raise ValueError('amount must be non-negative')
		self.stock += int(amount)
		self.save(update_fields=['stock'])

	def decrease_stock(self, amount):
		if amount < 0:
			raise ValueError('amount must be non-negative')
		if amount > self.stock:
			raise ValueError('insufficient stock')
		self.stock -= int(amount)
		self.save(update_fields=['stock'])

	def reserve(self, quantity=1):
		if self.is_available(quantity):
			self.decrease_stock(quantity)
			return True
		return False
