# Django JWT 博客项目

基于 Django + JWT 认证的简单博客系统，支持文章阅读统计和缓存优化。

## 功能特性

- **JWT 认证**：使用 JWT token 进行用户认证
- **文章管理**：文章列表和详情页面
- **阅读统计**：记录文章总阅读量、唯一访客数和用户个人阅读次数
- **Redis 缓存**：使用 Redis 缓存阅读统计数据，提升性能
- **权限控制**：文章详情页需要登录才能访问

## 技术栈

- **后端**：Django 5.1.7 + Django REST Framework
- **认证**：JWT (djangorestframework-simplejwt)
- **数据库**：MySQL
- **缓存**：Redis
- **前端**：原生 HTML/CSS/JavaScript

## 项目结构

```
blog_project/
├── articles/                 # 文章应用
│   ├── models.py            # 文章和阅读记录模型
│   ├── views.py             # 视图逻辑
│   ├── views_status.py      # 阅读统计服务
│   ├── middleware.py        # JWT 认证中间件
│   └── urls.py              # URL 路由
├── templates/               # 模板文件
│   ├── login.html          # 登录页面
│   ├── article_list.html   # 文章列表页面
│   └── article_detail.html # 文章详情页面
├── blog_project/           # 项目配置
│   └── settings.py         # 项目设置
└── manage.py               # Django 管理脚本
```

## 安装部署

### 1. 环境要求

- Python 3.8+
- MySQL 5.7+
- Redis 6.0+

### 2. 安装依赖

```bash
pip install django==5.1.7
pip install djangorestframework
pip install djangorestframework-simplejwt
pip install django-redis
pip install django-cors-headers
pip install pymysql
```

### 3. 数据库配置

在 MySQL 中创建数据库：

```sql
CREATE DATABASE django_blog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

修改 `settings.py` 中的数据库配置：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_blog',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

### 4. Redis 配置

确保 Redis 服务运行在 `127.0.0.1:6379`，或修改 `settings.py` 中的 Redis 配置。

### 5. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. 创建超级用户

```bash
python manage.py createsuperuser
```

### 7. 启动服务

```bash
python manage.py runserver
```

访问 `http://127.0.0.1:8000` 即可使用。

## 使用说明

### 用户认证

1. 访问 `/login/` 进行登录
2. 登录成功后 JWT token 会存储在浏览器 localStorage 中
3. 后续请求会自动携带 token 进行认证

### 文章访问

- **文章列表**：`/articles/` - 所有用户可访问
- **文章详情**：`/articles/<id>/` - 需要登录才能访问

### 阅读统计

- 登录用户访问文章详情页会自动记录阅读次数
- 统计数据包括：总阅读量、唯一访客数、个人阅读次数
- 使用 Redis 缓存提升统计查询性能

## API 接口

### JWT 认证接口

- `POST /api/token/` - 获取 access token
- `POST /api/token/refresh/` - 刷新 token
- `POST /api/token/verify/` - 验证 token

### 请求示例

```javascript
// 登录获取 token
fetch('/api/token/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        username: 'your_username',
        password: 'your_password'
    })
})

// 访问需要认证的接口
fetch('/articles/1/', {
    headers: {
        'Authorization': `Bearer ${access_token}`
    }
})
```

## 核心特性说明

### JWT 认证中间件

自定义中间件 `JWTAuthenticationMiddleware` 自动处理 JWT token 认证，使 `request.user.is_authenticated` 能正确识别 JWT 认证的用户。

### 阅读统计缓存

`ViewStatsService` 类实现了：

- 先写缓存，异步更新数据库
- 缓存未命中时从数据库读取并回填缓存
- 使用 Redis 集合存储唯一访客数据

### 前端 JWT 处理

- 自动在请求头中携带 JWT token
- Token 过期时自动跳转到登录页
- 退出登录时清除本地存储的 token

## 开发说明

### 添加新文章和用户

```
# 在Django shell中运行
from django.contrib.auth.models import User
from articles.models import Article

# 创建测试用户
User.objects.create_user('admin', 'admin@test.com', 'admin123')
User.objects.create_user('test', 'test@test.com', 'test123')

# 创建测试文章
user = User.objects.first()
Article.objects.create(
    title='Django入门教程',
    content='这是Django的入门教程内容...',
    author=user
)
Article.objects.create(
    title='Python高级编程', 
    content='Python高级编程技巧分享...',
    author=user
)
```


### 扩展功能

- 可在 `articles/models.py` 中扩展文章模型
- 可在 `articles/views.py` 中添加新的视图
- 可在 `templates/` 中自定义页面模板

## 注意事项

- JWT token 默认有效期为 60 分钟
- Redis 缓存默认过期时间为 1 小时
- 确保 MySQL 和 Redis 服务正常运行
- 生产环境请修改 `SECRET_KEY` 并设置 `DEBUG = False`
