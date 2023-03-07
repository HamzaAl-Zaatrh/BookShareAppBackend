from django.db import models
from django.core import validators
from django.contrib.auth.models import User

class Books(models.Model):
    book_name = models.CharField(max_length=200)
    author = models.CharField(max_length=30)
    publisher = models.CharField(max_length=30)
    description = models.TextField(max_length=200)
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    ISBN = models.IntegerField()
    year = models.IntegerField()
    avg_rating = models.FloatField(default=0)
    number_rating = models.IntegerField(default=0)

    def __str__(self):
        return self.book_name

class Categories(models.Model):
    pass

class BookCategories(models.Model):
    pass

class UserBooks(models.Model):
    pass

class BookRatings(models.Model):
    pass 

#  
  
# class UserRatings(models.Model):
#     pass