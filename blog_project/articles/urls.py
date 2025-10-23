from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .views import LoginPageView, LogoutView, ArticleListView, ArticleDetailView

urlpatterns = [
    
    path('', LoginPageView.as_view(), name='home'),
    
    path('login/', LoginPageView.as_view(), name='login_page'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('articles/', ArticleListView.as_view(), name='article_list'),
    path('articles/<int:article_id>/', ArticleDetailView.as_view(), name='article_detail'),
    
    # JWT认证接口
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]