from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<int:user_id>/', views.profile_view, name='profile_detail'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('xml/', views.show_xml_user, name='show_xml_user'),
    path('json/', views.show_json_user, name='show_json_user'),
    path('xml/<int:user_id>/', views.show_xml_by_id_user, name='show_xml_by_id_user'),
    path('json/<int:user_id>/', views.show_json_by_id_user, name='show_json_by_id_user'),
    path('login-mobile/', views.login_mobile, name='login_mobile'),
    path('register-mobile/', views.register_mobile, name='register_mobile'),
    path('logout-mobile/', views.logout_mobile, name='logout_mobile'),
    path('profile-mobile/', views.profile_mobile, name='profile_mobile'),
    path('profile-mobile/<int:user_id>/', views.profile_mobile, name='profile_mobile_detail'),
    path('edit-profile-mobile/', views.edit_profile_mobile, name='edit_profile_mobile'),
    path('change-password-mobile/', views.change_password_mobile, name='change_password_mobile'),
]