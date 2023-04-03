from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import hashlib
from django.contrib.auth.hashers import make_password
import os
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from core.models import Book, UserBook, UserRating


def upload_to(instance, filename):
    return 'images/user/{filename}'.format(filename=filename)


class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        """
        Creates and saves a User with the given email, first name, last name, and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name,
                          last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email, first name, last name, and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, first_name, last_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # 'email' must be unique because it is named as the 'USERNAME_FIELD'
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    user_image_url = models.ImageField(
        upload_to=upload_to, blank=True, null=True, default="default_user.png")
    about = models.TextField(blank=True, null=True)
    books = models.ManyToManyField(Book, blank=True, through=UserBook, through_fields=(
        'book_owner_id', 'book_id'), related_name='users')
    date_registered = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)  # We must verify the email
    is_staff = models.BooleanField(default=False)
    # Field to store verification token
    verification_token = models.CharField(max_length=64, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def generate_verification_token(self):
        # Generate a random token
        token = hashlib.sha256(os.urandom(1024)).hexdigest()
        self.verification_token = token
        self.save()

    def __str__(self):
        """
        Returns a string representation of the user.
        """
        return self.email

    def get_full_name(self):
        """
        Returns the user's full name.
        """
        return f"{self.first_name} {self.last_name}"

    def set_password(self, raw_password):
        """
        Sets the user's password to the given raw password after hashing it.
        """
        self.password = make_password(raw_password)
        self.save()
    
    def calculate_avg_rating(self):
        # Get all UserBook objects for this book
        user_ratings = UserRating.objects.filter(user_rated_id=self)

        # Calculate the average rating for this book
        total_rating = sum(user_rating.user_rating for user_rating in user_ratings)
        num_ratings = user_ratings.count()
        if num_ratings > 0:
            avg_rating = total_rating / num_ratings
        else:
            avg_rating = 0

        return avg_rating

    def calculate_number_rating(self):
        # Get all UserBook objects for this book
        user_ratings = UserRating.objects.filter(user_rated_id=self)

        # Get the number of ratings for this book
        num_ratings = user_ratings.count()

        return num_ratings


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
