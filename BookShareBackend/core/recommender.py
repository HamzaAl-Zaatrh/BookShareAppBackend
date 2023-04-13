from .models import *
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from user_app.models import User





## version 1.0
def get_recommendations(id, user_id):
    # Load UserBooks into a DataFrame
    user_books = pd.DataFrame.from_records(UserBook.objects.all().values(
        'id', 'book_owner_id', 'book_id', 'book_id__book_name', 'book_id__author', 'book_id__categories__category', 'book_image_url'))
    
    ratings_df = pd.DataFrame.from_records(BookRating.objects.all().values())

    # get all the books rated by this user as a list
    rated_books = ratings_df.loc[ratings_df['book_rater_id_id'] == user_id, 'book_id_id'].tolist()
    
    user_books['book_image_url'] = user_books['book_image_url'].apply(lambda x: 'http://127.0.0.1:8000/media/' + x)

    # Renaming the columns
    user_books = user_books.rename(columns={
        'book_id__book_name': 'title',
        'book_owner_id': 'owner_id',
        'book_id__author': 'author',
        'book_id__categories__category': 'genres',
        'book_image_url': 'image'
    })

    # Grouping the data (Grouping categories)
    # lambda function uses the filter() function 
    # to remove any None values from the set before joining the remaining values with ', '.
    data = user_books.groupby('id').agg({
        'book_id': 'first',
        'owner_id': 'first',
        'title': 'first',
        'author': 'first',
        'genres': lambda x: ', '.join(set(filter(None, x))),
        'image': 'first'
    }).reset_index()

    # get all the books owned by this user as a list
    owned_books = data.loc[data['owner_id'] == user_id, 'book_id'].tolist()

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
    same_book_id = data[data['id'] == id]['book_id'].iloc[0]

    similarity_series = pd.Series(cosine_sim[index]).sort_values(ascending=False)
    list_index = similarity_series[similarity_series > 0.3].index.tolist()

    recommended_data = data.iloc[list_index]

    # drop the same books
    recommended_data = recommended_data[~(recommended_data['book_id']==same_book_id)]

    # drop all books that owned by this user
    recommended_data = recommended_data[~recommended_data['book_id'].isin(owned_books)]

    # drop all books that rated by this user
    recommended_data = recommended_data[~recommended_data['book_id'].isin(rated_books)]
    
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

print(get_recommendations(1, 4))

### Beta version
# def get_recommendations(id, user_id):
#     # Load UserBooks into a DataFrame
#     user_books = pd.DataFrame.from_records(UserBook.objects.all().values(
#         'id', 'book_owner_id', 'book_id', 'book_id__book_name', 'book_id__author', 'book_id__categories__category', 'book_image_url'))
#     ratings_df = pd.DataFrame.from_records(BookRating.objects.all().values())

#     book_rater_id = user_id # set the book_rater_id_id that you want to filter by
#     # get all the books rated by this user as a list
#     rated_books = ratings_df.loc[ratings_df['book_rater_id_id'] == book_rater_id, 'book_id_id'].tolist()
#     print(rated_books)
    
#     user_books['book_image_url'] = user_books['book_image_url'].apply(lambda x: 'http://127.0.0.1:8000/media/' + x)

#     # Renaming the columns
#     user_books = user_books.rename(columns={
#         'book_id__book_name': 'title',
#         'book_owner_id': 'owner_id',
#         'book_id__author': 'author',
#         'book_id__categories__category': 'genres',
#         'book_image_url': 'image'
#     })

#     if not user_books[(user_books['owner_id'] == user_id) & (user_books['id'] == id)].empty:
#         return {'detail': 'Bad request, this book is owned by this user'}
#         # return Response({'detail': 'Bad request, this book is owned by this user'}, status=status.HTTP_400_BAD_REQUEST)



#     # drop all books that owned by this user
#     # user_books = user_books.drop(user_books[user_books['owner_id'] == user_id].index)

#     # # drop all books that rated by this user
#     # user_books = user_books[~user_books['book_id'].isin(rated_books)]

#     # Grouping the data and drop duplicates
#     data = user_books.groupby('id').agg({
#         'book_id': 'first',
#         'owner_id': 'first',
#         'title': 'first',
#         'author': 'first',
#         'genres': lambda x: ', '.join(set(x)),
#         'image': 'first'
#     }).drop_duplicates(['book_id'], keep='last').reset_index()

#     cleaned_data = data.copy()

#     # Function to convert all strings to lower case and strip names of spaces
#     def clean_data(x):
#         #Check if director exists. If not, return empty string
#         if isinstance(x, str):
#             out = str.lower(x.replace(" ", ""))
#             output_string = out.replace(',', ' ')
#             return output_string
#         else:
#             return ''
            
#     # Apply clean_data function to your features.
#     features = ['author', 'genres']

#     for feature in features:
#         cleaned_data[feature] = cleaned_data[feature].apply(clean_data)

#     def create_metadata(x):
#         return x['author'] + ' ' + x['genres']
#     cleaned_data['metadata'] = cleaned_data.apply(create_metadata, axis=1)

#     count = CountVectorizer(stop_words='english')
#     count_matrix = count.fit_transform(cleaned_data['metadata'])

#     cosine_sim = cosine_similarity(count_matrix, count_matrix)

#     print(data)
#     print(cosine_sim)

#     index = data.index[data['id'] == id][0]

#     similarity_series = pd.Series(cosine_sim[index]).sort_values(ascending=False)
#     list_index = similarity_series[similarity_series > 0.3].index.tolist()

#     list_index.remove(index)
#     recommended_data = []
#     if len(list_index) <= 10:
#         recommended_data = data.iloc[list_index]
#     else:
#         recommended_data = data.iloc[list_index[:10]]

#     # drop all books that owned by this user
#     recommended_data = recommended_data.drop(recommended_data[recommended_data['owner_id'] == user_id].index)

#     # drop all books that rated by this user
#     recommended_data = recommended_data[~recommended_data['book_id'].isin(rated_books)]


#     # convert dataframe to dictionary
#     # We used the 'records' option in the to_dict() method 
#     # to convert the DataFrame to a list of dictionaries, where each dictionary represents a row in the DataFrame.
#     recommended_data_dict = recommended_data.to_dict('records')
#     return recommended_data_dict