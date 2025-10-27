from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth'
    label = 'accounts'  # Etiqueta única para evitar conflicto con django.contrib.auth
