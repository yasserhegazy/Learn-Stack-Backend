"""
Django app configuration for the Users module.
"""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.users'
    verbose_name = 'User & Role Management'
    
    def ready(self):
        """Import signal handlers when the app is ready."""
        # import modules.users.signals  # noqa
        pass
