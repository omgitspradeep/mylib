from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from club_bethani import views

urlpatterns = [
        path('getReader/',views.readerApi),
        path('getReader/<int:id>',views.readerApi),
        path('getBooks/',views.bookApi),
        path('getBooks/<int:id>',views.bookApi),  
        path('borrowBooks/',views.borrowApi),
        path('borrowBooks/<int:id>',views.borrowApi), 
        path('history/',views.borrowHistoryApi),
]
