# articles/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.db.models import Sum, Count
import json
import requests
from .models import Article, ArticleViewRecord

class LoginPageView(APIView):
    """登录页面"""
    permission_classes = [AllowAny]  # 允许任何人访问
    
    def get(self, request):
        return render(request, 'login.html')

class LoginAPIView(APIView):
    """处理登录请求"""
    permission_classes = [AllowAny]
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            # 调用 JWT 认证接口
            response = requests.post(
                'http://localhost:8000/api/token/',
                data={'username': username, 'password': password}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                # 将 token 存储到 session
                request.session['access_token'] = token_data['access']
                request.session['refresh_token'] = token_data['refresh']
                return Response({'success': True})
            else:
                return Response({'success': False, 'error': '用户名或密码错误'})
                
        except Exception as e:
            return Response({'success': False, 'error': '登录失败'})

class LogoutView(APIView):
    """退出登录"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        request.session.flush()
        return redirect('article_list')

class ArticleListView(APIView):
    """文章列表页 - 无需登录即可查看"""
    permission_classes = [AllowAny]  # 允许任何人访问
    
    def get(self, request):
        articles = Article.objects.all().order_by('-created_at')
        return render(request, 'article_list.html', {
            'articles': articles,
            'has_token': 'access_token' in request.session
        })

class ArticleDetailView(APIView):
    """文章详情页 - 需要登录才能记录阅读"""
    permission_classes = [AllowAny]  # 允许任何人访问，但我们会手动检查登录状态
    
    def get(self, request, article_id):
        # 检查是否已登录
        if 'access_token' not in request.session:
            return render(request, 'login_prompt.html', {
                'message': '请先登录才能查看文章详情和记录阅读',
                'redirect_url': f'/articles/{article_id}/'
            })
        
        # 获取文章
        article = get_object_or_404(Article, id=article_id)
        
        # 记录阅读（只有登录用户才记录）
        self._record_view(article, request.user)
        
        # 获取用户的阅读次数
        user_view_record = article.view_records.filter(user=request.user).first()
        user_view_count = user_view_record.view_count if user_view_record else 0
        
        return render(request, 'article_detail.html', {
            'article': article,
            'user_view_count': user_view_count
        })
    
    def _record_view(self, article, user):
        """记录阅读并更新统计"""
        try:
            with transaction.atomic():
                # 更新阅读记录
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