from django.contrib import admin
from django.forms import Textarea

from cesar.trans.models import *

class ActionAdmin(admin.ModelAdmin):
    """Displaying [Action] details"""

    list_display = ['appname', 'username', 'computer', 'ftype', 'fname', 'created']
    list_filter = ['appname', 'username']
    search_fields = ['appname', 'username', 'computer', 'ftype', 'fname']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


# Registered models
admin.site.register(Action, ActionAdmin)
