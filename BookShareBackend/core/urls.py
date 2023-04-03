from django.urls import path
from . import views


urlpatterns = [
    path('list/', views.BookUserList.as_view(), name='book_user_list'),

    path('book/', views.BookSearch.as_view(), name='book_search'),
    path('categories/', views.CategoriesView.as_view(), name='get_categories'),
    path('add-new/', views.AddNewBookView.as_view(), name='add_book'),
    
    path('your-library/', views.YourBooksList.as_view(), name='your_library'),
    path('your-library/<int:pk>/', views.RepostOrDelete.as_view(), name='repost_delete_book'),

    path('library/<int:pk>/', views.LibraryBooksList.as_view(), name='library_books_list'),
    path('library/<int:pk>/create-rating/', views.UserRatingCreateView.as_view(), name='library_create_rating'),
    path('library/<int:pk>/get-rating/', views.UserRatingDetailView.as_view(), name='library_get_rating'),
]
