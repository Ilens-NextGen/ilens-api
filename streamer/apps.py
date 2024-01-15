from django.apps import AppConfig  # type: ignore[import]


class StreamerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "streamer"
