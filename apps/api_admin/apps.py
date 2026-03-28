from django.apps import AppConfig


class ApiAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'apps.api_admin'
    verbose_name       = 'API Admin'
