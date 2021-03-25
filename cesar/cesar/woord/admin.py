from django.contrib import admin
from django.contrib.admin.models import LogEntry, DELETION
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.forms import Textarea
from django.utils.html import escape

from cesar.woord.models import *
from cesar.woord.forms import *

class FieldChoiceAdmin(admin.ModelAdmin):
    readonly_fields=['machine_value']
    list_display = ['english_name','dutch_name','abbr', 'machine_value','field']
    list_filter = ['field']

    def save_model(self, request, obj, form, change):

        if obj.machine_value == None:
            # Check out the query-set and make sure that it exists
            qs = FieldChoice.objects.filter(field=obj.field)
            if len(qs) == 0:
                # The field does not yet occur within FieldChoice
                # Future: ask user if that is what he wants (don't know how...)
                # For now: assume user wants to add a new field (e.g: wordClass)
                # NOTE: start with '0'
                obj.machine_value = 0
            else:
                # Calculate highest currently occurring value
                highest_machine_value = max([field_choice.machine_value for field_choice in qs])
                # The automatic machine value we calculate is 1 higher
                obj.machine_value= highest_machine_value+1

        obj.save()


class WoordUserAdmin(admin.ModelAdmin):
    """Display and edit [WoordUser] objects"""

    fields = ['name', 'gender', 'age', 'about', 'status']
    list_display = ['name', 'gender', 'age', 'about', 'status']
    list_filter = ['gender', 'status']
    search_fields = ['name']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'class': 'mytextarea'})},
        }


class ResultAdmin(admin.ModelAdmin):
    """Display and edit [Result] objects"""

    fields = ['user', 'question', 'judgment']
    list_display = ['user', 'question', 'judgment']
    list_filter = ['question', 'user']
    search_fields = ['question', 'user']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'class': 'mytextarea'})},
        }





# Models that serve others
admin.site.register(FieldChoice, FieldChoiceAdmin)

# Models for the [woord] app
admin.site.register(WoordUser, WoordUserAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Stimulus)


