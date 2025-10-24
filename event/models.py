import uuid

from django.db import models


class Event(models.Model):
	CATEGORY = [
		('badminton', 'Badminton'),
		('football', 'Football'),
		('basketball', 'Basketball'),
		('tennis', 'Tennis'),
		('volleyball', 'Volleyball'),
	]
	match_id = models.CharField(max_length=100, unique=True, default='')
	name = models.CharField(max_length=255)
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	home_team = models.CharField(max_length=255)
	away_team = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	poster = models.ImageField(upload_to='events/posters/', blank=True, null=True)
	venue = models.CharField(max_length=255)
	date = models.DateTimeField()
	capacity = models.PositiveIntegerField(default=0)
	category = models.CharField(max_length=20, choices=CATEGORY, default='football')

	class Meta:
		ordering = ['-date', 'name']

	def __str__(self):
		return f"{self.name} — {self.home_team} vs {self.away_team} @ {self.venue}"

