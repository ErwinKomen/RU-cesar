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
    """This is for uploading one or more files"""

    files_field = forms.FileField(label="Specify which file(s) should be loaded",
                                  widget=forms.ClearableFileInput(attrs={'multiple': True}))
    clamuser = forms.CharField(label="CLAM service user name")
    clampw = forms.CharField(max_length=32, widget=forms.PasswordInput)

