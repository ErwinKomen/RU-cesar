from django.contrib import admin
from django.forms import Textarea
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from cesar.lingo.models import *
from cesar.lingo.forms import *


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


class ExperimentAdmin(admin.ModelAdmin):
    """Display and edit of [NewsItem] definitions"""

    list_display = ['title', 'until', 'status', 'created', 'saved', 'home' ]
    search_fields = ['title', 'status']
    fields = ['title', 'created', 'until', 'status', 'home', 'msg']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'class': 'mytextarea'})},
        }

    def response_post_save_change(self, request, obj):
        # Return to the details view on saving
        sUrl = redirect( reverse('exp_details', args=[obj.id]) )
        return sUrl

    def response_add(self, request, obj, post_url_continue = None):
        # Return to the experiment list view
        sUrl = redirect(reverse('exp_list'))
        return sUrl

    def response_delete(self, request, obj_display, obj_id):
        sUrl = redirect(reverse('exp_list'))
        return sUrl


class QdataAdmin(admin.ModelAdmin):
    """Display and edit [Question Data] definitions"""

    fields = ['qmeta', 'qtext', 'qtopic', 'qsuggest', 'qcorr', 'experiment', 'include']
    list_display = ['qmeta', 'qtopic', 'qsuggest', 'qcorr', 'experiment', 'include']
    search_fields = ['qmeta']
    list_filter = ['include']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'class': 'mytextarea'})},
        }

    def response_post_save_change(self, request, obj):
        # Return to the details view on saving
        sUrl = redirect( reverse('qdata_details', args=[obj.id]) )
        return sUrl

    def response_add(self, request, obj, post_url_continue = None):
        # Return to the details view of the experiment
        sUrl = redirect(reverse('exp_details', args=[obj.experiment.id]))
        return sUrl

    def response_delete(self, request, obj_display, obj_id):
        sUrl = redirect(reverse('exp_list'))
        return sUrl


class ResponseAdmin(admin.ModelAdmin):
    """Display and edit [Response] objects from participants"""

    fields = ['experiment', 'participant', 'answer']
    list_display = ['experiment', 'participant', 'answer']
    search_fields = ['experiment']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'class': 'mytextarea'})},
        }


class ParticipantAdmin(admin.ModelAdmin):
    """Display and edit [Participant] objects"""

    fields = ['ip', 'age', 'gender', 'edu', 'email', 'created']
    list_display = ['ip', 'age', 'gender', 'edu', 'email', 'created']
    search_fields = ['ip', 'email']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'class': 'mytextarea'})},
        }


# Models that serve others
admin.site.register(FieldChoice, FieldChoiceAdmin)

# Models for Cesar Lingo
admin.site.register(Experiment, ExperimentAdmin)
admin.site.register(Qdata, QdataAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Response, ResponseAdmin)
