from rest_framework import serializers
from .models import Book

class BooksSerializer(serializers.ModelSerializer):
    image_url = serializers.ImageField(required=False)

    class Meta:
        model = Book
        fields = '__all__'