"""
Django settings for job_portal project.

Generated by 'django-admin startproject' using Django 5.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-(3va&-s=92973708e2m#x@n+-xvd#d$)@)&*1%e65ffga*eohm'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'spectrumjobs', # Application
    'channels', # Redis channels
    'bootstrap4', # Bootstrap4
    'notifications', # Notifications
    # Social account authentication
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # Two-factor authentication using OTP and Google mobile authenticator
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
]

# Application middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware", # Django-allauth middleware
    'django_otp.middleware.OTPMiddleware', # Django-otp middleware
]

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

""" django-allauth """
# Django-allauth: social account providers
SOCIAL_AUTH_CLIENT_ID = os.getenv('SOCIAL_AUTH_CLIENT_ID') # Get Oauth 2.0 client ID from environment variable
SOCIAL_AUTH_CLIENT_SECRET = os.getenv('SOCIAL_AUTH_CLIENT_SECRET') # Get Oauth 2.0 secret key from environment variable

SOCIALACCOUNT_PROVIDERS = {
    # Google
    'google': {
        'APP': {
            'client_id': os.environ.get('GOOGLE_OAUTH_CLIENT_ID'),
            'secret': os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET'),
            'key': ''
        }
    }
}

# Django-allauth: redirects
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/' 

# Django-allauth: site identifier
#SITE_ID=1 

""" django-otp """
# Django-otp: Authenticator application identifier
OTP_TOTP_ISSUER = 'spectrumjobs'

# Django-otp: OTP timeout and window
OTP_TOTP_VERIFY_TIMEOUT = 120  
OTP_TOTP_WINDOW = 300 

ROOT_URLCONF = 'job_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'job_portal.wsgi.application'
ASGI_APPLICATION = "job_portal.routing.application"

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Uploads
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

""" Django Channels """
# Redis channel layer backend configuration for real-time interactions
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)]
        },
    },

}

""" Celery """
# Celery broker configuration for celery.py
from celery.schedules import crontab

# Broker
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0' 

# Scheduler for monthly feedback notifications 
CELERY_BEAT_SCHEDULE = {
    'send-monthly-feedback-reminders': {
        'task': 'spectrumjobs.tasks.send_monthly_feedback_notifications',
        'schedule': crontab(day_of_month='2', hour=9, minute=0),  
        #'schedule': crontab(minute='*'),  # test scheduler every min
    },
}

""" Sessions """
# Session security policies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True 
SESSION_COOKIE_AGE = 1800  # 30 minutes session timer
SESSION_EXPIRE_AT_BROWSER_CLOSE = True # Expire session on browser closure


""" Enhanced Password Hashing """
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]