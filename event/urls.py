from django.urls import path
from django.http import HttpResponse
from event.views import show_event_main, event_detail, add_event, edit_event, delete_event, add_event_ajax, show_json, proxy_image, create_event_flutter, update_event_flutter, delete_event_flutter

# ini cuma biar gw bisa makemigrations
# nanti kalian apus aja trs ganti sm urls kalian yg bener
def index(request):
	return HttpResponse('Event index')

app_name = 'event'

urlpatterns = [
	path('', show_event_main, name='show_event_main'),
    path('events/json/', show_json, name='show_json'),
    path('events/add/', add_event, name='add_event'),
    path('events/create-flutter/', create_event_flutter, name='create_event_flutter'),
    path('events/update-flutter/<str:match_id>/', update_event_flutter, name='update_event_flutter'),
    path('events/delete-flutter/<str:match_id>/', delete_event_flutter, name='delete_event_flutter'),
    path('events/add-event-ajax/', add_event_ajax, name='add_event_ajax'),
    path('events/<str:match_id>/', event_detail, name='event_detail'),
	path('events/<str:match_id>/edit/', edit_event, name='edit_event'),
	path('events/<str:match_id>/delete/', delete_event, name='delete_event'),
    path('proxy-image/', proxy_image, name='proxy_image'),


]
