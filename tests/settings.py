"""Offline Django tests: isolated SQLite, fake mail settings, no production .env."""

from pathlib import Path

SECRET_KEY = 'offline-club-mail-regression-tests'
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'members',
]
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
ROOT_URLCONF = 'tests.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'OPTIONS': {'loaders': [
        ('django.template.loaders.locmem.Loader', {
            'base.html': '{% block content %}{% endblock %}',
        }),
        ('django.template.loaders.filesystem.Loader', [str(Path(__file__).resolve().parent.parent / 'templates')]),
    ]},
}]
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
TIME_ZONE = 'Asia/Shanghai'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.invalid'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = 'sender@example.invalid'
OFFER_CONFIRM_BASE_URL = 'https://neweid.example.invalid'
WECOM_WEBHOOK_URL = ''
FEISHU_WEBHOOK_URL = ''
NOTIFY_WEBHOOK_URLS = ''
WECOM_BRIEF_WEBHOOK_URL = ''

