from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    LoginPageView, 
    LoginAPIView, 
    LogoutView, 
    ArticleListView, 
    ArticleDetailView
)

urlpatterns = [
    # JWT 认证
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('login/', LoginPageView.as_view(), name='login_page'),
    path('login-api/', LoginAPIView.as_view(), name='login_api'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('articles/', ArticleListView.as_view(), name='article_list'),
    path('articles/<int:article_id>/', ArticleDetailView.as_view(), name='article_detail'),
]