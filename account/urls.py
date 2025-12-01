from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<int:user_id>/', views.profile_view, name='profile_detail'),
    path('profile/update/', views.profile_update, name='profile_update'),  # AJAX only
    path('profile/change-password/', views.change_password, name='change_password'),  # AJAX only
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('xml/', views.show_xml_user, name='show_xml_user'),
    path('json/', views.show_json_user, name='show_json_user'),
    path('xml/<int:user_id>/', views.show_xml_by_id_user, name='show_xml_by_id_user'),
    path('json/<int:user_id>/', views.show_json_by_id_user, name='show_json_by_id_user'),
    path('login-mobile/', views.login_mobile, name='login_mobile'),
]