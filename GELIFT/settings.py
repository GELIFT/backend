"""
Django settings for GELIFT project.

Generated by 'django-admin startproject' using Django 2.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'sbjusvd3re$q@b@o)7k*0@vr_-^!6(md@kzw(#q%3^4g16&l5g'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Application definition

# ----------- CHANGE VALUES HERE -----------------------------

ALLOWED_HOSTS = ['gelift.win.tue.nl']
GMAPS_API_KEY = "AIzaSyA88aymL5Qn5RhVAjCXanY_xjl4KhqfDFQ"
FIREBASE_KEY = "AAAAA9nkfCE:APA91bEpXyMrPIrR23E2zBkyHD5Ei5zymrI4Sd_dTgogkQOV1RAQ4ov1yp4RfzBeB0wR5aJL5JEmjbdlGuyA-tr92arV2tlmzIRiy3YfBLLrzMOzPfdvJXoa5KJzciHYJNCFt20-4m_l"
STATICFILES_DIRS = [
    '/srv/http/gelift/static/'
]
# Do not forget the "/" at the end of URL, MEDIA_ROOT and MEDIA_URL
URL = 'https://gelift.win.tue.nl/'
MEDIA_ROOT = '/srv/http/gelift/static/media/'
MEDIA_URL = 'static/media/'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'gelift',
        'USER': 'gelift',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': ''
    }
}

# Email settings
EMAIL_USE_TLS = False
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.tue.nl'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = "noreply@gelift.win.tue.nl"

# ---------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'backend',
    'rest_framework',
    'rest_framework.authtoken',
    'webapp',
    'fcm_django',
    'coverage',
    'django_extensions',
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

ROOT_URLCONF = 'GELIFT.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
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

WSGI_APPLICATION = 'GELIFT.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Amsterdam'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Firebase django settings
FCM_DJANGO_SETTINGS = {
    "FCM_SERVER_KEY": FIREBASE_KEY,
    "ONE_DEVICE_PER_USER": False,
    "DELETE_INACTIVE_DEVICES": False
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '/static/')

# Custom User model
AUTH_USER_MODEL = 'webapp.User'

# Django admin status
ADMIN_ENABLED = True

# REST framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser'
    )
}

# Page where the webapp will redirect after login
LOGIN_REDIRECT_URL = '/admin/dashboard/'

TIME_INPUT_FORMATS = [
    '%H:%M:%S',  # 00:00:00
    '%H:%M:%S.%f',  # 00:00:00.000000
    '%H:%M',  # 00:00
]