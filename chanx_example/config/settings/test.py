from .base import *  # NOQA

TEST = True

MEDIA_URL = "media-testing/"
MEDIA_ROOT = str(BASE_DIR / "media-testing/")

SPECTACULAR_SETTINGS = {
    **SPECTACULAR_SETTINGS,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SERVE_AUTHENTICATION": [],
}
