from django.urls import path
from news.apis.v1.user import UserSignUpView, UserSignInView, UserMySelfView, UserSignOutView
urlpatterns = [
path('signup/', UserSignUpView.as_view(), name='signUp'),
path('signin/', UserSignInView.as_view(), name='signIn'),
path('signout/', UserSignOutView.as_view(), name='signOut'),
path('me/', UserMySelfView.as_view(), name='me')
]