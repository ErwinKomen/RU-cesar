"""
Definition of forms for the SEEKER app.
"""

from django import forms
#from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import ModelForm, formset_factory, modelformset_factory, BaseFormSet
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _

from cesar.doc.models import *

class UploadFilesForm(forms.Form):
    """This is for uploading one or more files for Concreteness"""

    files_field = forms.FileField(label="Specify which file(s) should be loaded",
                                  widget=forms.ClearableFileInput(attrs={'multiple': True}))
    clamuser = forms.CharField(label="CLAM service user name")
    clampw = forms.CharField(max_length=32, widget=forms.PasswordInput)


class UploadNexisForm(forms.Form):
    """This is for uploading one or more files for Nexis Uni """

    files_field = forms.FileField(label="Specify which file(s) should be loaded",
                                  widget=forms.ClearableFileInput(attrs={'multiple': True}))


class UploadOneFileForm(forms.Form):
    """This is for uploading one file"""

    file_field = forms.FileField(label="Specify which file should be imported",
                                  widget=forms.ClearableFileInput())


class NexisBatchForm(forms.ModelForm):

    class Meta:
        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = NexisBatch
        fields = ['created', 'count']
        widgets = {
            'count':    forms.TextInput(attrs={'style': 'width: 100%;'}),
            'created':  forms.DateTimeInput(attrs={'style': 'width: 100%;'})
            }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(NexisBatchForm, self).__init__(*args, **kwargs)
        # Make sure some are not obligatory
        self.fields['created'].required = False
        self.fields['count'].required = False
