from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from . import serializers
from django.shortcuts import get_object_or_404


User = get_user_model()


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def logout_view(request):
    request.user.auth_token.delete()
    return Response({'success': 'Logged out successfully'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def verify_email(request, token):
    user = get_object_or_404(User, verification_token=token)
    user.is_active = True
    user.verification_token = None
    user.save()
    return Response({'success': 'Email verification successful'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def registration_view(request):
    serializer = serializers.RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    
    # send verification email
    user.generate_verification_token()
    subject = 'Verify Your Email'
    message = f'Hi {user.first_name},\n\nPlease click on the link to verify your email: {request.build_absolute_uri("/account/verify-email/")}{user.verification_token}/\n\nBest,\nMySite Team'
    from_email = settings.EMAIL_FROM
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)

    return Response({'success': 'Registration successful. Please check your email to verify your account.'}, status=status.HTTP_201_CREATED)


# @api_view(['POST'])
# @permission_classes((permissions.AllowAny,))
# def reset_password(request):
#     email = request.data.get('email')
#     if not email:
#         return Response({'error': 'Please provide an email address'}, status=status.HTTP_400_BAD_REQUEST)

#     user = get_object_or_404(User, email=email)
#     user.generate_verification_token()

#     # send password reset email
#     subject = 'Reset Your Password'
#     message = f'Hi {user.first_name},\n\nPlease click on the link to reset your password: {request.build_absolute_uri("/reset-password/")}{user.verification_token}/\n\nBest,\nMySite Team'
#     from_email = settings.EMAIL_FROM
#     recipient_list = [user.email]
#     send_mail(subject, message, from_email, recipient_list)

#     return Response({'success': 'Password reset instructions have been sent to your email address.'}, status=status.HTTP_200_OK)
