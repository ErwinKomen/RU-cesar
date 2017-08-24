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


class ArgumentDefInline(admin.TabularInline):
    model = ArgumentDef
    form = ArgumentDefForm
    extra = 0


class FunctionDefAdmin(admin.ModelAdmin):
    """Display and edit of [Function] definitions"""

    list_display = ['name', 'title', 'type', 'argnum']
    search_fields = ['name', 'title','type', 'argnum']
    fields = ['name', 'title', 'type', 'argnum']
    inlines = [ArgumentDefInline]

class RelationAdmin(admin.ModelAdmin):
    """Display and edit [Relation] definitions"""

    list_display = ['name', 'xpath']
    search_fields = ['name', 'xpath']
    fields = ['name', 'xpath']



# Models for Cesar Browser
admin.site.register(Research, ResearchAdmin)
admin.site.register(Gateway)
admin.site.register(Construction)
admin.site.register(FunctionDef, FunctionDefAdmin)
admin.site.register(Relation, RelationAdmin)
