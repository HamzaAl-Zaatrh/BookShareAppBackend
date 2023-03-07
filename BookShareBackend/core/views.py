from .models import Book
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.exceptions import ValidationError
from . import serializers


class BooksViewSet(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = serializers.BooksSerializer 
