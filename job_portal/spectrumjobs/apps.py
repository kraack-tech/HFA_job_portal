from django.apps import AppConfig

class SpectrumjobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'spectrumjobs'
    def ready(self):
        # Import consumer and signal scripts
        import spectrumjobs.consumers
        import spectrumjobs.signals 
