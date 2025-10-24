from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
	path('<int:event_id>/preview/', views.review_preview, name='preview'),
    path('<int:event_id>/all/', views.show_reviews, name='list'),
    path('<int:event_id>/create/', views.add_review, name='create'),
    path('<int:review_id>/edit/', views.edit_review, name='edit'),
    path('<int:review_id>/delete/', views.delete_review, name='delete'),
    path("<int:event_id>/filter/", views.filter_reviews, name="filter"),
    
]
