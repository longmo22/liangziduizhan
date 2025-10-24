from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.core.cache import cache

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Article, ArticleViewRecord
from .views_status import ViewStatsService

class LoginPageView(APIView):
    """登录页面"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return render(request, 'login.html')

class LogoutView(APIView):
    """退出登录"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return JsonResponse({'success': True})

class ArticleListView(APIView):
    """文章列表页"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        #查询所有文章并返回
        articles = Article.objects.all().order_by('-created_at')
        return render(request, 'article_list.html', {
            'articles': articles,
            'is_authenticated': request.user.is_authenticated
        })

class ArticleDetailView(APIView):
    """文章详情页"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        
        # 只有登录用户才记录阅读
        if request.user.is_authenticated:
            """没加缓存版本"""
            #记录用户阅读行为
            # self._record_view(article, request.user)
            # 查询当前用户对该文章的阅读记录
            # user_view_record = article.view_records.filter(user=request.user).first()
            # 获取用户的阅读次数，如果没有记录则为0
            # user_view_count = user_view_record.view_count if user_view_record else 0

            """加缓存版本"""
            ViewStatsService.record_view(article_id, request.user.id)
            user_view_count = ViewStatsService.get_user_views(article_id, request.user.id)

        else:
            user_view_count = 0
        
        # 获取文章统计
        stats = ViewStatsService.get_article_stats(article_id)

        return render(request, 'article_detail.html', {
            'article': article,
            'user_view_count': user_view_count,
            'total_views': stats['total_views'],
            'unique_visitors': stats['unique_visitors'],
            'is_authenticated': request.user.is_authenticated,
            'username': request.user.username if request.user.is_authenticated else None
        })
    
    def _record_view(self, article, user):
        """记录阅读并更新统计"""
        try:
            with transaction.atomic():
            # 使用事务确保数据操作的原子性
                # 如果记录不存在则创建并设置view_count为1，如果存在则返回现有记录
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


# class ArticleStatsView(APIView):
#     """文章统计API"""
#     permission_classes = [AllowAny]
    
#     def get(self, request, article_id):
#         """获取文章统计信息"""
#         stats = ViewStatsService.get_article_stats(article_id)
        
#         return JsonResponse({
#             'article_id': article_id,
#             'total_views': stats['total_views'],
#             'from_cache': stats['from_cache'],
#             'cache_hit_rate': ViewStatsService.get_cache_hit_rate()
#         })