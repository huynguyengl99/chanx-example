# mypy: ignore-errors

from .base import *  # NOQA

SECRET_KEY = env.str("DJANGO_SECRET_KEY")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS += ["anymail"]
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
# https://anymail.readthedocs.io/en/stable/installation/#anymail-settings-reference
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
ANYMAIL: dict[str, Any] = {}
