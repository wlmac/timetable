from datetime import datetime, timezone  # noqa: F401

import sentry_sdk

# Daily Announcements

GOOGLE_SHEET_ID = ""
SECRETS_PATH = ""

# ruff: noqa: F821

SECRET_KEY = "change me!"
DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"  # to emails just get printed to the console.
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".ngrok.io", ".ngrok-free.app"]

GCAL_API_KEY = "Change me"

GEMINI_API_KEY = "Change me"

if DEBUG:
    import mimetypes
    import socket  # only if you haven't already imported this

    host_name, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
        "127.0.0.1",
        "10.0.2.2",
    ]

    mimetypes.add_type(
        "application/javascript", ".js", True
    )  # fix some browser issues.

# Banner config
now = datetime.now(TZ)
# BANNER_REFERENCE_TIME =  datetime.strptime("2023-11-14", "%Y-%m-%d").replace(tzinfo=timezone.utc)  # use instead of $now for non-relative banners.

BANNER3 += [
    dict(
        start=now,  # when to start displaying the banner
        end=now + timedelta(days=5),
        # when to stop displaying the banner (e.g. 5 days after start)
        content="Hello Hey!",  # banner text
        icon_url="/static/core/img/logo/logo-maskable-192.png",
        # optionally, displays an icon on the left of the banner
        cta_link="https://jasoncameron.dev",  # optional
        cta_label="wow! go visit this cool site!",  # optional (but required if cta_link is present)
    )
]


if not DEBUG:
    """
    Only used on production
    """
    sentry_sdk.init(
        # dsn="get this from sentry.io",
        enable_tracing=True,
        # Set traces_sample_rate to 1.0 to capture 100% of transactions%
        traces_sample_rate=0.7,
        # Set profiles_sample_rate to 1.0 to profile 100%
        profiles_sample_rate=0.7,
        include_source_context=True,
        include_local_variables=True,
        environment="production",
        send_default_pii=True,
        integrations=SENTRY_INTEGRATIONS,
    )
