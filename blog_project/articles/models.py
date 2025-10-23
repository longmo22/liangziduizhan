from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Article(models.Model):
    """文章模型"""
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles', verbose_name="作者")
    title = models.CharField(max_length=200, verbose_name="文章标题")
    content = models.TextField(blank=True, null=True, verbose_name="文章内容")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    total_views = models.IntegerField(default=0, verbose_name="总阅读量")
    unique_visitors = models.IntegerField(default=0, verbose_name="唯一访客数")

    class Meta:
        db_table = 't_articles'
        verbose_name = '文章'
        verbose_name_plural = "文章"

    def __str__(self):
        return self.title

class ArticleViewRecord(models.Model):
    """文章阅读记录模型"""

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='view_records', verbose_name="文章")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    view_count = models.IntegerField(default=1, verbose_name='阅读次数')
    first_viewed = models.DateTimeField(default=timezone.now, verbose_name='首次阅读时间')
    last_viewed = models.DateTimeField(auto_now=True, verbose_name='最后阅读时间')

    class Meta:
        db_table = 't_article_view_records'
        verbose_name = '文章阅读记录'
        verbose_name_plural = '文章阅读记录'
        unique_together = ('article', 'user')  # 确保每个用户对每篇文章只有一条记录

    def __str__(self):
        return f"{self.article.title}-{self.user.username}"