from django.contrib import admin
from django.forms import Textarea

from cesar.seeker.models import *
from cesar.seeker.forms import *


class ConstructionInline(admin.TabularInline):
    model = Construction
    form = ConstructionWrdForm
    extra = 0


class ResearchAdmin(admin.ModelAdmin):
    """Displaying [Research]"""

    list_display = ['name', 'purpose', 'gateway_name']
    search_fields = ['name', 'purpose', 'gateway_name']
    # inlines = [ConstructionInline]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


# Models for Cesar Browser
admin.site.register(Research, ResearchAdmin)
admin.site.register(Gateway)
admin.site.register(Construction)
