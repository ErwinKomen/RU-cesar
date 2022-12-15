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
    clamuser = forms.CharField(label="CLAM service user name", required=False)
    clampw = forms.CharField(max_length=32, widget=forms.PasswordInput, required=False)


class UploadNexisForm(forms.Form):
    """This is for uploading one or more files for Nexis Uni """

    files_field = forms.FileField(label="Specify which file(s) should be loaded",
                                  widget=forms.ClearableFileInput(attrs={'multiple': True}))


class UploadOneFileForm(forms.Form):
    """This is for uploading one file"""

    file_field = forms.FileField(label="Specify which file should be imported",
                                  widget=forms.ClearableFileInput())


class UploadMwexForm(forms.Form):
    """This is for uploading one file"""

    file_source = forms.FileField(label="Specify which file should be imported",
                                  widget=forms.ClearableFileInput())


class UploadTwitterExcelForm(forms.Form):
    """This is for uploading one file"""

    file_source = forms.FileField(label="Specify which file should be imported",
                                  widget=forms.ClearableFileInput())
    dofiles = forms.CharField(max_length=32, required=False)


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


class LocTimeForm(forms.ModelForm):
    class Meta:
        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = LocTimeInfo
        fields = ['example', 'score']
        widgets = {
            'example':  forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Use * as wildcard when searching'}),
            'score':    forms.TextInput(attrs={'style': 'width: 100%;'})
            }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(LocTimeForm, self).__init__(*args, **kwargs)
        # Make sure some are not obligatory
        self.fields['example'].required = False
        self.fields['score'].required = False


class ExpressionForm(forms.ModelForm):
    class Meta:
        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = Expression
        fields = ['full', 'score']
        widgets = {
            'full':     forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Use * as wildcard when searching'}),
            'score':    forms.TextInput(attrs={'style': 'width: 100%;'})
            }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(ExpressionForm, self).__init__(*args, **kwargs)
        # Make sure some are not obligatory
        self.fields['full'].required = False
        self.fields['score'].required = False


class HomonymForm(forms.ModelForm):
    class Meta:
        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = Homonym
        fields = ['stimulus', 'postag', 'meaning', 'm']
        widgets = {
            'stimulus': forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Lemma of word'}),
            'postag':   forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Part-of-speech tag'}),
            'meaning':  forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Sense of meaning'}),
            'm':        forms.NumberInput(attrs={'style': 'width: 100%;', 'placeholder': 'Metric for this sense'})
            }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(HomonymForm, self).__init__(*args, **kwargs)
        # Make sure some are not obligatory
        self.fields['stimulus'].required = False
        self.fields['postag'].required = False
        self.fields['meaning'].required = False
        self.fields['m'].required = False

        return None


# ================= NEXIS FORMS =======================================

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

