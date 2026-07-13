from django.urls import path
from news.apis.v1.user import UserSignInView, UserMySelfView, UserSignOutView
urlpatterns = [
path('signin/', UserSignInView.as_view(), name='signIn'),
path('signout/', UserSignOutView.as_view(), name='signOut'),
path('me/', UserMySelfView.as_view(), name='me')
]