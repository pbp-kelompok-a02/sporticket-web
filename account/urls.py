from django.urls import path
from django.http import HttpResponse

def index(request):
	return HttpResponse('Account index')

app_name = 'account'

urlpatterns = [
	path('', index, name='index'),
]
