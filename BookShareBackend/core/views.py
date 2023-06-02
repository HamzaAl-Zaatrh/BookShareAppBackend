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
from django.db.models import Count, Avg
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


class BookGeneralDetails(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Book.objects.all()
    serializer_class = serializers.BookSerializer

################################### add a book page 2 (new) ##########################################


class AddNewBookView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.BookSerializer

    def post(self, request, *args, **kwargs):

        book_serializer = self.get_serializer(data=request.data)
        book_serializer.is_valid(raise_exception=True)

        # Convert comma-separated string to list of integers
        book = book_serializer.save(
            categories=request.data.get('categories', []).split(','))

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
        book_rating_data = {
            'book_id': book.id,
            'book_rater_id': request.user.id,
            'book_rating': request.data.get('rating', 0)
        }

        book_rating_serializer = serializers.BookRatingSerializer(
            data=book_rating_data)
        book_rating_serializer.is_valid(raise_exception=True)
        book_rating_serializer.save()

        return Response({'detail': 'The book was added successfully.'}, status=status.HTTP_201_CREATED)


class AddEditBook(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user_id = request.user.id
        book_id = request.data.get('book_id')
        rating = request.data.get('rating')

        # First we check if the book has rating or not
        book_rating_qs = BookRating.objects.filter(
            book_id=book_id, book_rater_id=user_id)
        if rating:
            if book_rating_qs.exists():
                book_rating = book_rating_qs.first()
                book_rating.book_rating = rating
                book_rating.save()
            else:
                # Create BookRating object
                book_rating_data = {
                    'book_id': book_id,
                    'book_rater_id': user_id,
                    'book_rating': rating
                }
                rating_serializer = serializers.BookRatingSerializer(
                    data=book_rating_data)
                rating_serializer.is_valid(raise_exception=True)
                rating_serializer.save()

        # check if a userbook exists or not
        # if it exists we will edit
        # You can delete the image field from the request if you don't want to change the image
        image = request.FILES.get('image')
        add_flag = True
        user_book_qs = UserBook.objects.filter(
            book_id=book_id, book_owner_id=user_id)
        if user_book_qs.exists():
            add_flag = False
            user_book = user_book_qs.first()
            if image:
                user_book.book_image_url = image
                user_book.save()
            # If you want to delete the image
            del_image = request.data.get('del_image')
            if del_image:
                user_book.book_image_url = 'default_book.png'
                user_book.save()
        else:
            # Create UserBook object for the book owner
            user_book_data = {
                'book_owner_id': user_id,
                'book_id': book_id,
                'book_image_url': image,
                'status': True
            }
            user_book_serializer = serializers.BookOwnerSerializer(
                data=user_book_data)
            user_book_serializer.is_valid(raise_exception=True)
            user_book_serializer.save()

        # Edit the Book information
        book = Book.objects.get(id=book_id)
        book.book_name = request.data.get('book_name')
        book.author = request.data.get('author')
        book.publisher = request.data.get('publisher')
        book.description = request.data.get('description')
        book.year = request.data.get('year')
        book.ISBN = request.data.get('ISBN')

        category_ids = request.data.get('categories').split(
            ',')  # split string into list of ids
        # convert each id to an integer
        category_ids = [int(id.strip()) for id in category_ids]
        book.categories.set(category_ids)  # set the categories for the book
        book.save()

        # add_flag = request.data.get('add_flag')
        detail = {}
        if add_flag:
            detail = {'detail': 'The Book has been added successfully.'}
        else:
            detail = {'detail': 'The Book has been edited successfully.'}

        return Response(detail, status=status.HTTP_200_OK)


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

        if not(type == 'borrow_request'):
            # Delete the borrow request notification
            notification = Notification.objects.filter(id = request.data.get('notification_id'))
            notification.first().delete()

        return Response({'detail': 'The notification has been sent successfully.'}, status=status.HTTP_201_CREATED)
        # return Response(notification_serializer.data, status=status.HTTP_201_CREATED)


class NotificationList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()
    serializer_class = serializers.NotificationsSerializer

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(receiver_id=user)


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

# version 1.0
def get_recommendations(id, user_id):
    # Load UserBooks into a DataFrame
    user_books = pd.DataFrame.from_records(UserBook.objects.all().values(
        'id', 'book_owner_id', 'book_id', 'book_id__book_name', 'book_id__author', 'book_id__categories__category', 'book_image_url'))

    ratings_df = pd.DataFrame.from_records(BookRating.objects.all().values())

    # get all the books rated by this user as a list
    rated_books = ratings_df.loc[ratings_df['book_rater_id_id']
                                 == user_id, 'book_id_id'].tolist()

    user_books['book_image_url'] = user_books['book_image_url'].apply(
        lambda x: 'http://127.0.0.1:8000/media/' + x)

    # Renaming the columns
    user_books = user_books.rename(columns={
        'id': 'user_book_id',
        'book_id__book_name': 'book_name',
        'book_owner_id': 'owner_id',
        'book_id__author': 'author',
        'book_id__categories__category': 'categories__category',
        'book_image_url': 'image_url'
    })

    # Grouping the data (Grouping categories)
    # lambda function uses the filter() function
    # to remove any None values from the set before joining the remaining values with ', '.
    data = user_books.groupby('user_book_id').agg({
        'book_id': 'first',
        'owner_id': 'first',
        'book_name': 'first',
        'author': 'first',
        'categories__category': lambda x: ', '.join(set(filter(None, x))),
        'image_url': 'first'
    }).reset_index()

    # get all the books owned by this user as a list
    owned_books = data.loc[data['owner_id'] == user_id, 'book_id'].tolist()

    cleaned_data = data.copy()

    # Function to convert all strings to lower case and strip names of spaces
    def clean_data(x):
        # Check if auther exists. If not, return empty string
        if isinstance(x, str):
            out = str.lower(x.replace(" ", ""))
            output_string = out.replace(',', ' ')
            return output_string
        else:
            return ''

    # Apply clean_data function to your features.
    features = ['author', 'categories__category']

    for feature in features:
        cleaned_data[feature] = cleaned_data[feature].apply(clean_data)

    def create_metadata(x):
        return x['author'] + ' ' + x['categories__category']
    cleaned_data['metadata'] = cleaned_data.apply(create_metadata, axis=1)

    count = CountVectorizer(stop_words='english')
    count_matrix = count.fit_transform(cleaned_data['metadata'])

    cosine_sim = cosine_similarity(count_matrix, count_matrix)

    print(data)
    print(cosine_sim)

    index = data.index[data['user_book_id'] == id][0]
    same_book_id = data[data['user_book_id'] == id]['book_id'].iloc[0]

    similarity_series = pd.Series(
        cosine_sim[index]).sort_values(ascending=False)
    list_index = similarity_series[similarity_series > 0.3].index.tolist()

    recommended_data = data.iloc[list_index]

    # drop the same books
    recommended_data = recommended_data[~(
        recommended_data['book_id'] == same_book_id)]

    # drop all books that owned by this user
    recommended_data = recommended_data[~recommended_data['book_id'].isin(
        owned_books)]

    # drop all books that rated by this user
    recommended_data = recommended_data[~recommended_data['book_id'].isin(
        rated_books)]

    # drop duplicate books
    recommended_data.drop_duplicates(['book_id'], keep='last', inplace=True)

    # get only first 10 books
    if recommended_data.shape[0] > 10:
        recommended_data = recommended_data[:10]

    # convert dataframe to dictionary
    # We used the 'records' option in the to_dict() method
    # to convert the DataFrame to a list of dictionaries, where each dictionary represents a row in the DataFrame.
    recommended_data_dict = recommended_data.to_dict('records')
    return recommended_data_dict


class MoreLikeThisView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserBook.objects.all()

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


class RecommendedForYou(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserBook.objects.all()

    def get(self, request, *args, **kwargs):
        user_id = request.user.id

        # We use "order_by('?')" to randomly order the books and only the first 5 books are selected
        rated_books = BookRating.objects.filter(
            book_rater_id=user_id, book_rating__gt=6).order_by('?')[:5]

        if rated_books.count() == 0:
            return Response({'detail': "You need to rate more books to get our Recommendations."}, status=status.HTTP_404_NOT_FOUND)
            # return Response({'detail': "You need to rate at least 5 books to get our Recommendations."}, status=status.HTTP_404_NOT_FOUND)

        # List of dictionaries
        data = []
        for rated_book in rated_books:
            # get the id of the book
            book_id = rated_book.book_id
            user_book = UserBook.objects.filter(book_id=book_id).first()

            if user_book:
                user_book_id = user_book.id
                # check if there are any recommendations for this book
                recommendations = get_recommendations(user_book_id, user_id)
                if recommendations:
                    for recommendation in recommendations[0:2]:
                        data.append(recommendation)

        if not data:
            return Response({'detail': "We're sorry, but we don't have any book recommendations for you yet."}, status=status.HTTP_404_NOT_FOUND)

        # drop the duplicate books
        df = pd.DataFrame(data)
        df.drop_duplicates(['book_id'], keep='first', inplace=True)
        data = df.to_dict('records')

        return Response(data, status=status.HTTP_200_OK)


class TopRated(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Calculate the average rating and number of ratings for each book
        books = Book.objects.annotate(
            avg_rating=Avg('bookrating__book_rating'),
            num_ratings=Count('bookrating')
        ).values('id', 'book_name', 'avg_rating', 'num_ratings', 'categories__category')

        books_df = pd.DataFrame.from_records(books)

        books_df = books_df.groupby('id').agg({
            'book_name': 'first',
            'avg_rating': 'first',
            'num_ratings': 'first',
            'categories__category': lambda x: ', '.join(set(filter(None, x)))
        }).reset_index()

        # C is the mean rate across the whole books list
        C = books_df['avg_rating'].mean()
        # m is the minimum rates required to be listed in the chart
        # In other words, for a book to feature in the charts, it must have more rates than at least 90% of the books in the list.
        m = books_df['num_ratings'].quantile(0.9)
        # We filter out the books that qualify for the chart
        q_books = books_df.copy().loc[books_df['num_ratings'] >= m]

        def weighted_rating(x, m=m, C=C):
            v = x['num_ratings']
            R = x['avg_rating']
            # Calculation based on the IMDB formula
            return (v/(v+m) * R) + (m/(m+v) * C)

        # Define a new feature 'score' and calculate its value with `weighted_rating()`
        q_books['score'] = q_books.apply(weighted_rating, axis=1)
        # Sort movies based on score calculated above
        q_books = q_books.sort_values('score', ascending=False)[:10]

        def get_user_book_id(row):
            userbook = UserBook.objects.filter(book_id=row['id']).first()
            return userbook.id

        def get_image(row):
            userbook = UserBook.objects.filter(book_id=row['id']).first()
            return 'http://127.0.0.1:8000' + userbook.book_image_url.url

        q_books['user_book_id'] = q_books.apply(get_user_book_id, axis=1)
        q_books['image_url'] = q_books.apply(get_image, axis=1)

        q_books_dict = q_books.to_dict('records')
        return Response(q_books_dict, status=status.HTTP_200_OK)
