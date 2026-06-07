# E-era Member Center Backend

E-era Member Center Backend 是一个基于 Django 的会员中心与身份认证后端，提供 OAuth 登录、会员资料、身份认证申请、社团报名、审核与邮件通知等功能。

## 功能特性

- OAuth 登录与本地用户同步
- 会员资料与身份卡展示
- 身份认证申请、审核、通过与拒绝
- 社团报名申请与审核流转
- 笔试通知、Offer 通知与 Offer 确认
- Django Admin 后台管理
- MySQL 数据库存储

## 技术栈

- Python 3.10+
- Django 5.1
- Django OAuth Toolkit
- MySQL / PyMySQL
- WhiteNoise
- Bootstrap 模板页面

## 本地开发

### 1. 创建虚拟环境

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制示例文件：

```bash
copy .env.example .env
```

macOS / Linux:

```bash
cp .env.example .env
```

至少需要配置：

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `OAUTH2_CLIENT_ID`
- `OAUTH2_CLIENT_SECRET`
- `OAUTH_CALLBACK_URL`

如果需要发送邮件，还需要配置 `EMAIL_*` 相关变量。

> 不要提交 `.env` 或任何包含真实密钥、数据库密码、OAuth client secret、SMTP 密码的文件。

### 4. 初始化数据库

先创建 MySQL 数据库，然后运行：

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. 启动服务

```bash
python manage.py runserver
```

默认访问地址：[http://localhost:8000](http://localhost:8000)

也可以使用项目自带启动脚本：

```bash
python start_server.py
```

## 常用命令

```bash
python manage.py check
python manage.py migrate
python manage.py collectstatic
python manage.py runserver
```

## 项目结构

```text
eidProject/        # Django 项目配置
members/           # 会员、认证、报名业务模块
templates/         # 页面模板
manage.py          # Django 管理入口
requirements.txt   # Python 依赖
start_server.py    # 启动辅助脚本
```

## 部署注意事项

- 生产环境请设置 `DJANGO_DEBUG=false`。
- 生产环境请设置严格的 `DJANGO_ALLOWED_HOSTS` 和 `CSRF_TRUSTED_ORIGINS`。
- 使用独立数据库账号，并限制最小权限。
- 通过环境变量或密钥管理系统注入 `DJANGO_SECRET_KEY`、数据库密码、OAuth secret、SMTP 密码。
- 不要在日志中打印 access token、OAuth 返回数据或用户隐私信息。
- 建议启用 HTTPS，并正确配置安全 Cookie 与反向代理头。

## 开源安全说明

本仓库开源快照不包含真实 `.env` 文件。若你从旧私有仓库迁移而来，任何曾经提交到 Git 历史中的数据库密码、OAuth client secret、Django secret key、SMTP 密码都应视为已经泄露，请在生产环境中立即轮换。

## License

本项目基于 [Apache License 2.0](./LICENSE) 开源。
