from django.urls import path
from django.http import HttpResponse

# ini cuma biar gw bisa makemigrations
# nanti kalian apus aja trs ganti sm urls kalian yg bener
def index(request):
	return HttpResponse('Review index')

app_name = 'review'

urlpatterns = [
	path('', index, name='index'),
]
