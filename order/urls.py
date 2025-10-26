from django.urls import path
from . import views

app_name = "order"

urlpatterns = [
    path("create/<uuid:ticket_id>/", views.create_order, name="create"),
    path("edit/<uuid:ticket_id>//<int:order_id>/", views.create_order, name="edit"),
    path("history/", views.order_history, name="history"),
    path("cancel/<int:order_id>/", views.cancel_order, name="cancel"),
    path("cancel-ajax/<int:order_id>/", views.cancel_order_ajax, name="cancel_ajax"), 
]