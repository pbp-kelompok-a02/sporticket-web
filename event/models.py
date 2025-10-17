from django.db import models


class Event(models.Model):
	name = models.CharField(max_length=255)
	home_team = models.CharField(max_length=255)
	away_team = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	poster = models.ImageField(upload_to='events/posters/', blank=True, null=True)
	venue = models.CharField(max_length=255)
	date = models.DateTimeField()
	capacity = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['-date', 'name']

	def __str__(self):
		return f"{self.name} — {self.home_team} vs {self.away_team} @ {self.venue}"

