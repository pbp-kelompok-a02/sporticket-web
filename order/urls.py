from django.urls import path
from . import views

app_name = "order"

urlpatterns = [
    path("create/<uuid:ticket_id>/", views.create_order, name="create"),
    path("edit/<uuid:ticket_id>/<int:order_id>/", views.create_order, name="edit"),
    path("history/", views.order_history, name="history"),
    path("cancel/<int:order_id>/", views.cancel_order, name="cancel"),
    path("cancel-ajax/<int:order_id>/", views.cancel_order_ajax, name="cancel_ajax"), 
    path("create-flutter/<uuid:ticket_id>/", views.create_order_flutter),
    path("history-flutter/", views.order_history_flutter),
    path("edit-flutter/<int:order_id>/", views.edit_order_flutter),
    path("detail-flutter/<int:order_id>/", views.order_detail_flutter),
    path("confirm-flutter/<int:order_id>/", views.confirm_order_flutter),
    path("cancel-flutter/<int:order_id>/", views.cancel_order_flutter),
]