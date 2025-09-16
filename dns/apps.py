from django.apps import AppConfig


class DnsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dns'
    
    def ready(self):
        import dns.signals