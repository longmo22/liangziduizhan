from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Sum, Count
from django.contrib.auth import logout, authenticate, login
from django.http import JsonResponse
from .models import Article, ArticleViewRecord

class LoginPageView(APIView):
    """登录页面"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return render(request, 'login.html')

class LogoutView(APIView):
    """退出登录"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        logout(request)
        return redirect('article_list')

class ArticleListView(APIView):
    """文章列表页 - 完全开放"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        articles = Article.objects.all().order_by('-created_at')
        return render(request, 'article_list.html', {
            'articles': articles,
            'is_authenticated': request.user.is_authenticated
        })

class ArticleDetailView(APIView):
    """文章详情页"""
    permission_classes = [AllowAny]
    
    def get(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        
        # 只有登录用户才记录阅读
        if request.user.is_authenticated:
            self._record_view(article, request.user)
            user_view_record = article.view_records.filter(user=request.user).first()
            user_view_count = user_view_record.view_count if user_view_record else 0
        else:
            user_view_count = 0
        
        return render(request, 'article_detail.html', {
            'article': article,
            'user_view_count': user_view_count,
            'is_authenticated': request.user.is_authenticated,
            'username': request.user.username if request.user.is_authenticated else None
        })
    
    def _record_view(self, article, user):
        """记录阅读并更新统计"""
        try:
            with transaction.atomic():
                view_record, created = ArticleViewRecord.objects.get_or_create(
                    article=article,
                    user=user,
                    defaults={'view_count': 1}
                )
                
                if not created:
                    view_record.view_count += 1
                    view_record.save()
                
                # 更新文章统计
                article.total_views = ArticleViewRecord.objects.filter(
                    article=article
                ).aggregate(total=Sum('view_count'))['total'] or 0
                article.unique_visitors = ArticleViewRecord.objects.filter(
                    article=article
                ).values('user').distinct().count()
                article.save()
                
        except Exception as e:
            print(f"记录阅读错误: {e}")