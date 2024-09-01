from pathlib import Path

_using_docker_config = True  # intended for allow changing config *in dev*

BASE_DIR = Path(__file__).resolve().parent.parent

ALLOWED_HOSTS = ["localhost"]

STATIC_ROOT = "/app-public"

MEDIA_ROOT = "/app-media"
MEDIA_URL = "/media/"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "metropolis_db",
        "USER": "metropolis_user",
        "PASSWORD": "changeme_metropolis_password",  # overwritten by local settings
        "HOST": "postgres",
        "PORT": "",
    }
}

CELERY_BROKER_URL = "redis://redis:6379"

try:
    with open(os.path.join(os.path.dirname(__file__), "docker_local_settings.py")) as f:  # noqa: F821
        exec(f.read(), globals())
except IOError:
    raise TypeError(
        "There is an error in the naming of docker_local_settings.py. See docker compose. It should contain the data in local_settings.py."
    )
