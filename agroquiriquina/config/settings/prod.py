import os

from .base import *  # noqa
from .base import env_list

DEBUG = False

if SECRET_KEY == "dev-insecure-key-change-me":  # noqa: F405
    raise RuntimeError("Define DJANGO_SECRET_KEY en producción.")

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True") == "True"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
