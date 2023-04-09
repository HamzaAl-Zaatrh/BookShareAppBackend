from rest_framework import serializers
from .models import *
from user_app.serializers import UserInfoSerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class BookSerializer(serializers.ModelSerializer):
    avg_rating = serializers.StringRelatedField(source='calculate_avg_rating')
    number_rating = serializers.StringRelatedField(
        source='calculate_number_rating')
    categories_name = serializers.StringRelatedField(source='categories', many=True, read_only=True)

    class Meta:
        model = Book
        exclude = ['owners']
        extra_kwargs = {
            'categories': {'write_only': True}
        }

# use for list book
class UserBookSerializer(serializers.ModelSerializer):
    book_id = BookSerializer()
    book_owner_id = UserInfoSerializer(read_only=True)

    class Meta:
        model = UserBook
        exclude = ['borrowed_by', 'created_at', 'updated_at']


# for add new book
class BookOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBook
        exclude = ['borrowed_by', 'created_at', 'updated_at']

    def validate(self, data):
        if not data.get('book_image_url'):
            data['book_image_url'] = 'default_book.png'
        return data


class BookRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookRating
        fields = '__all__'


########################## Your Library Page Serializers ###########################
# Get Your Books
class YourBooksSerializer(serializers.ModelSerializer):
    book_id = BookSerializer()
    # To get his full name, id, and his image
    borrowed_by = UserInfoSerializer(read_only=True)

    class Meta:
        model = UserBook
        exclude = ['book_owner_id', 'created_at', 'updated_at']


############################## Library Visitor Page Serializers ##################################
class UserRatingSerializer(serializers.ModelSerializer):
    avg_rating = serializers.FloatField(
        source='user_rated_id.calculate_avg_rating', read_only=True)
    number_rating = serializers.IntegerField(
        source='user_rated_id.calculate_number_rating', read_only=True)

    class Meta:
        model = UserRating
        # fields = '__all__'
        exclude = ['id']


####################################### Book Visitor Page #########################################
class BookRatingSerializer(serializers.ModelSerializer):
    avg_rating = serializers.FloatField(
        source='book_id.calculate_avg_rating', read_only=True)
    number_rating = serializers.IntegerField(
        source='book_id.calculate_number_rating', read_only=True)

    class Meta:
        model = BookRating
        # fields = '__all__'
        exclude = ['id', 'created_at', 'updated_at']

############################## Notifications functionality ##################################

class NotificationsSerializer(serializers.ModelSerializer):
    sender_name = serializers.StringRelatedField(source='sender_id.get_full_name', read_only=True)
    receiver_name = serializers.StringRelatedField(source='receiver_id.get_full_name', read_only=True)
    book_name = serializers.StringRelatedField(source='user_book_id.book_id.book_name', read_only=True)
    time_since_created = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Notification
        exclude = ['created_at']