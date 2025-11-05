from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
	path('<str:match_id>/preview/', views.review_preview, name='preview'),
    path('<str:match_id>/all/', views.show_reviews, name='list'),
    path('<str:match_id>/create/', views.add_review, name='create'),
    path('<str:match_id>/<int:review_id>/edit/', views.edit_review, name='edit'),
    path('<str:match_id>/<int:review_id>/delete/', views.delete_review, name='delete'),
    path("<str:match_id>/filter/", views.filter_reviews, name="filter"),
    
]
