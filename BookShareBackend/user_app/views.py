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
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.serializers import ValidationError
from .permissions import *
from rest_framework.permissions import IsAuthenticated


User = get_user_model()


class ProfileInfo(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = serializers.ProfileInfoSerializer


class ChangePassword(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = serializers.ChangePasswordSerializer

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)


class ProfileDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated & IsOwnerOrReadOnly]
    queryset = User.objects.all()
    serializer_class = serializers.ProfileSerializer


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        username = request.data["username"]

        if not User.objects.filter(email=username).exists():
            return Response({'error': 'email not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        token, created = Token.objects.get_or_create(user=user)

        # Build image URL
        image_url = None
        if user.user_image_url:
            image_url = request.build_absolute_uri(user.user_image_url.url)

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'user_image_url': image_url
        })


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
    message = f'Hi {user.get_full_name()},\n\nPlease click on the link to verify your email: {request.build_absolute_uri("/account/verify-email/")}{user.verification_token}/\n\nBest regards,\nBookShare Team'
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
