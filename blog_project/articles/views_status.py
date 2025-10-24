import threading
import logging
import threading

from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.db.models import Sum, Count

from .models import Article, ArticleViewRecord

logger = logging.getLogger(__name__)

class ViewStatsService:
    """阅读统计"""
    @staticmethod
    def record_view(article_id,user_id):
        """记录阅读 先写缓存 异步更新数据库"""
        try:
            # 生成缓存键
            user_key = f'article:{article_id}:user:{user_id}:views'
            total_key = f'article:{article_id}:total_views'
            unique_key = f'article:{article_id}:unique_visitors'

            #缓存更新用户阅读数
            user_view = cache.get(user_key,0) + 1
            cache.set(user_key,user_view,timeout=60*60)

            #缓存更新总阅读量
            total_view = cache.incr(total_key) if cache.has_key(total_key) else 1
            if total_view == 1:
                #如果是新键则设置过期时间
                cache.expire(total_key, timeout=60*60)

            # 缓存更新独立访客,集合实现
            cache.sadd(unique_key, user_id)
            cache.expire(unique_key, timeout=60*60)

            # 异步更新数据库
            ViewStatsService._delay_db_update(article_id, user_id)
            return True
    
        except Exception as e:
            logger.error(f"记录阅读失败: {e}")
            # 降级：直接写数据库
            return ViewStatsService._update_database(article_id, user_id)
        
    @staticmethod
    def _delay_db_update(article_id, user_id):
        """延迟更新数据库"""
        try:
            #通过线程模拟异步
            thread = threading.Thread(target=ViewStatsService._update_database,args=(article_id, user_id))
            thread.daemon = True #守护线程
            thread.start()

        except Exception as e:
            logger.error(f"异步更新数据库失败: {e}")
            ViewStatsService._update_database(article_id, user_id)

    @staticmethod
    def _update_database(article_id, user_id):
        """更新数据库"""
        try:
            with transaction.atomic():
                view_record,create = ArticleViewRecord.objects.get_or_create(
                    article_id=article_id,
                    user_id=user_id,
                    defaults={'view_count': 1}
                )
                if not create:
                    view_record.view_count = F('view_count') + 1 #F对象避免竞争
                    view_record.save(update_fields=['view_count'])
                
                # 更新文章总统计
                ViewStatsService._update_article_stats(article_id)
                
            return True
        except Exception as e:
            logger.error(f"数据库更新失败: {e}")
            return False
    
    @staticmethod
    def _update_article_stats(article_id):
        try:
            stats = ArticleViewRecord.objects.filter(article_id=article_id).aggregate(
                total_views=Sum('view_count'),
                unique_visitors=Count('user_id', distinct=True)
            )
            Article.objects.filter(id=article_id).update(
                total_views=stats['total_views'] or 0,
                unique_visitors=stats['unique_visitors'] or 0
            )
        except Exception as e:
            logger.error(f"更新文章统计失败: {e}")
            return False
        
    @staticmethod
    def get_article_stats(article_id):
        """获取文章统计信息"""
        try:
            #先从缓存中获取
            total_key = f'article:{article_id}:total_views'
            unique_key = f'article:{article_id}:unique_visitors'

            total_views = cache.get(total_key)
            unique_visitors = cache.scard(unique_key) if cache.has_key(unique_key) else None

            cache_hit = total_views is not None and unique_visitors is not None

            if not cache_hit:
                #缓存未命中，从数据库中获取
                article = Article.objects.get(id=article_id)
                total_views = article.total_views
                unique_visitors = article.unique_visitors

                #回填缓存
                cache.set(total_key, total_views, timeout=60*60)
                if unique_visitors > 0:
                    cache.set(unique_key, unique_visitors, 60*30)

            return {
                'total_views': total_views or 0,
                'unique_visitors': unique_visitors or 0,
                'from_cache': cache_hit
            }
            
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'total_views': 0, 'unique_visitors': 0, 'from_cache': False}
        
    @staticmethod
    def get_user_views(article_id, user_id):
        """"获取用户阅读数"""
        try:
            #查缓存
            user_key = f'article:{article_id}:user:{user_id}:views'
            cache_views = cache.get(user_key)

            if cache_views is not None:
                return int(cache_views)

            #未命中，查数据库
            view_record = ArticleViewRecord.objects.filter(
                article_id=article_id,
                user_id=user_id
            ).first()

            views = view_record.view_count if view_record else 0

            #回填
            cache.set(user_key, views, timeout=60*60)   
            
            return views
        
        except Exception as e:
            logger.error(f"获取用户阅读数失败: {e}")
            return 0
        