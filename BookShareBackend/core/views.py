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
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
# from .recommender import *

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
        similar_books = UserBook.objects.filter(book_id=UserBook.objects.get(
            pk=pk).book_id).exclude(id=pk).exclude(book_owner_id=user)
        if similar_books.exists():
            return similar_books
        else:
            return UserBook.objects.none()


class BookRatingDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = BookRating.objects.all()
    serializer_class = serializers.BookRatingSerializer

    def get(self, request, *args, **kwargs):
        # Get the pk parameter from the URL
        user_book_id = self.kwargs.get('pk')
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
        # Get the pk parameter from the URL
        user_book_id = self.kwargs.get('pk')
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


############################## Notifications functionalities ##################################
# two forms for the JSON request:
############### (1) ###################
# {
#     "user_book_id": 1,
#     "type": "borrow_request",
#     "message": ""
# }
############### (2) ###################
# {
#      "user_book_id": 1,
#     "receiver_id": 2,
#     "type": "accept/reject",
#     "message": "you can use this number: 0788888888 to contact with me"
# }

class NotificationRequest(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()

    def post(self, request, *args, **kwargs):
        type = request.data.get('type')
        user_book_qs = UserBook.objects.filter(
            id=request.data.get('user_book_id'))

        if not user_book_qs.exists():
            return Response({'detail': 'The Book does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        if (type == 'accept' or type == 'reject') and not (user_book_qs.first().book_owner_id.id == request.user.id):
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        if type == 'borrow_request' and not user_book_qs.first().status:
            return Response({'detail': 'This book is already borrowed.'}, status=status.HTTP_400_BAD_REQUEST)

        notification_data = {}

        if type == 'borrow_request':
            notification_data = {
                'sender_id': request.user.id,
                'receiver_id': user_book_qs.first().book_owner_id.id,
                'user_book_id': user_book_qs.first().id,
                'type': type,
                'message': ''
            }
        else:
            notification_data = {
                'sender_id': request.user.id,
                'receiver_id': request.data.get('receiver_id'),
                'user_book_id': user_book_qs.first().id,
                'type': type,
                'message': request.data.get('message')
            }

        # if type == 'accept' we must modify the 'status' and 'borrowed_by' fields in the UserBook model
        if type == 'accept':
            user_book = user_book_qs.first()
            user_book.status = False
            user_book.borrowed_by = User.objects.get(
                id=request.data.get('receiver_id'))
            user_book.save()

        notification_serializer = serializers.NotificationsSerializer(
            data=notification_data)
        notification_serializer.is_valid(raise_exception=True)
        notification_serializer.save()
        return Response({'detail': 'The notification has been sent successfully.'}, status=status.HTTP_201_CREATED)
        # return Response(notification_serializer.data, status=status.HTTP_201_CREATED)
    
class NotificationList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()
    serializer_class = serializers.NotificationsSerializer

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(receiver_id = user)
    
class NotificationDestroy(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()
    serializer_class = serializers.NotificationsSerializer

    def delete(self, request, *args, **kwargs):
        notification_id = self.kwargs.get('pk')
        notification = Notification.objects.get(pk=notification_id)
        if not notification.receiver_id == self.request.user:
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
# To get the contact information you can use http://127.0.0.1:8000/account/<sender_id>/


############################## Recommender functionalities ##################################

def get_recommendations(id, user_id):
    # Load UserBooks into a DataFrame
    user_books = pd.DataFrame.from_records(UserBook.objects.all().values(
        'id', 'book_owner_id', 'book_id', 'book_id__book_name', 'book_id__author', 'book_id__categories__category', 'book_image_url'))
    ratings_df = pd.DataFrame.from_records(BookRating.objects.all().values())

    book_rater_id = user_id # set the book_rater_id_id that you want to filter by
    # get all the books rated by this user as a list
    rated_books = ratings_df.loc[ratings_df['book_rater_id_id'] == book_rater_id, 'book_id_id'].tolist()
    print(rated_books)
    
    user_books['book_image_url'] = user_books['book_image_url'].apply(lambda x: 'http://127.0.0.1:8000/media/' + x)

    # Renaming the columns
    user_books = user_books.rename(columns={
        'book_id__book_name': 'title',
        'book_owner_id': 'owner_id',
        'book_id__author': 'author',
        'book_id__categories__category': 'genres',
        'book_image_url': 'image'
    })

    if not user_books[(user_books['owner_id'] == user_id) & (user_books['id'] == id)].empty:
        return {'detail': 'Bad request, this book is owned by this user'}
        # return Response({'detail': 'Bad request, this book is owned by this user'}, status=status.HTTP_400_BAD_REQUEST)



    # drop all books that owned by this user
    user_books = user_books.drop(user_books[user_books['owner_id'] == user_id].index)

    # drop all books that rated by this user
    user_books = user_books.drop(rated_books)

    # Grouping the data and drop duplicates
    data = user_books.groupby('id').agg({
        'book_id': 'first',
        'owner_id': 'first',
        'title': 'first',
        'author': 'first',
        'genres': lambda x: ', '.join(set(x)),
        'image': 'first'
    }).drop_duplicates(['book_id'], keep='last').reset_index()

    cleaned_data = data.copy()

    # Function to convert all strings to lower case and strip names of spaces
    def clean_data(x):
        #Check if director exists. If not, return empty string
        if isinstance(x, str):
            out = str.lower(x.replace(" ", ""))
            output_string = out.replace(',', ' ')
            return output_string
        else:
            return ''
            
    # Apply clean_data function to your features.
    features = ['author', 'genres']

    for feature in features:
        cleaned_data[feature] = cleaned_data[feature].apply(clean_data)

    def create_metadata(x):
        return x['author'] + ' ' + x['genres']
    cleaned_data['metadata'] = cleaned_data.apply(create_metadata, axis=1)

    count = CountVectorizer(stop_words='english')
    count_matrix = count.fit_transform(cleaned_data['metadata'])

    cosine_sim = cosine_similarity(count_matrix, count_matrix)

    print(data)
    print(cosine_sim)

    index = data.index[data['id'] == id][0]

    similarity_series = pd.Series(cosine_sim[index]).sort_values(ascending=False)
    list_index = similarity_series[similarity_series > 0.3].index.tolist()

    list_index.remove(index)
    recommended_data = []
    if len(list_index) <= 10:
        recommended_data = data.iloc[list_index]
    else:
        recommended_data = data.iloc[list_index[:10]]

    # print(recommended_data)

    # convert dataframe to dictionary
    # We used the 'records' option in the to_dict() method 
    # to convert the DataFrame to a list of dictionaries, where each dictionary represents a row in the DataFrame.
    recommended_data_dict = recommended_data.to_dict('records')
    return recommended_data_dict

class MoreLikeThisView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserBook.objects.all()
    # serializer_class = serializers.NotificationsSerializer

    def get(self, request, *args, **kwargs):
        # Get the pk parameter from the URL
        user_book_id = self.kwargs.get('pk')
        user_id = request.user.id

        # check if the book exists
        user_book_qs = UserBook.objects.filter(id=user_book_id)
        if not user_book_qs.exists():
            return Response({'detail': 'The Book does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        
        data = get_recommendations(user_book_id, user_id)
        return Response(data, status=status.HTTP_200_OK)