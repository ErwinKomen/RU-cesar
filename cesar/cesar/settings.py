"""
Django settings for cesar project.

Generated by 'django-admin startproject' using Django 1.9.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import posixpath
import socket
from django.contrib import admin

hst = socket.gethostbyname(socket.gethostname())

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_NAME = os.path.basename(BASE_DIR)
WRITABLE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../writable/database/"))
if "RU-cesar\\writable" in WRITABLE_DIR:
    # Need another string
    WRITABLE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../writable/database/"))

# Set the MEDIA_URL, which depends on the writable
MEDIA_DIR = os.path.abspath(os.path.join(WRITABLE_DIR, "../media/"))
# The MEDIA_ROOT is important for upload_to
MEDIA_ROOT = MEDIA_DIR

# Surfsara VM:
CRPP_HOME = 'http://corpus-studio-web.cttnww-meertens.surf-hosted.nl/crpp'
PROJECT_DIR = '/etc/project'

APP_PREFIX = "dd/"
ADMIN_SITE_URL = "/dd"
USE_REDIS = False
if "d:" in WRITABLE_DIR or "D:" in WRITABLE_DIR:
    APP_PREFIX = ""
    # admin.site.site_url = '/'
    ADMIN_SITE_URL = "/"
    # Ponyland: use through 8080-8080 SSH tunnel
    CRPP_HOME = 'http://localhost:8080/CrppS'
    PROJECT_DIR = '/var/www/tomcat8/live/tomcat8/crpp/project'
elif "131.174" in hst:
    # Configuration within the Radboud University environment
    APP_PREFIX = ""
    # admin.site.site_url = '/'
    ADMIN_SITE_URL = "/"
    # Ponyland-internal:
    CRPP_HOME = 'http://localhost:8080/CrppS'
    PROJECT_DIR = '/var/www/tomcat8/live/tomcat8/crpp/project'
    USE_REDIS = True
elif "/var/www" in WRITABLE_DIR:
    # New configuration of http://corpus-studio-web.cttnww-meertens.surf-hosted.nl/cesar
    APP_PREFIX = "cesar/"
    # admin.site.site_url = '/'
    ADMIN_SITE_URL = "/cesar"
else:
    # admin.site.site_url = '/dd'
    ADMIN_SITE_URL = "/dd"


# FORCE_SCRIPT_NAME = admin.site.site_url

DATA_UPLOAD_MAX_NUMBER_FIELDS = None


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '379848c4-ce15-403e-a74a-f994d720554b'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False # True
if "d:" in WRITABLE_DIR or "D:" in WRITABLE_DIR:
    DEBUG = True

# if the request URL does not match any of the patterns in the URLconf and it doesn’t end in a slash, 
#   an HTTP redirect is issued to the same URL with a slash appended.
APPEND_SLASH = True

ALLOWED_HOSTS = ['localhost', 'cesar.science.ru.nl']
BLOCKED_IPS = []

# Application definition

INSTALLED_APPS = [
    # Add your apps here to enable them
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_select2',
    # 'basic',
    'cesar.basic',
    'cesar.browser',
    'cesar.viewer',
    'cesar.seeker',
    'cesar.doc',
    'cesar.trans',
    'cesar.tsg',
    'cesar.lingo',
    'cesar.brief',
    'cesar.woord'
]

# MIDDLEWARE_CLASSES = [
MIDDLEWARE = [
    # Doesn't work on the server: 'corsheaders.middleware.CorsMiddleware',
    'cesar.utils.BlockedIpMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = True
# CORS_ALLOW_CREDENTIALS = False

ROOT_URLCONF = 'cesar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'cesar/templates')],
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

# Caching
if USE_REDIS:
    CACHES = {"default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": "redis://127.0.0.1:7778/1",
                "TIMEOUT": None,
                "OPTIONS": { "CLIENT_CLASS": "django_redis.client.DefaultClient", }
                },
                "select2": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": "redis://127.0.0.1:7778/2",
                "TIMEOUT": None,
                "OPTIONS": { "CLIENT_CLASS": "django_redis.client.DefaultClient", }
                }
            }
    # Set the cache backend to select2
    SELECT2_CACHE_BACKEND = 'select2'
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': None,
        },
        'select2': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': None,
        }
    }
    # Set the cache backend to select2
    SELECT2_CACHE_BACKEND = 'select2'

WSGI_APPLICATION = 'cesar.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(WRITABLE_DIR, 'cesar.db'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Amsterdam'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
if ("/var/www" in WRITABLE_DIR):
    STATIC_URL = "/" + APP_PREFIX + "static/"

STATIC_ROOT = os.path.abspath(os.path.join("/", posixpath.join(*(BASE_DIR.split(os.path.sep) + ['static']))))

