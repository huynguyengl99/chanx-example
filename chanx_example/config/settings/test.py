from .base import *  # NOQA

TEST = True

MEDIA_URL = "media-testing/"
MEDIA_ROOT = str(BASE_DIR / "media-testing/")

SPECTACULAR_SETTINGS = {
    **SPECTACULAR_SETTINGS,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SERVE_AUTHENTICATION": [],
}

CHANX = {
    "SEND_COMPLETION": True,
}
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

OPENAI_API_KEY = "Mock-key"
