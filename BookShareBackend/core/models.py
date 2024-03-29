from django.db import models
from django.core import validators
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from datetime import timedelta


def upload_to(instance, filename):
    return 'images/book/{filename}'.format(filename=filename)


class Category(models.Model):
    category = models.CharField(max_length=30)

    def __str__(self):
        return self.category


class Book(models.Model):
    book_name = models.CharField(max_length=200)
    author = models.CharField(max_length=30)
    publisher = models.CharField(max_length=30, blank=True, null=True)
    description = models.TextField(max_length=200, blank=True, null=True)
    ISBN = models.IntegerField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    categories = models.ManyToManyField(Category, blank=True)
    owners = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, through='UserBook', through_fields=(
        'book_id', 'book_owner_id'), related_name='books_owned')

    def __str__(self):
        return self.book_name

    def calculate_avg_rating(self):
        # Get all UserBook objects for this book
        book_ratings = BookRating.objects.filter(book_id=self)

        # Calculate the average rating for this book
        total_rating = sum(
            book_rating.book_rating for book_rating in book_ratings)
        num_ratings = book_ratings.count()
        if num_ratings > 0:
            avg_rating = round(total_rating / num_ratings, 1)
        else:
            avg_rating = 0

        return avg_rating

    def calculate_number_rating(self):
        # Get all UserBook objects for this book
        book_ratings = BookRating.objects.filter(book_id=self)

        # Get the number of ratings for this book
        num_ratings = book_ratings.count()

        return num_ratings


class UserBook(models.Model):
    book_owner_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_book')
    book_id = models.ForeignKey(Book, on_delete=models.CASCADE)
    book_image_url = models.ImageField(upload_to=upload_to, blank=True, null=True, default="default_book.png")
    status = models.BooleanField(default=True)
    borrowed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='borrowed_book')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Descending order
        unique_together = ('book_owner_id', 'book_id')

    def __str__(self):
        return f'{self.book_owner_id.get_full_name()} | {self.book_id.book_name} | status: {self.status}'


class BookRating(models.Model):
    book_id = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='bookrating')
    book_rater_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book_rating = models.IntegerField(
        validators=[validators.MinValueValidator(0), validators.MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('book_id', 'book_rater_id')

    def __str__(self):
        return f'{self.book_id.book_name} | {self.book_rater_id.get_full_name()} | rating: {self.book_rating}'


class UserRating(models.Model):
    user_rated_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings_received')
    user_rater_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings_given')
    user_rating = models.IntegerField(
        validators=[validators.MinValueValidator(0), validators.MaxValueValidator(10)])
    
    class Meta:
        unique_together = ('user_rated_id', 'user_rater_id')

    def __str__(self):
        return f'rated: {self.user_rated_id.get_full_name()} | rater: {self.user_rater_id.get_full_name()} | rating: {self.user_rating}'


class Notification(models.Model):
    sender_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sender')
    receiver_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receiver')
    user_book_id = models.ForeignKey(UserBook, on_delete=models.CASCADE, null=True)
    type = models.CharField(max_length=20)
    message = models.TextField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.type

    def time_since_created(self):
        now = timezone.now()
        time_difference = now - self.created_at

        if time_difference < timedelta(minutes=1):
            return f"{time_difference.seconds} s"
        elif time_difference < timedelta(hours=1):
            return f"{int(time_difference.seconds/60)} m"
        elif time_difference < timedelta(days=1):
            return f"{int(time_difference.seconds/3600)} h"
        elif time_difference < timedelta(weeks=1):
            return f"{time_difference.days} d"
        else:
            return f"{int(time_difference.days/7)} w"
