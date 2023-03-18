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
    subject = 'Verify Your Email - BookShare'
    message = f'Hi {user.get_full_name()},\n\nPlease click on the link to verify your email: {request.build_absolute_uri(" ")}{user.verification_token}/\n\nBest regards,\nBookShare Team'
    from_email = settings.EMAIL_FROM
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)

    return Response({'success': 'Registration successful. Please check your email to verify your account.'}, status=status.HTTP_201_CREATED)


class PasswordResetView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Send password reset email
        serializer.send_password_reset_email()

        return Response(
            {'detail': 'Password reset email has been sent'},
            status=status.HTTP_200_OK
        )

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = serializers.PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'detail': 'Password has been reset'},
            status=status.HTTP_200_OK
        )
