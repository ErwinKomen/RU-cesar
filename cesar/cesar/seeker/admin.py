from django.contrib import admin
from django.forms import Textarea

from cesar.seeker.models import *
from cesar.seeker.forms import *


class ConstructionInline(admin.TabularInline):
    model = Construction
    form = ConstructionWrdForm
    extra = 0


class ShareGroupInline(admin.TabularInline):
    model = ShareGroup
    form = SharegForm
    extra = 0


class ResearchAdmin(admin.ModelAdmin):
    """Displaying [Research]"""

    list_display = ['name', 'owner', 'stype', 'created', 'saved', 'purpose', 'gateway_name']
    search_fields = ['name', 'owner', 'purpose', 'gateway_name']
    list_filter = ['owner']
    # inlines = [ConstructionInline]
    inlines = [ShareGroupInline]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class ArgumentDefInline(admin.TabularInline):
    model = ArgumentDef
    form = ArgumentDefForm
    extra = 0

class FuncionCodeInline(admin.TabularInline):
    model = FunctionCode
    form = FunctionCodeForm
    extra = 0


class FunctionDefAdmin(admin.ModelAdmin):
    """Display and edit of [Function] definitions"""

    list_display = ['name', 'title', 'type', 'argnum', 'get_function_count']
    search_fields = ['name', 'title','type', 'argnum']
    fields = ['name', 'title', 'type', 'argnum']
    inlines = [ArgumentDefInline, FuncionCodeInline]

class RelationAdmin(admin.ModelAdmin):
    """Display and edit [Relation] definitions"""

    list_display = ['name', 'type', 'xpath']
    search_fields = ['name','type', 'xpath']
    fields = ['name', 'type','xpath']



# Models for Cesar Browser
admin.site.register(Research, ResearchAdmin)
admin.site.register(FunctionDef, FunctionDefAdmin)
admin.site.register(Relation, RelationAdmin)
