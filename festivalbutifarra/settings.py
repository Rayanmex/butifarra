# Forzar el uso de pysqlite3 en lugar del sqlite3 del sistema
# (necesario en servidores con SQLite antiguo, como AlmaLinux 8)
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    # En Windows no existe pysqlite3, pero tampoco hace falta.
    pass

from pathlib import Path
import os



BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================
#  SEGURIDAD
# =============================================================

# SECRET_KEY: se lee de variable de entorno si existe.
# En producción (servidor), se define DJANGO_SECRET_KEY en /etc/systemd/system/butifarra.service
# En desarrollo, usa el fallback.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-cambia-esta-clave-en-produccion'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'chatbot-sigef.tabasco.gob.mx',
    'www.chatbot-sigef.tabasco.gob.mx',
    '127.0.0.1',
    'localhost',
]

# Necesario para que los formularios funcionen por HTTPS
CSRF_TRUSTED_ORIGINS = [
    'http://chatbot-sigef.tabasco.gob.mx',
    'https://chatbot-sigef.tabasco.gob.mx',
]

# Cookies seguras (solo en producción con HTTPS)
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Descomentar cuando HTTPS esté 100% funcionando:
    # SECURE_SSL_REDIRECT = True

# =============================================================
#  APLICACIONES
# =============================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'festivalbutifarra.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'festivalbutifarra.wsgi.application'

# =============================================================
#  BASE DE DATOS
# =============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# =============================================================
#  CONTRASEÑAS
# =============================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================================
#  INTERNACIONALIZACIÓN
# =============================================================

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# =============================================================
#  ARCHIVOS ESTÁTICOS Y MEDIA
# =============================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================
#  OTROS
# =============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard_redirect'
LOGOUT_REDIRECT_URL = 'accounts:login'