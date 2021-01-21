"""
Definition of forms for the SEEKER app.
"""

from django import forms
#from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import ModelForm, formset_factory, modelformset_factory, BaseFormSet, ModelMultipleChoiceField
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _
from django_select2.forms import Select2MultipleWidget, ModelSelect2MultipleWidget, ModelSelect2TagWidget, ModelSelect2Widget, HeavySelect2Widget


from cesar.doc.models import *

# ========================================= WIDGETS ====================================================


class UserWidget(ModelSelect2MultipleWidget):
    model = User
    search_fields = [ 'username__icontains' ]

    def label_from_instance(self, obj):
        return obj.username

    def get_queryset(self):
        return User.objects.all().order_by('username').distinct()


# ================= FORMS =======================================

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


class FrogLinkForm(forms.ModelForm):
    ownlist = ModelMultipleChoiceField(queryset=None, required=False, 
                widget=UserWidget(attrs={'data-placeholder': 'Select multiple users...', 'style': 'width: 100%;', 'class': 'searching'}))

    class Meta:
        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = FrogLink
        fields = ['created', 'name']
        widgets = {
            'name':     forms.TextInput(attrs={'style': 'width: 100%;'}),
            'created':  forms.DateTimeInput(attrs={'style': 'width: 100%;'})
            }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(FrogLinkForm, self).__init__(*args, **kwargs)
        # Make sure some are not obligatory
        self.fields['created'].required = False
        self.fields['name'].required = False
        self.fields['ownlist'].queryset = User.objects.all()


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

