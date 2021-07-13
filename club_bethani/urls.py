from django.conf import settings
from django.conf.urls.static import static
from django.urls import base, path, include

from club_bethani import views
from django.contrib import admin

admin.site.site_header = "Bethani Book Society Administration"
admin.site.site_title = "BBC"
admin.site.index_title ="Welcome to Bethani Book Club"


urlpatterns = [

        path('borrowBooks/',views.borrowApi),
        path('borrowBooks/<int:id>',views.borrowApi), 
        path('history/',views.borrowHistoryApi),
        path('signup/',views.signUpNewUser),
        path('allbooks/', views.AllbooksPagination.as_view(),name="allbookspag"),
        path('login/', views.login,name='log'),
        path('getReader/',views.readerApi),
        path('getReader/<int:id>',views.readerApi),
        path('getBooks/<int:bookID>',views.bookApi),  
        path('getBooks/',views.bookApi),  
        path('getMyBooks/<int:ownerId>',views.getMyBooks,name="mybooks"),
        path('changePassword/',views.changePassword),

]


'''

The URLs provided by auth are:

accounts/login/ [name='login']
accounts/logout/ [name='logout']
accounts/password_change/ [name='password_change']
accounts/password_change/done/ [name='password_change_done']
accounts/password_reset/ [name='password_reset']
accounts/password_reset/done/ [name='password_reset_done']
accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
accounts/reset/done/ [name='password_reset_complete']


'''
