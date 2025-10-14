from django.apps import AppConfig


class DnsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dns'
    
    def ready(self):
        # Import signals to register them
        from . import signals
        
        # HADDNS signals are automatically registered via @receiver decorators
        # No additional signal registration needed