from django.contrib import admin
from django.forms import Textarea

from cesar.tsg.models import *

class TsgInfoAdmin(admin.ModelAdmin):
    """Displaying [Variable]"""

    list_display = ['infokey', 'infoval']
    search_fields = ['infokey']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class TsgHandleAdmin(admin.ModelAdmin):
    """Displaying [Variable]"""

    list_display = ['code', 'url', 'created']
    search_fields = ['code', 'url']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


# Registered models
admin.site.register(TsgInfo, TsgInfoAdmin)
admin.site.register(TsgHandle, TsgHandleAdmin)