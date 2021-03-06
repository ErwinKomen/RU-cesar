from django.contrib import admin
from django.forms import Textarea

from cesar.viewer.models import *
from cesar.viewer.forms import *


class NewsItemAdmin(admin.ModelAdmin):
    """Display and edit of [NewsItem] definitions"""

    list_display = ['title', 'until', 'status', 'created', 'saved' ]
    search_fields = ['title', 'status']
    fields = ['title', 'created', 'until', 'status', 'msg']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'class': 'mytextarea'})},
        }


# Models for Cesar Viewer
admin.site.register(NewsItem, NewsItemAdmin)
