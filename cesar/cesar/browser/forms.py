"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import *
from cesar.browser.models import *

def init_choices(obj, sFieldName, sSet, maybe_empty=False):
    if (obj.fields != None and sFieldName in obj.fields):
        obj.fields[sFieldName].choices = build_choice_list(sSet, maybe_empty=maybe_empty)
        obj.fields[sFieldName].help_text = get_help(sSet)



class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'User name'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder':'Password'}))


class VariableForm(forms.ModelForm):
    """Definition of one variable that is part of a set of variables under a [metavar]"""

    class Meta:
        model = Variable
        fields = "__all__"
        widgets={
          'value': forms.Textarea(attrs={'rows': 1, 'cols': 100})
          }


class GroupingForm(forms.ModelForm):
    """Definition of one variable that is part of a set of variables under a [metavar]"""

    class Meta:
        model = Grouping
        fields = "__all__"
        widgets={
          'value': forms.Textarea(attrs={'rows': 1, 'cols': 100})
          }


class TagsetForm(forms.ModelForm):
    """Definition of one tagset (part of a [metavar])"""

    class Meta:
        model = Tagset
        fields = "__all__"
        widgets={
          'definition': forms.TextInput(attrs={'size': 100})
          }


class PartForm(forms.ModelForm):
    """Size the input boxes and textarea for the form"""

    class Meta:
        model = Part
        fields = "__all__"
        widgets={'name': forms.TextInput(attrs={'size': 15}),
                 'dir':  forms.TextInput(attrs={'size': 15}),
                 'descr': forms.Textarea(attrs={'rows': 1}),
                 'url': forms.TextInput(attrs={'size': 40}),
                 'metavar': forms.Select(attrs={'size': 1}),
                 'corpus': forms.Select(attrs={'size': 1})
            }


class ConstituentNameTransForm(forms.ModelForm):
    """Constituent name sizing"""

    class Meta:
        model = ConstituentNameTrans
        fields = "__all__"
        widgets={'lng': forms.Select(attrs={'size': 1}),
                 'descr': forms.Textarea(attrs={'rows': 1})
            }


class TextAdminForm(forms.ModelForm):
    """Admin [Text] form"""

    class Meta:
        model = Text
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(TextAdminForm, self).__init__(*args, **kwargs)
        init_choices(self, 'format', CORPUS_FORMAT)


class TextForm(forms.ModelForm):
    """Non-admin view and change text metadata"""

    class Meta:
        model = Text
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(TextForm, self).__init__(*args, **kwargs)
        init_choices(self, 'format', CORPUS_FORMAT)
        for field in self.fields:
            wClass = 'vTextField' 
            if isinstance(self.fields[field].widget, NumberInput):
                wClass = 'vIntegerField'
            elif isinstance(self.fields[field].widget, Select):
                wClass = ''
            elif isinstance(self.fields[field].widget, Textarea):
                wClass = ''
               
            # Adapt the field type by adding a class
            if wClass != '':
                self.fields[field].widget.attrs.update({'class': wClass})


class PartSearchForm(forms.ModelForm):

    search = forms.CharField(label=_("Corpus name"))
    sortOrder = forms.CharField(label=_("Sort Order"), initial="metavar")
    part = forms.CharField(label=_("Corpus part"))
    metavar = forms.CharField(label=_("Meta variable"))

    class Meta:

        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = Part
        fields = "__all__"    # ('gloss', 'optdialect')


class TextSearchForm(forms.ModelForm):
    """Search for one text in a particular language/corpus/part/genre etc"""

    # Additional fields
    search = forms.CharField(label=_("Text name"))
    sortOrder = forms.CharField(label=_("Sort Order"), initial="metavar")
    language = forms.CharField(label=_("Language"))
    corpus = forms.CharField(label=_("Corpus"))
    part = forms.CharField(label=_("Section"))

    class Meta:

        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = Text
        fields = "__all__"    # Standard fields

