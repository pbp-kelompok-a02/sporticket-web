from django.urls import path
from . import views, APIviews

app_name = 'review'

urlpatterns = [
	path('<str:match_id>/preview/', views.review_preview, name='preview'),
    path('<str:match_id>/all/', views.show_reviews, name='list'),
    path('<str:match_id>/create/', views.add_review, name='create'),
    path('<str:match_id>/<int:review_id>/edit/', views.edit_review, name='edit'),
    path('<str:match_id>/<int:review_id>/delete/', views.delete_review, name='delete'),
    path("<str:match_id>/filter/", views.filter_reviews, name="filter"),
    path('<str:match_id>/api/', APIviews.get_reviews_json, name='get_reviews_json'),
    path('<str:match_id>/api/add/', APIviews.add_review_flutter, name='add_review_flutter'),
    path('<str:match_id>/api/edit/<int:review_id>/', APIviews.edit_review_flutter, name='edit_review_flutter'),
    path('<str:match_id>/api/delete/<int:review_id>/', APIviews.delete_review_flutter, name='delete_review_flutter'),
]
