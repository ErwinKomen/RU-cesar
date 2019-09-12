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
WRITABLE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../writable/database/"))
if "RU-cesar\\writable" in WRITABLE_DIR:
    # Need another string
    WRITABLE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../../writable/database/"))

# Surfsara VM:
CRPP_HOME = 'http://corpus-studio-web.cttnww-meertens.surf-hosted.nl/crpp'
PROJECT_DIR = '/etc/project'

APP_PREFIX = "dd/"
if "d:" in WRITABLE_DIR or "D:" in WRITABLE_DIR:
    APP_PREFIX = ""
    admin.site.site_url = '/'
    # Ponyland: use through 8080-8080 SSH tunnel
    CRPP_HOME = 'http://localhost:8080/CrppS'
    PROJECT_DIR = '/var/www/tomcat8/live/tomcat8/crpp/project'
elif "131.174" in hst:
    # Configuration within the Radboud University environment
    APP_PREFIX = ""
    admin.site.site_url = '/'
    # Ponyland-internal:
    CRPP_HOME = 'http://localhost:8080/CrppS'
    PROJECT_DIR = '/var/www/tomcat8/live/tomcat8/crpp/project'
elif "/var/www" in WRITABLE_DIR:
    # New configuration of http://corpus-studio-web.cttnww-meertens.surf-hosted.nl/cesar
    APP_PREFIX = "cesar/"
    admin.site.site_url = '/cesar'
else:
    admin.site.site_url = '/dd'

FORCE_SCRIPT_NAME = admin.site.site_url

DATA_UPLOAD_MAX_NUMBER_FIELDS = None


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '379848c4-ce15-403e-a74a-f994d720554b'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', 'cesar.science.ru.nl', 'corpus-studio-web.cttnww-meertens.surf-hosted.nl']

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
    'cesar.browser',
    'cesar.viewer',
    'cesar.seeker',
    'cesar.doc',
    'cesar.tsg',
    'cesar.lingo'
]

# MIDDLEWARE_CLASSES = [
MIDDLEWARE = [
    # Doesn't work on the server: 'corsheaders.middleware.CorsMiddleware',
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
