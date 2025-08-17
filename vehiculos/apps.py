from django.apps import AppConfig


class VehiculosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vehiculos'


from django.apps import AppConfig

class TuAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tu_app'

    def ready(self):
        import vehiculos.signals  # Asegúrate de crear este archivo si no existe