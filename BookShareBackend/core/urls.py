from django.urls import path
from . import views


urlpatterns = [
    path('list/', views.BookUserList.as_view(), name='book_user_list'),
    path('recommended-for-you/', views.RecommendedForYou.as_view(), name='recommended_for_you'),
    path('top-rated/', views.TopRated.as_view(), name='top_rated'),

    path('book-search/', views.BookSearch.as_view(), name='book_search'),
    path('categories/', views.CategoriesView.as_view(), name='get_categories'),
    path('add-new/', views.AddNewBookView.as_view(), name='add_new_book'),
    path('add-edit/', views.AddEditBook.as_view(), name='add_edit_book'),
    
    path('your-library/', views.YourBooksList.as_view(), name='your_library'),
    path('your-library/<int:pk>/', views.RepostOrDelete.as_view(), name='repost_delete_book'),

    path('library/<int:pk>/', views.LibraryBooksList.as_view(), name='library_books_list'),
    path('library/<int:pk>/create-rating/', views.UserRatingCreateView.as_view(), name='library_create_rating'),
    path('library/<int:pk>/get-rating/', views.UserRatingDetailView.as_view(), name='library_get_rating'),

    path('book/<int:pk>/', views.BookDetails.as_view(), name='book_details'),
    path('book/<int:pk>/create-rating/', views.BookRatingCreateView.as_view(), name='book_create_rating'),
    path('book/<int:pk>/get-rating/', views.BookRatingDetailView.as_view(), name='book_get_rating'),
    path('book/<int:pk>/same-book/', views.SameBookView.as_view(), name='same_book'),
    path('book/<int:pk>/more-like/', views.MoreLikeThisView.as_view(), name='more_like_this'),

    path('create-notification/', views.NotificationRequest.as_view(), name='create_notification'),
    path('notifications/', views.NotificationList.as_view(), name='list_notifications'),
    path('notification-delete/<int:pk>/', views.NotificationDestroy.as_view(), name='delete_notification'),
]
