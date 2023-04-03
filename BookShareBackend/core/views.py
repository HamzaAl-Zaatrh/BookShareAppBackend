from .models import *
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.exceptions import ValidationError
from . import serializers
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from .permissions import *
from django_filters.rest_framework import DjangoFilterBackend
from user_app.models import User
from django.shortcuts import get_object_or_404


######################### Home Page (List of all books) with search/Filter/ordering #################
# /list/?search=dfgd&book_id__categories=&status=


class BookUserList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserBook.objects.all()
    serializer_class = serializers.UserBookSerializer
    filter_backends = [filters.SearchFilter,
                       DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['book_id__book_name', 'book_id__author', 'book_id__ISBN',
                     'book_owner_id__first_name', 'book_owner_id__last_name', 'book_owner_id__address']
    filterset_fields = ['book_id__categories', 'status']
    ordering_fields = ['created_at']

    def get_queryset(self):
        user = self.request.user
        return UserBook.objects.exclude(book_owner_id=user)


################################### add a book page 1 (search) #######################################
# /book/?search=
class BookSearch(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Book.objects.all()
    serializer_class = serializers.BookSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['book_name', 'author', 'ISBN']

    # To ensure that the books returned are not owned by the user before
    def get_queryset(self):
        user = self.request.user
        # return Book.objects.exclude(owners=user).distinct()
        return Book.objects.exclude(owners=user)

################################### add a book page 2 (new) ##########################################


class AddNewBookView(generics.CreateAPIView):
    serializer_class = serializers.BookSerializer

    def post(self, request, *args, **kwargs):
        # Convert comma-separated string to list of integers
        # categories_str = request.data.get('categories')
        # categories_list = [int(cat) for cat in categories_str.split(',')]

        book_serializer = self.get_serializer(data=request.data)
        book_serializer.is_valid(raise_exception=True)
        book = book_serializer.save()

        # Create UserBook object for the book owner
        user_book_data = {
            'book_owner_id': request.user.id,
            'book_id': book.id,
            'book_image_url': request.FILES.get('book_image_url'),
            'status': True
        }
        user_book_serializer = serializers.BookOwnerSerializer(
            data=user_book_data)
        user_book_serializer.is_valid(raise_exception=True)
        user_book_serializer.save()

        # Create BookRating object for the book
        book_rating_data = {}
        if not request.data.get('rating'):
            book_rating_data = {
                'book_id': book.id,
                'book_rater_id': request.user.id,
                'book_rating': 0
            }
        else:
            book_rating_data = {
                'book_id': book.id,
                'book_rater_id': request.user.id,
                'book_rating': request.data.get('rating')
            }

        book_rating_serializer = serializers.BookRatingSerializer(
            data=book_rating_data)
        book_rating_serializer.is_valid(raise_exception=True)
        book_rating_serializer.save()

        return Response({'detail': 'The book add successfully.'}, status=status.HTTP_201_CREATED)

########################################### GET categories ########################################


class CategoriesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer

################################# Your Library Page Functionality #################################
# List your books


class YourBooksList(generics.ListAPIView):
    permission_classes = [IsAuthenticated & IsOwner]
    queryset = UserBook.objects.all()
    serializer_class = serializers.YourBooksSerializer
    filter_backends = [filters.SearchFilter,
                       DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['book_id__book_name', 'book_id__author', 'book_id__ISBN']
    filterset_fields = ['book_id__categories', 'status']
    ordering_fields = ['created_at']

    def get_queryset(self):
        user = self.request.user
        return UserBook.objects.filter(book_owner_id=user)

# Repost Functionality


class RepostOrDelete(generics.UpdateAPIView, generics.DestroyAPIView):
    permission_classes = [IsAuthenticated & IsOwner]
    queryset = UserBook.objects.all()
    serializer_class = serializers.YourBooksSerializer
    # {
    #   "status": true
    # }
    # We check if the status field is being updated to True. If it is, we set the borrowed_by field to None

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Check if status is being updated to True
        if 'status' in request.data and request.data['status'] is True:
            # Set borrowed_by to null
            instance.borrowed_by = None

        serializer.save()
        return Response(serializer.data)

############################## Library Visitor Page ##################################


class LibraryBooksList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserBook.objects.all()
    serializer_class = serializers.UserBookSerializer
    filter_backends = [filters.SearchFilter,
                       DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['book_id__book_name', 'book_id__author', 'book_id__ISBN']
    filterset_fields = ['book_id__categories', 'status']
    ordering_fields = ['created_at']

    def get_queryset(self):
        pk = self.kwargs.get('pk')  # Get the pk parameter from the URL
        return UserBook.objects.filter(book_owner_id=pk)


class UserRatingDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserRating.objects.all()
    serializer_class = serializers.UserRatingSerializer

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')  # Get the pk parameter from the URL
        user_rater_id = request.user.id
        user_rating_qs = UserRating.objects.filter(
            user_rated_id=pk, user_rater_id=user_rater_id)

        if user_rating_qs.exists():
            user_rating = user_rating_qs.first()
            serializer = self.serializer_class(user_rating)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            user_rated_id = get_object_or_404(User, pk=pk)
            data = {'user_rating': 0,
                    'avg_rating': user_rated_id.calculate_avg_rating(),
                    'number_rating': user_rated_id.calculate_number_rating()}
            return Response(data, status=status.HTTP_200_OK)
            # return Response({'detail': 'The requested rating does not exist.'}, status=status.HTTP_404_NOT_FOUND)


class UserRatingCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserRating.objects.all()

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')  # Get the pk parameter from the URL
        user_rater_id = request.user.id
        rating = request.data.get('rating')

        # Check if UserRating object already exists
        user_rating_qs = UserRating.objects.filter(
            user_rated_id=pk, user_rater_id=user_rater_id)
        if user_rating_qs.exists():
            user_rating = user_rating_qs.first()
            user_rating.user_rating = rating
            user_rating.save()
            serializer = serializers.UserRatingSerializer(user_rating)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Create UserRating object
        user_rating_data = {
            'user_rated_id': pk,
            'user_rater_id': user_rater_id,
            'user_rating': rating
        }
        serializer = serializers.UserRatingSerializer(data=user_rating_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


############################## Book Visitor Page ##################################

class BookDetails(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserBook.objects.all()
    serializer_class = serializers.UserBookSerializer


class SameBookView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserBook.objects.all()
    serializer_class = serializers.UserBookSerializer

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs.get('pk') 
        # Get all books that are similar to this one but don't show the book we're on and don't show the book if the user owns it
        similar_books = UserBook.objects.filter(book_id=UserBook.objects.get(pk=pk).book_id).exclude(id=pk).exclude(book_owner_id=user)
        if similar_books.exists():
            return similar_books
        else:
            return UserBook.objects.none()


class BookRatingDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = BookRating.objects.all()
    serializer_class = serializers.BookRatingSerializer

    def get(self, request, *args, **kwargs):
        user_book_id = self.kwargs.get('pk')  # Get the pk parameter from the URL
        pk = UserBook.objects.get(pk=user_book_id).book_id.id
        book_rater_id = request.user.id
        book_rating_qs = BookRating.objects.filter(
            book_id=pk, book_rater_id=book_rater_id)

        if book_rating_qs.exists():
            book_rating = book_rating_qs.first()
            serializer = self.serializer_class(book_rating)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            book_id = get_object_or_404(Book, pk=pk)
            data = {'book_rating': 0,
                    'avg_rating': book_id.calculate_avg_rating(),
                    'number_rating': book_id.calculate_number_rating()}
            return Response(data, status=status.HTTP_200_OK)
            # return Response({'detail': 'The requested rating does not exist.'}, status=status.HTTP_404_NOT_FOUND)


class BookRatingCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserRating.objects.all()

    def post(self, request, *args, **kwargs):
        user_book_id = self.kwargs.get('pk')  # Get the pk parameter from the URL
        pk = UserBook.objects.get(pk=user_book_id).book_id.id
        book_rater_id = request.user.id
        rating = request.data.get('rating')

        # Check if BookRating object already exists
        book_rating_qs = BookRating.objects.filter(
            book_id=pk, book_rater_id=book_rater_id)
        if book_rating_qs.exists():
            book_rating = book_rating_qs.first()
            book_rating.book_rating = rating
            book_rating.save()
            serializer = serializers.BookRatingSerializer(book_rating)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Create BookRating object
        book_rating_data = {
            'book_id': pk,
            'book_rater_id': book_rater_id,
            'book_rating': rating
        }
        serializer = serializers.BookRatingSerializer(data=book_rating_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
