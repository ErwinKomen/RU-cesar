from django.contrib import admin
from django.forms import Textarea

from cesar.browser.models import *
from cesar.browser.forms import *

class FieldChoiceAdmin(admin.ModelAdmin):
    readonly_fields=['machine_value']
    list_display = ['english_name','dutch_name','machine_value','field']
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
    extra = 0


class VariableNameAdmin(admin.ModelAdmin):
    """Displaying [VariableName]"""

    list_display = ['name', 'type']
    search_field = ['name', 'type']
    inlines = [VariableInline]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class VariableAdmin(admin.ModelAdmin):
    """Displaying [Variable]"""

    list_display = ['name', 'loc', 'metavar']
    search_field = ['name', 'loc', 'metavar']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class GroupingInline(admin.TabularInline):
    model = Grouping
    extra = 0


class GroupingNameAdmin(admin.ModelAdmin):
    """Displaying [GroupingName]"""

    list_display = ['name']
    search_field = ['name']
    inlines = [GroupingInline]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class GroupingAdmin(admin.ModelAdmin):
    """Displaying [Grouping]"""

    list_display = ['name', 'metavar']
    search_field = ['name', 'metavar']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class ConstituentNameTransInline(admin.TabularInline):
    model = ConstituentNameTrans
    form = ConstituentNameTransForm
    extra = 0


class ConstituentNameTransAdmin(admin.ModelAdmin):
    """Displaying [TagsetNameTrans]"""

    list_display = ['lng', 'descr']
    search_field = ['lng', 'descr']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class ConstituentAdmin(admin.ModelAdmin):
    """Displaying [ConstituentName]"""

    list_display = ['title', 'eng']
    search_field = ['title', 'eng']
    inlines = [ConstituentNameTransInline]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class TagsetInline(admin.TabularInline):
    model = Tagset
    extra = 0


class TagsetAdmin(admin.ModelAdmin):
    """Displaying [Tagset]"""

    list_display = ['constituent', 'definition', 'metavar']
    search_field = ['constituent', 'definition', 'metavar']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class MetavarAdmin(admin.ModelAdmin):
    """Displaying [Metavar]"""

    list_display = ['name', 'hidden']
    search_field = ['name']
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


class PartAdmin(admin.ModelAdmin):
    """Displaying [Part]"""

    list_display = ['name', 'dir', 'metavar', 'corpus']
    search_field = ['name', 'dir', 'metavar', 'corpus']
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
    search_field = ['name', 'lng', 'eth', 'metavar', 'status']
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
