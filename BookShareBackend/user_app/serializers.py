from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from core.models import UserBook

User = get_user_model()


class ProfileInfoSerializer(serializers.ModelSerializer):
    full_name = serializers.StringRelatedField(source='get_full_name')
    avg_rating = serializers.StringRelatedField(source='calculate_avg_rating')
    number_rating = serializers.StringRelatedField(
        source='calculate_number_rating')

    class Meta:
        model = User
        fields = ['id', 'full_name', 'avg_rating', 'number_rating', 'email', 'phone_number',
                  'address', 'user_image_url', 'about']


class UserInfoSerializer(serializers.ModelSerializer):
    """To get his full name, id, and his image"""
    full_name = serializers.StringRelatedField(source='get_full_name')

    class Meta:
        model = User
        fields = ['id', 'full_name', 'user_image_url']


class ChangePasswordSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)
    confirm_new_password = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['current_password', 'new_password', 'confirm_new_password']

    def save(self):
        user = self.context['request'].user
        current_password = self.validated_data['current_password']
        new_password = self.validated_data['new_password']
        confirm_new_password = self.validated_data['confirm_new_password']

        if new_password != confirm_new_password:
            raise serializers.ValidationError(
                {'error': 'New password and confirm new password must be the same'})

        if not user.check_password(current_password):
            raise serializers.ValidationError(
                {'error': 'current password is incorrect'})

        user.set_password(new_password)
        user.save()

        # Send password change email
        subject = 'Password changed successfully'
        message = f'Hi {user.get_full_name()},\n\nYour password has been changed successfully.\n\nBest regards,\nBookShare Team'
        from_email = settings.EMAIL_FROM
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)

        return user


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number',
                  'address', 'user_image_url', 'about', 'books']

        extra_kwargs = {
            'books': {'read_only': True},
            'email': {'read_only': True}
        }

    def validate(self, data):
        if not data.get('user_image_url'):
            data['user_image_url'] = 'default_user.png'
        return data


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)
    # user_image_url = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number',
                  'address',  'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def save(self):

        password = self.validated_data['password']
        confirm_password = self.validated_data['confirm_password']

        if password != confirm_password:
            raise serializers.ValidationError(
                {'error': 'password and confirm_password must be the same'})

        # if User.objects.filter(email=self.validated_data['email']).exists():
        #     raise serializers.ValidationError(
        #         {'error': 'email already exists!'})

        account = User(
            email=self.validated_data['email'],
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name'],
            phone_number=self.validated_data['phone_number'],
            address=self.validated_data['address'])
        account.set_password(password)

        account.save()
        return account

#     def update(self, instance, validated_data):
#         if 'password' in validated_data:
#             password = validated_data.pop('password')
#             instance.set_password(password)

#         return super().update(instance, validated_data)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        """
        Check that the email is registered
        """
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'There is no user registered with this email address'
            )
        return value

    def send_password_reset_email(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)

        # Generate password reset token
        user.generate_verification_token()
        user.save()

        # Send password reset email
        subject = 'Password Reset Request'
        message = f'Hi {user.get_full_name()},\n\nYou have requested to reset your password. Please click on the following link to reset your password: http://127.0.0.1:8000/account/password-reset/{user.verification_token}/\n\nBest regards,\nBookShare Team'
        from_email = settings.EMAIL_FROM
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128)
    verification_token = serializers.CharField(max_length=64)

    def validate_verification_token(self, value):
        """
        Check that the verification token is valid
        """
        try:
            user = User.objects.get(verification_token=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'Invalid verification token'
            )

        if not user.verification_token:
            raise serializers.ValidationError(
                'Invalid verification token'
            )

        return value

    def save(self):
        user = User.objects.get(
            verification_token=self.validated_data['verification_token'])
        user.set_password(self.validated_data['password'])
        user.verification_token = None
        user.save()

        return user