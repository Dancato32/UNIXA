"""AppConfig for the community app — connects signals on ready."""

from django.apps import AppConfig


class CommunityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'community'
    verbose_name = 'Campus Community Hub'

    def ready(self):
        # Import signals so they are registered with Django's signal dispatcher
        import community.signals  # noqa: F401
