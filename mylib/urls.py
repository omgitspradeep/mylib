
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)




urlpatterns = [
    path('admin/', admin.site.urls),

    path('gettoken/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('refreshtoken/', TokenRefreshView.as_view(), name='token_refresh'),

    path('verifytoken/', TokenVerifyView.as_view(), name='token_verify'),

    #path to bbc app endpoints
    path('bbc/api/',include('club_bethani.urls')),

        
    path('reset_password/',auth_views.PasswordResetView.as_view(), name='reset_password'),
    path('reset_password_sent/',auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/',auth_views.PasswordResetCompleteView.as_view(),name='password_reset_complete'),
        
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)





'''

1. Check whether user exsits for given username. If yes, get the email address of that user.
2. Send Email to that user                               PasswordResetDoneView.as_view()
3. Link to password reset form in email                  PasswordResetConfirmView.as_view()
4. password successfully changed message.                PasswordResetCompletesView.as_view()


URL for change password http://127.0.0.1:8000/reset_password/

'''
