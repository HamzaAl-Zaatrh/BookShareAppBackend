from django.urls import path, include
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('login/', obtain_auth_token, name='login'),
    path('register/', views.registration_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
