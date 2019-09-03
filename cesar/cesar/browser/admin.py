from django.contrib import admin
from django.contrib.admin.models import LogEntry, DELETION
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.forms import Textarea
from django.utils.html import escape

from cesar.browser.models import *
from cesar.browser.forms import *


class LogEntryAdmin(admin.ModelAdmin):

    date_hierarchy = 'action_time'

    # readonly_fields = LogEntry._meta.get_all_field_names()
    readonly_fields = [f.name for f in LogEntry._meta.get_fields()]

    list_filter = ['user', 'content_type', 'action_flag' ]
    search_fields = [ 'object_repr', 'change_message' ]    
    list_display = ['action_time', 'user', 'content_type', 'object_link', 'action_flag_', 'change_message', ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.method != 'POST'

    def has_delete_permission(self, request, obj=None):
        return False

    def action_flag_(self, obj):
        flags = { 1: "Addition", 2: "Changed", 3: "Deleted", }
        return flags[obj.action_flag]

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = '<a href="{}">{}</a>'.format(
                reverse('admin:{}_{}_change'.format(ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
            )
        return link
    object_link.allow_tags = True
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = u'object'


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


class VariableInline(admin.TabularInline):
    model = Variable
    form = VariableForm
    extra = 0


class VariableNameAdmin(admin.ModelAdmin):
    """Displaying [VariableName]"""

    list_display = ['name', 'type']
    search_fields = ['name', 'type']
    inlines = [VariableInline]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class VariableAdmin(admin.ModelAdmin):
    """Displaying [Variable]"""

    list_display = ['name', 'loc', 'metavar']
    search_fields = ['name', 'loc', 'metavar']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class GroupingInline(admin.TabularInline):
    model = Grouping
    form = GroupingForm
    extra = 0


class GroupingNameAdmin(admin.ModelAdmin):
    """Displaying [GroupingName]"""

    list_display = ['name']
    search_fields = ['name']
    inlines = [GroupingInline]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class GroupingAdmin(admin.ModelAdmin):
    """Displaying [Grouping]"""

    list_display = ['name', 'metavar']
    search_fields = ['name', 'metavar']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class ConstituentNameTransInline(admin.TabularInline):
    model = ConstituentNameTrans
    form = ConstituentNameTransForm
    verbose_name = "Constituent name translation"
    verbose_name_plural = "Constituent name translations"
    extra = 0


class ConstituentNameTransAdmin(admin.ModelAdmin):
    """Displaying [TagsetNameTrans]"""

    list_display = ['lng', 'descr']
    search_fields = ['lng', 'descr']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class ConstituentAdmin(admin.ModelAdmin):
    """Displaying [ConstituentName]"""

    list_display = ['title', 'eng']
    search_fields = ['title', 'eng']
    inlines = [ConstituentNameTransInline]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class TagsetInline(admin.TabularInline):
    model = Tagset
    form = TagsetForm
    extra = 0


class TagsetAdmin(admin.ModelAdmin):
    """Displaying [Tagset]"""

    list_display = ['constituent', 'definition', 'metavar']
    search_fields = ['constituent', 'definition', 'metavar']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class MetavarAdmin(admin.ModelAdmin):
    """Displaying [Metavar]"""

    list_display = ['name', 'hidden']
    search_fields = ['name']
    inlines = [VariableInline, GroupingInline, TagsetInline]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class DownloadAdmin(admin.ModelAdmin):
    """Displaying [Download]"""

    list_display = ['part', 'format']
    search_field = ['part', 'format']


class DownloadInline(admin.TabularInline):
    model = Download
    extra = 0


class SentenceAdmin(admin.ModelAdmin):
    """Showing a sentence"""

    form = SentenceAdminForm

    list_display = ['order', 'identifier', 'sent']
    search_fields = ['order', 'identifier', 'sent']
    list_filter = ['text__part__name', 'text__fileName']


class SentenceInline(admin.TabularInline):
    model = Sentence
    extra = 0


class TextAdmin(admin.ModelAdmin):
    """Showing texts"""

    form = TextAdminForm

    list_display = ['part','formatname', 'fileName', 'lines','title', 'datename', 'author', 'genrename', 'subtypename']
    # list_display = ['admin_form_column_names',]
    search_fields = ['part','format', 'fileName','title', 'date', 'author', 'genre', 'subtype']
    list_filter = ['part', 'format', 'genre', 'subtype']
    inlines = [SentenceInline]


class PartAdmin(admin.ModelAdmin):
    """Displaying [Part]"""

    list_display = ['name', 'dir', 'metavar', 'corpus']
    search_fields = ['name', 'dir', 'metavar', 'corpus']
    inlines = [DownloadInline]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 2})},
        }


class PartInline(admin.TabularInline):
    model = Part
    form = PartForm
    extra = 0


class CorpusAdmin(admin.ModelAdmin):
    """Displaying [Corpus]"""

    list_display = ['name', 'lng', 'eth', 'metavar', 'status']
    search_fields = ['name', 'lng', 'eth', 'metavar', 'status']
    inlines = [PartInline]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }



# Models that serve others
admin.site.register(FieldChoice, FieldChoiceAdmin)
admin.site.register(HelpChoice)

# Models for Cesar Browser
admin.site.register(Metavar, MetavarAdmin)
admin.site.register(VariableName, VariableNameAdmin)
admin.site.register(Variable, VariableAdmin)
admin.site.register(Constituent, ConstituentAdmin)
admin.site.register(Tagset, TagsetAdmin)
admin.site.register(GroupingName, GroupingNameAdmin)
admin.site.register(Grouping, GroupingAdmin)
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(Part, PartAdmin)
admin.site.register(Download, DownloadAdmin)
admin.site.register(Text, TextAdmin)
admin.site.register(Sentence, SentenceAdmin)

# Logbook of activities
admin.site.register(LogEntry, LogEntryAdmin)

# How to display user information
admin.site.unregister(User)
# What to display in a list
UserAdmin.list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'last_login']
# Turn it on again
admin.site.register(User, UserAdmin)

