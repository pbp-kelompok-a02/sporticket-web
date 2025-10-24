from django.urls import path
from . import views

app_name = "order"

urlpatterns = [
    path("create/<int:ticket_id>/", views.create_order, name="create"),
    path("edit/<int:ticket_id>/<int:order_id>/", views.create_order, name="edit"),
    path("history/", views.order_history, name="history"),
    path("cancel/<int:order_id>/", views.cancel_order, name="cancel"),
]
