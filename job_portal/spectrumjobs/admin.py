from django.contrib import admin
from .models import *

# Admin dashboard models
admin.site.register(Calendar)
admin.site.register(CitizenFeedback)
admin.site.register(EmployerFeedback)
admin.site.register(SensoryProfile)
admin.site.register(CitizenProfile)
admin.site.register(Job)

