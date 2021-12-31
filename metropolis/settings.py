"""
Django settings for metropolis project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "Change me"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.flatpages",
    "core",
    "allauth",
    "allauth.account",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "martor",
    "django_select2",
    "pwa",
    # SSO (OAuth)
    "oauth2_provider",
    # GraphQL
    "graphene_django",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
    "core.middleware.TimezoneMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
]

ROOT_URLCONF = "metropolis.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "metropolis.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Cache

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Auth settings

AUTH_USER_MODEL = "core.User"

# Media settings

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

# Timetable settings

TIMETABLE_FORMATS = {
    "pre-2020": {
        "schedules": {
            "default": [
                {
                    "description": {
                        "time": "08:45 AM - 10:05 AM",
                        "course": "Period 1",
                    },
                    "time": [[8, 45], [10, 5]],
                    "position": [{1}, {1}],
                },
                {
                    "description": {
                        "time": "10:15 AM - 11:30 AM",
                        "course": "Period 2",
                    },
                    "time": [[10, 15], [11, 30]],
                    "position": [{2}, {2}],
                },
                {
                    "description": {
                        "time": "12:30 PM - 01:45 PM",
                        "course": "Period 3",
                    },
                    "time": [[12, 30], [13, 45]],
                    "position": [{3}, {4}],
                },
                {
                    "description": {
                        "time": "01:50 PM - 03:05 PM",
                        "course": "Period 4",
                    },
                    "time": [[13, 50], [15, 5]],
                    "position": [{4}, {3}],
                },
            ]
        },
        "courses": 4,
        "positions": {1, 2, 3, 4},
        "cycle": {
            "length": 2,
            "duration": "day",
        },
        "question": {
            "prompt": "Your Nth course on day 1 is this course. N = ?",
            "choices": [
                (1, 1),
                (2, 2),
                (3, 3),
                (4, 4),
            ],
        },
    },
    "covid": {
        "schedules": {
            "default": [
                {
                    "description": {
                        "time": "08:45 AM - 12:30 PM (In person)",
                        "course": "Morning Class",
                    },
                    "time": [[8, 45], [12, 30]],
                    "position": [{1}, {2}, {3}, {4}],
                },
                {
                    "description": {
                        "time": "08:45 AM - 12:30 PM (At home)",
                        "course": "Morning Class",
                    },
                    "time": [[8, 45], [12, 30]],
                    "position": [{2}, {1}, {4}, {3}],
                },
                {
                    "description": {
                        "time": "02:00 PM - 03:15 PM (At home)",
                        "course": "Afternoon Class",
                    },
                    "time": [[14, 0], [15, 15]],
                    "position": [{3, 4}, {3, 4}, {1, 2}, {1, 2}],
                },
            ],
        },
        "courses": 2,
        "positions": {1, 2, 3, 4},
        "cycle": {
            "length": 4,
            "duration": "day",
        },
        "question": {
            "prompt": "On which day are you in person for this course?",
            "choices": [
                (1, 1),
                (2, 2),
                (3, 3),
                (4, 4),
            ],
        },
    },
    "week": {
        "schedules": {
            "default": [
                {
                    "description": {
                        "time": "09:00 AM - 11:30 AM",
                        "course": "Morning Class",
                    },
                    "time": [[9, 0], [11, 30]],
                    "position": [{1, 5, 7}, {3, 6, 7}],
                },
                {
                    "description": {
                        "time": "12:15 PM - 02:45 PM",
                        "course": "Afternoon Class",
                    },
                    "time": [[12, 15], [14, 45]],
                    "position": [{2, 5, 7}, {4, 6, 7}],
                },
            ],
            "late-start": [
                {
                    "description": {
                        "time": "10:00 AM - 12:00 PM",
                        "course": "Morning Class",
                    },
                    "time": [[10, 0], [12, 0]],
                    "position": [{1, 5, 7}, {3, 6, 7}],
                },
                {
                    "description": {
                        "time": "12:45 PM - 02:45 PM",
                        "course": "Afternoon Class",
                    },
                    "time": [[12, 45], [14, 45]],
                    "position": [{2, 5, 7}, {4, 6, 7}],
                },
            ],
            "early-dismissal": [
                {
                    "description": {
                        "time": "09:00 AM - 10:14 AM",
                        "course": "Morning Class",
                    },
                    "time": [[9, 0], [10, 14]],
                    "position": [{1, 5, 7}, {3, 6, 7}],
                },
                {
                    "description": {
                        "time": "10:16 AM - 11:30 AM",
                        "course": "Afternoon Class",
                    },
                    "time": [[10, 16], [11, 30]],
                    "position": [{2, 5, 7}, {4, 6, 7}],
                },
            ],
        },
        "courses": 4,
        "positions": {1, 2, 3, 4, 5, 6, 7},
        "cycle": {
            "length": 2,
            "duration": "week",
        },
        "question": {
            "prompt": "When do you have class for this course?",
            "choices": [
                (1, "Week 1 Morning"),
                (2, "Week 1 Afternoon"),
                (3, "Week 2 Morning"),
                (4, "Week 2 Afternoon"),
                (5, "This course is a 2-credit Co-op in Week 1."),
                (6, "This course is a 2-credit Co-op in Week 2."),
                (7, "This course is a 4-credit Co-op."),
            ],
        },
    },
}

# Authentication settings

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "username"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_FORMS = {
    "login": "allauth.account.forms.LoginForm",
    "signup": "core.forms.MetropolisSignupForm",
    "add_email": "allauth.account.forms.AddEmailForm",
    "change_password": "allauth.account.forms.ChangePasswordForm",
    "set_password": "allauth.account.forms.SetPasswordForm",
    "reset_password": "allauth.account.forms.ResetPasswordForm",
    "reset_password_from_key": "allauth.account.forms.ResetPasswordKeyForm",
    "disconnect": "allauth.socialaccount.forms.DisconnectForm",
}
LOGIN_URL = "/accounts/login"
LOGIN_REDIRECT_URL = "/accounts/profile"
LOGOUT_REDIRECT_URL = "/"

# ReCaptcha settings

RECAPTCHA_PUBLIC_KEY = ""
RECAPTCHA_PRIVATE_KEY = ""
RECAPTCHA_REQUIRED_SCORE = 0.85

# NavBar settings

NAVBAR = {
    "Announcements": "/announcements",
    "Blog": "/blog",
    "Clubs": "/clubs",
    "Map": "/map",
    "Calendar": "/calendar",
    "About": "/about",
}

# Announcements settings

ANNOUNCEMENTS_CUSTOM_FEEDS = []

# API settings

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

# SSO (OAuth) Settings

OAUTH2_PROVIDER = {
    "SCOPES": {
        "user": "Read other users' data",
        "me_meta": "Read your account data",
        "me_announcement": "Read your announcement feed",
        "me_schedule": "Read your schedules",
        "me_timetable": "Read your timetables",
    },
    "CLIENT_ID_GENERATOR_CLASS": "oauth2_provider.generators.ClientIdGenerator",
}

# GraphQL Settings
GRAPHENE = {"SCHEMA": "core.api2.schema"}

# CORS settings

CORS_URLS_REGEX = r"^/api/.*$"

CORS_ALLOW_METHODS = [
    "GET",
    "HEAD",
    "OPTIONS",
]

CORS_ALLOWED_ORIGINS = [
    "https://maclyonsden.com",
]

# Color settings

TAG_COLOR_SATURATION = 0.2
TAG_COLOR_VALUE = 1.0

# Martor settings

MARTOR_THEME = "bootstrap"
MARTOR_MARKDOWN_BASE_MENTION_URL = "/user/"
MARTOR_UPLOAD_URL = "/api/martor/upload-image"
MARTOR_UPLOAD_MEDIA_DIR = "martor"
MARTOR_UPLOAD_SAFE_EXTS = {".jpg", ".jpeg", ".png", ".gif"}
MARTOR_MARKDOWN_EXTENSIONS = [
    "markdown.extensions.tables",
    "markdown.extensions.nl2br",
    "markdown.extensions.fenced_code",
    "martor.extensions.emoji",
    "martor.extensions.escape_html",
    "martor.extensions.urlize",
    "core.markdown",
]

# Select2 settings

SELECT2_CACHE_BACKEND = "default"
SELECT2_JS = "js/select2.min.js"
SELECT2_CSS = "css/select2.min.css"

# PWA settings

PWA_APP_NAME = "Metropolis"
PWA_APP_DESCRIPTION = "William Lyon Mackenzie's online hub for announcements, calendar events, clubs, and timetables"
PWA_APP_THEME_COLOR = "#073763"
PWA_APP_BACKGROUND_COLOR = "#1c233f"
PWA_APP_DISPLAY = "standalone"
PWA_APP_SCOPE = "/"
PWA_APP_ORIENTATION = "any"
PWA_APP_START_URL = "/"
PWA_APP_STATUS_BAR_COLOR = "default"
PWA_APP_ICONS = [
    {
        "src": "/static/core/img/logo/logo-any-96.png",
        "sizes": "96x96",
        "type": "image/png",
        "purpose": "any",
    },
    {
        "src": "/static/core/img/logo/logo-maskable-96.png",
        "sizes": "96x96",
        "type": "image/png",
        "purpose": "maskable",
    },
    {
        "src": "/static/core/img/logo/logo-any-144.png",
        "sizes": "144x144",
        "type": "image/png",
        "purpose": "any",
    },
    {
        "src": "/static/core/img/logo/logo-maskable-144.png",
        "sizes": "144x144",
        "type": "image/png",
        "purpose": "maskable",
    },
    {
        "src": "/static/core/img/logo/logo-any-192.png",
        "sizes": "192x192",
        "type": "image/png",
        "purpose": "any",
    },
    {
        "src": "/static/core/img/logo/logo-maskable-192.png",
        "sizes": "192x192",
        "type": "image/png",
        "purpose": "maskable",
    },
]
PWA_APP_SPLASH_SCREEN = []
PWA_APP_LANG = "en-CA"
PWA_APP_DEBUG_MODE = False
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, "templates", "serviceworker.js")

# Mapbox settings

MAPBOX_APIKEY = "change me"

# Metropolis settings

METROPOLIS_STAFFS = {
    "Project Manager": {},
    "Frontend Developer": {},
    "Backend Developer": {},
    "App Developer": {},
    "Graphic Designer": {},
    "Content Creator": {},
}

METROPOLIS_STAFF_BIO = {}

# Theme Settings

THEMES = {
    "spring": {
        "banner": "/static/core/img/themes/banners/spring.jpg",
        "banner_css": "/static/core/css/themes/banners/spring-banner.css",
        "logo": "/static/core/img/themes/logos/dark-transparent.png",
        "theme": "/static/core/css/themes/base-theme.css",
    },
    "summer": {
        "banner": "/static/core/img/themes/banners/summer.jpg",
        "banner_css": "/static/core/css/themes/banners/summer-banner.css",
        "logo": "/static/core/img/themes/logos/dark-transparent.png",
        "theme": "/static/core/css/themes/base-theme.css",
    },
    "autumn": {
        "banner": "/static/core/img/themes/banners/autumn.jpg",
        "banner_css": "/static/core/css/themes/banners/autumn-banner.css",
        "logo": "/static/core/img/themes/logos/dark-transparent.png",
        "theme": "/static/core/css/themes/base-theme.css",
    },
    "winter": {
        "banner": "/static/core/img/themes/banners/winter.jpg",
        "banner_css": "/static/core/css/themes/banners/winter-banner.css",
        "logo": "/static/core/img/themes/logos/dark-transparent.png",
        "theme": "/static/core/css/themes/base-theme.css",
    },
    "halloween": {
        "banner": "/static/core/img/themes/banners/halloween.jpg",
        "banner_css": "/static/core/css/themes/banners/halloween-banner.css",
        "logo": "/static/core/img/themes/logos/halloween-transparent.png",
        "theme": "/static/core/css/themes/halloween-theme.css",
    },
    "remembrance": {
        "banner": "/static/core/img/themes/banners/winter.jpg",
        "banner_css": "/static/core/css/themes/banners/winter-banner.css",
        "logo": "/static/core/img/themes/logos/remembrance-transparent.png",
        "theme": "/static/core/css/themes/base-theme.css",
    },
    "christmas": {
        "banner": "/static/core/img/themes/banners/christmas.jpg",
        "banner_css": "/static/core/css/themes/banners/christmas-banner.css",
        "logo": "/static/core/img/themes/logos/christmas-transparent.png",
        "theme": "/static/core/css/themes/christmas-theme.css",
    },
}

CURRENT_THEME = "winter"

# Misc settings

SITE_ID = 1

SITE_URL = "http://127.0.0.1:8000"

TOS_URL = "/terms/"
PRIVPOL_URL = "/privacy/"

CRISPY_TEMPLATE_PACK = "bootstrap4"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SILENCED_SYSTEM_CHECKS = ["urls.W002"]

API_VERSION = "3.2.0"
API2_VERSION = "0.1.0"

DEFAULT_TIMEZONE = "UTC"

ANNOUNCEMENT_APPROVAL_BCC_LIST = []


try:
    from metropolis.config import *
except ImportError:
    print("Please create a config file to override values in settings.py")

THEME_BANNER = THEMES[CURRENT_THEME]["banner"]
THEME_BANNER_CSS = THEMES[CURRENT_THEME]["banner_css"]
THEME_LOGO = THEMES[CURRENT_THEME]["logo"]
THEME_CSS = THEMES[CURRENT_THEME]["theme"]
