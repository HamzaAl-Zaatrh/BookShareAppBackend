from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    # user_image_url = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'address',  'password', 'confirm_password']
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
    
    # def create(self, validated_data):
    #     user = User.objects.create_user(
    #         email=validated_data['email'],
    #         first_name=validated_data['first_name'],
    #         last_name=validated_data['last_name'],
    #         password=validated_data['password']
    #     )

    #     user.generate_verification_token()
    #     user.save()

    #     # Send verification email
    #     subject = 'Verify your email address'
    #     message = f'Hi {user.first_name},\n\nThank you for registering in our website. Please verify your email address by clicking on the following link: http://localhost:8000/user/verify-email/{user.verification_token}/\n\nBest regards,\nTeam'
    #     from_email = settings.EMAIL_FROM
    #     recipient_list = [user.email]
    #     send_mail(subject, message, from_email, recipient_list)

    #     return user
    ###########################################################################################

#     def update(self, instance, validated_data):
#         if 'password' in validated_data:
#             password = validated_data.pop('password')
#             instance.set_password(password)

#         return super().update(instance, validated_data)


# class PasswordResetSerializer(serializers.Serializer):
#     email = serializers.EmailField()

#     def validate_email(self, value):
#         """
#         Check that the email is registered
#         """
#         try:
#             User.objects.get(email=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError(
#                 'There is no user registered with this email address'
#             )
#         return value

#     def send_password_reset_email(self):
#         email = self.validated_data['email']
#         user = User.objects.get(email=email)

#         # Generate password reset token
#         user.generate_verification_token()
#         user.save()

#         # Send password reset email
#         subject = 'Password Reset Request'
#         message = f'Hi {user.first_name},\n\nYou have requested to reset your password. Please click on the following link to reset your password: http://localhost:8000/user/password-reset/{user.verification_token}/\n\nBest regards,\nTeam'
#         from_email = settings.EMAIL_FROM
#         recipient_list = [user.email]
#         send_mail(subject, message, from_email, recipient_list)


# class PasswordResetConfirmSerializer(serializers.Serializer):
#     password = serializers.CharField(max_length=128)
#     verification_token = serializers.CharField(max_length=64)
#     def validate_verification_token(self, value):
#         """
#         Check that the verification token is valid
#         """
#         try:
#             user = User.objects.get(verification_token=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError(
#                 'Invalid verification token'
#             )

#         if not user.verification_token:
#             raise serializers.ValidationError(
#                 'Invalid verification token'
#             )

#         return value

#     def save(self):
#         user = User.objects.get(verification_token=self.validated_data['verification_token'])
#         user.set_password(self.validated_data['password'])
#         user.verification_token = None
#         user.save()

#         return user
