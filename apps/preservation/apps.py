from django.apps import AppConfig

class PreservationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.preservation'

    def ready(self):
        import apps.preservation.signals
