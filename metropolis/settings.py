import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Final, List, Literal

import pytz
from sentry_sdk.integrations import django as sen_django
from sentry_sdk.integrations import logging as sen_logging
from sentry_sdk.integrations import redis

from metropolis.timetable_formats import TIMETABLE_FORMATS  # noqa: F401

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "Change me"

API_VERSION = "3.2.1"
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
    "django.contrib.redirects",
    "django.contrib.sitemaps",
    "core",
    "allauth",
    "allauth.account",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "martor",
    "django_select2",
    "pwa",
    "oauth2_provider",
    "hijack",
    "hijack.contrib.admin",  # show a hijack button on admin.
    "drf_spectacular",
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
    "core.middleware.CustomRedirectFallbackTemporaryMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "allauth.account.middleware.AccountMiddleware",
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
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",  # prod uses redis
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

TIME_ZONE = "America/Toronto"
TZ = pytz.timezone("America/Toronto")
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

TERM_GRACE_PERIOD = timedelta(weeks=2)


# Authentication settings
SESSION_SAVE_EVERY_REQUEST = True  # Refreshes session expiry  session on every request
SESSION_COOKIE_SECURE = True  # Only send session cookie over HTTPS
SESSION_COOKIE_AGE = 15 * 86400  # 15 days
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
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

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# NavBar settings

NAVBAR = {
    "Announcements": {
        "All": "/announcements?feed=all",
        "School": "/announcements?feed=school",
        "Student Council": "/announcements?feed=studentcouncil",
    },
    "Calendar": "/calendar",
    "Clubs": "/clubs",
    "Content": "/blog",
    "Doodle": "https://doodle.maclyonsden.com",
    "Map": "/map",
    "Resources": "/resources",
    "About": {
        "WLMCI": "/about?tab=history",
        "About": "/about?tab=about",
        "Team": "/about?tab=team",
        "Contact WLMCI": "/about?tab=school",
        "Contact Us": "/about?tab=contact",
    },
}

# post settings

POST_CONTENT_TYPES = ("announcement", "blogpost", "comment", "exhibit")

# Announcements settings

ANNOUNCEMENTS_CUSTOM_FEEDS = []  # list of PKs of organizations

# Comment settings

ALLOW_COMMENTS: bool = True  # Whether to allow comments on posts

# API settings

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 30,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

GLOBAL_LOOKUPS: Final[List[str]] = [
    "id"
]  # lookups allowed for all providers, first value will be the default if not specified
IGNORED_QUERY_PARAMS: List[str] = [
    "limit",
    "offset",
    "search_type",
    "format",
]  # query params that are ignored by the API (e.g., for lookups)

LOOKUP_FIELD_REPLACEMENTS: Dict[str, str] = {
    "TextField": "__iexact",
    "CharField": "__iexact",
}

# SSO (OAuth) Settings
CLEAR_EXPIRED_TOKENS_BATCH_INTERVAL = 5
CLEAR_EXPIRED_TOKENS_BATCH_SIZE = 500

OAUTH2_PROVIDER = dict(
    SCOPES={
        "openid": "OpenID Connect",
        "email": "Read your email address",
        "user": "Read other users' data",
        "internal": "Internal Application",
        "me_meta": "Read your account data",
        "me_announcement": "Read your announcement feed",
        "me_schedule": "Read your schedules",
        "me_timetable": "Read your timetables",
    },
    CLIENT_ID_GENERATOR_CLASS="oauth2_provider.generators.ClientIdGenerator",
    OIDC_ENABLED=True,
)

with open(os.path.join(os.path.dirname(__file__), "local_rsa_privkey.pem")) as f:
    OAUTH2_PROVIDER.update(
        dict(
            OIDC_RSA_PRIVATE_KEY=f.read(),
        )
    )


# sentry settings

SENTRY_INTEGRATIONS = [  # https://docs.sentry.io/platforms/python/integrations/logging/#ignoring-a-logger
    sen_django.DjangoIntegration(
        transaction_style="url",
        # Create spans and track performance of all middleware.
        middleware_spans=True,  # todo disable in a week (2024-02-10)
        # Create spans and track performance of all synchronous Django signals receiver functions in your Django project
        signals_spans=True,  # todo disable in a month then enable to test notifs
        # Create spans and track performance of all read operations to configured caches. The spans also include information if the cache access was a hit or a miss.
        cache_spans=True,
    ),
    redis.RedisIntegration(),
    sen_logging.LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.WARNING,  # Send records as events
    ),
]

# Scheme generation
SPECTACULAR_SETTINGS = {
    "TITLE": "Metropolis",
    "DESCRIPTION": "The API for metropolis and related services",
    "VERSION": API_VERSION,
    "LICENSE": {
        "name": "AGPL-3",
        "url": "https://github.com/wlmac/metropolis/blob/develop/LICENSE",
    },
    "SORT_OPERATION_PARAMETERS": False,
    "COMPONENT_SPLIT_PATCH": False,
    "OAUTH2_FLOWS": [],
    "OAUTH2_AUTHORIZATION_URL": "/authorize",
    "OAUTH2_TOKEN_URL": "/api/auth/token",
    "OAUTH2_REFRESH_URL": "/api/auth/token/refresh",
    "DEFAULT_GENERATOR_CLASS": "core.schema.MetroSchemaGenerator",
    "OAUTH2_SCOPES": OAUTH2_PROVIDER["SCOPES"].keys(),
    # "POSTPROCESSING_HOOKS": ["core.schema.run_fixers"],
    #'SERVE_INCLUDE_SCHEMA': False,
    # OTHER SETTINGS
}


# CORS settings

CORS_URLS_REGEX = r"^/api/.*$"

CORS_ALLOWED_ORIGINS = [
    "https://maclyonsden.com",
]

# Color settings

TAG_COLOR_SATURATION = 0.2
TAG_COLOR_VALUE = 1.0

# Martor settings

MARTOR_THEME = "bootstrap"
# MARTOR_ALTERNATIVE_CSS_FILE_THEME = "fix-martor.css" todo add back
MARTOR_MARKDOWN_BASE_MENTION_URL = "/user/"
MARTOR_UPLOAD_URL = "/api/upload-image/"
MARTOR_UPLOAD_MEDIA_DIR = "martor"
MARTOR_UPLOAD_SAFE_EXTS = {".jpg", ".jpeg", ".png", ".gif"}
MARTOR_MARKDOWN_EXTENSIONS = [
    "markdown.extensions.tables",
    "markdown.extensions.nl2br",
    "markdown.extensions.fenced_code",
    "martor.extensions.escape_html",
    "martor.extensions.urlize",
    "core.markdown.embed",
    "core.markdown.emoji",
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

# Team settings

METROPOLIS_POSITIONS = (
    ("Project Manager", "Project Manager"),
    ("Frontend Developer", "Frontend Developer"),
    ("Backend Developer", "Backend Developer"),
    ("App Developer", "App Developer"),
    ("Graphic Designer", "Graphic Designer"),
    ("Content Creator", "Content Creator"),
    ("Doodle Developer", "Doodle Developer"),
)

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
    "valentines": {
        "banner": "/static/core/img/themes/banners/valentines.jpg",
        "banner_css": "/static/core/css/themes/banners/valentines-banner.css",
        "logo": "/static/core/img/themes/logos/valentines-transparent.png",
        "theme": "/static/core/css/themes/valentines-theme.css",
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
    "39": {
        "banner": "/static/core/img/themes/banners/spring.jpg",
        "banner_css": "/static/core/css/themes/banners/spring-banner.css",
        "logo": "/static/core/img/themes/logos/dark-transparent.png",
        "theme": "/static/core/css/themes/39-theme.css",
    },
}

CURRENT_THEME = "autumn"  # should be changed in local_settings.py

# Lazy Loading

LAZY_LOADING = {  # set to` False to disable
    "per_page": 2,
    "initial_limit": 4,
}

# Misc settings

SITE_ID = 1

SITE_URL = "http://127.0.0.1:8000"

TOS_URL = "/terms/"
PRIVPOL_URL = "/privacy/"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

HIJACK_PERMISSION_CHECK = "core.utils.hijack.hijack_permissions_check"

ALLOWED_HIJACKERS = [746, 165]  # Jason Cameron & Ken Shibata

ANNOUNCEMENT_APPROVAL_BCC_LIST = []

ROOT = "http://localhost"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "ROTATE_REFRESH_TOKENS": True,  # create new refresh token on every refresh (with renewed on refresh
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "UPDATE_LAST_LOGIN": True,
}
# Event calender Settings

ICAL_PADDING = timedelta(days=4 * 7)  # iCalendar Feed

# Qualified Trials
QLTR: Dict[str, Dict] = {
    "ia": dict(
        title="Cumulative Minor Changes to Index",
    ),
}

TEACHER_EMAIL_SUFFIX = "@tdsb.on.ca"
STUDENT_EMAIL_SUFFIX = "@student.tdsb.on.ca"

MAINTENANCE_MODE: Literal["", False, "pre", "post", "in"] = ""
PRE = ""
BANNER3: List = [
    #   dict(
    #       start=BANNER_REFERENCE_TIME,
    #       end=BANNER_REFERENCE_TIME + timedelta(days=5),
    #       content="This is some banner :)",
    #       icon_url="...", # optional
    #       cta_link="https://nyiyui.ca", # optional
    #       cta_label="some shameless plug to nowhere amirite", # optional (but required if cta_link is present)
    #   ),
]

CELERY_TIMEZONE = "America/Toronto"

# (Expo) Notifications

NOTIF_EXPO_TIMEOUT_SECS = 3

ANNOUNCEMENTS_NOTIFY_FEEDS = []  # list of PKs of organizations
EVENTS_NOTIFY_FEEDS = []  # list of PKs of organizations
NOTIF_DRY_RUN = True
NOTIFICATIONS_ENABLED = False


def is_aware(d: datetime) -> bool:
    return d.tzinfo is not None and d.tzinfo.utcoffset(d) is not None


def check_banner3(banner: Dict) -> None:
    assert is_aware(banner["start"])
    assert is_aware(banner["end"])
    assert bool(banner.get("cta_link")) == bool(
        banner.get("cta_label")
    )  # both or neither, not one or the other


for banner in BANNER3:
    check_banner3(banner)

try:
    with open(os.path.join(os.path.dirname(__file__), "./local_settings.py")) as f:
        exec(f.read(), globals())
except IOError:
    os.listdir(os.path.dirname(__file__))
    raise FileNotFoundError(
        "local_settings.py not found, please consult docs for setup instructions"
    )

if SECRET_KEY == "Change me":
    raise TypeError("override SECRET_KEY")


def set_maintenance():
    _PRE = ""
    match MAINTENANCE_MODE:
        case "pre":
            _PRE = '<div style="background-color: #ffc107; color: #000000; text-align: center; padding: 10px;">Metropolis is undergoing pre - maintenance preparations. Please be advised that temporary service interruptions may occur. We appreciate your patience as we work towards improving and enhancing your experience.</div>'
        case "post":
            _PRE = '<div style="background-color: #cce5ff; color: #000000; text-align: center; padding: 10px;">Metropolis recently experienced downtime for essential server maintenance.We appreciate your understanding during this period of ongoing improvements and enhancements.</div>'
        case "in":
            '<div style="background-color: #ff0000; color: #ffffff; text-align: center; padding: 10px; font-weight: bold;">Metropolis is currently undergoing upgrades.Please note that any data may not be saved during this process. </div>'
    global PRE
    PRE = PRE or _PRE  # Prioritise PRE


set_maintenance()

THEME_BANNER = THEMES[CURRENT_THEME]["banner"]
THEME_BANNER_CSS = THEMES[CURRENT_THEME]["banner_css"]
THEME_LOGO = THEMES[CURRENT_THEME]["logo"]
THEME_CSS = THEMES[CURRENT_THEME]["theme"]

SPECTACULAR_SETTINGS.update(SWAGGER_UI_FAVICON_HREF=THEME_LOGO)

# Daily Annoucment 

GOOGLE_SHEET_KEY = ""
SECRETS_PATH = ""