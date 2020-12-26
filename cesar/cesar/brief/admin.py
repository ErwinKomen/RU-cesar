from django.contrib import admin
from django.contrib.admin.models import LogEntry, DELETION
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.forms import Textarea
from django.utils.html import escape

from cesar.brief.models import *
from cesar.brief.forms import *

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


class BriefSectionAdmin(admin.ModelAdmin):
    """Display and edit [BriefSection] objects"""

    fields = ['name', 'order', 'intro', 'module']
    list_display = ['module', 'name', 'order']
    list_filter = ['module']
    search_fields = ['name']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'class': 'mytextarea'})},
        }


class BriefQuestionAdmin(admin.ModelAdmin):
    """Display and edit [BriefQuestion] objects"""

    fields = ['order', 'rtype', 'ntype', 'content', 'help', 'placeholder', 'section']
    list_display = ['get_module', 'get_section', 'order', 'content', 'rtype', 'ntype']
    list_filter = ['section__module__order']   #    ['get_module', 'get_section']
    search_fields = ['name']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'class': 'mytextarea'})},
        }

    def get_module(self, obj):
        return obj.section.module.order
    get_module.admin_order_field = 'section'
    get_module.short_description = 'Module'

    def get_section(self,obj):
        return obj.section.order
    get_section.admin_order_field = 'section'
    get_section.short_description = "Section"




# Models that serve others
admin.site.register(FieldChoice, FieldChoiceAdmin)

# Models for the [brief] app
admin.site.register(BriefEntry)
admin.site.register(BriefModule)
admin.site.register(BriefQuestion, BriefQuestionAdmin)
admin.site.register(BriefSection, BriefSectionAdmin)
admin.site.register(Project)
admin.site.register(AnswerEntry)
admin.site.register(AnswerQuestion)


