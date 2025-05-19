"""
Настройки Django для контейнера Docker
"""

import os
from .settings import *

# Отключаем отладку в продакшене
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Настройки базы данных SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Настройки статических файлов
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Настройки логирования для контейнера
log_dir = '/app/logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)
LOGGING['handlers']['file']['filename'] = os.path.join(log_dir, 'debug.log')

# Настройки безопасности
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8001',
    'http://127.0.0.1:8001',
    'http://0.0.0.0:8001',
] 