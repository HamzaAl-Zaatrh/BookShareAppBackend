from django.urls import path, include
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('login/', views.CustomAuthToken.as_view(), name='login'),
    path('register/', views.registration_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/', views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('profile/<int:pk>/', views.ProfileDetail.as_view(), name='profile_details'),
    path('change-password/',
         views.ChangePassword.as_view(), name='change_password'),
     # For Library Visitor Page
     path('<int:pk>/', views.ProfileInfo.as_view(), name='profile_info'),
]
