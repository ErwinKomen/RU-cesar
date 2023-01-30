from django.contrib import admin
from django.forms import Textarea

from cesar.doc.models import *

class ExpressionAdmin(admin.ModelAdmin):
    """Displaying [Expression]"""

    list_display = ['full', 'score']
    search_fields = ['full', 'score']
    fields = ['full', 'score', 'lemmas']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }



# Registered models
admin.site.register(FrogLink)
# admin.site.register(FoliaProcessor)
admin.site.register(Brysbaert)
admin.site.register(Expression, ExpressionAdmin)
