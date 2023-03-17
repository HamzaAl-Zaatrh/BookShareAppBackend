from django.contrib import admin
from .models import *

admin.site.register(Book)
admin.site.register(Category)
admin.site.register(BookRating)
admin.site.register(UserRating)
admin.site.register(Notification)
admin.site.register(UserBook)
