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
from cesar.basic.forms import BasicForm

# ========================================= WIDGETS ====================================================


class UserWidget(ModelSelect2MultipleWidget):
    model = User
    search_fields = [ 'username__icontains' ]

    def label_from_instance(self, obj):
        return obj.username

    def get_queryset(self):
        return User.objects.all().order_by('username').distinct()


class ConcrWidget(ModelSelect2MultipleWidget):
    model = FrogLink
    search_fields = [ 'name__icontains' ]
    qs = None

    def label_from_instance(self, obj):
        return obj.name

    def get_queryset(self):
        qs_this = FrogLink.objects.none()
        if not self.qs is None:
            qs_this = self.qs
        return qs_this


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


class ConcreteForm(BasicForm):
    concrlist = ModelMultipleChoiceField(queryset=None, required=False, 
        widget=ConcrWidget(attrs={'data-placeholder': 'Select multiple texts...', 'style': 'width: 100%;', 'class': 'searching'}))

    class Meta:
        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = FrogLink
        fields = []

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(ConcreteForm, self).__init__(*args, **kwargs)

        oErr = ErrHandle()
        try:
            # Initially allow all FrogLink objects
            qs = FrogLink.objects.all()
            self.fields['concrlist'].queryset = qs

            # Check if this is a specific instance
            if 'instance' in kwargs:
                instance = kwargs['instance']
                # It is, and we need to be sure to select the right queryset
                owner = instance.fdocs.owner
                qs = FrogLink.objects.filter(fdocs__owner=owner).exclude(id=instance.id).distinct()
                self.fields['concrlist'].queryset = qs
                self.fields['concrlist'].widget.qs = qs

        except:
            msg = oErr.get_error_message()
            oErr.DoError("ConcreteForm")
        return None


class FrogLinkForm(forms.ModelForm):
    ownlist = ModelMultipleChoiceField(queryset=None, required=False, 
                widget=UserWidget(attrs={'data-placeholder': 'Select multiple users...', 'style': 'width: 100%;', 'class': 'searching'}))
    concrlist = ModelMultipleChoiceField(queryset=None, required=False, 
        widget=ConcrWidget(attrs={'data-placeholder': 'Select multiple texts...', 'style': 'width: 100%;', 'class': 'searching'}))

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

        oErr = ErrHandle()
        try:
            # Make sure some are not obligatory
            self.fields['created'].required = False
            self.fields['name'].required = False
            self.fields['ownlist'].queryset = User.objects.all()

            # Initially allow all FrogLink objects
            qs = FrogLink.objects.all()
            self.fields['concrlist'].queryset = qs

            # Check if this is a specific instance
            if 'instance' in kwargs:
                instance = kwargs['instance']
                # It is, and we need to be sure to select the right queryset
                owner = instance.fdocs.owner
                qs = FrogLink.objects.filter(fdocs__owner=owner).exclude(id=instance.id).distinct()
                self.fields['concrlist'].queryset = qs
                self.fields['concrlist'].widget.qs = qs

                # Make sure the initial values are filled in correctly
                self.fields['concrlist'].initial = [x.id for x in instance.comparisons.all()]
        except:
            msg = oErr.get_error_message()
            oErr.DoError("FrogLinkForm")
        return None

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


class GenreForm(forms.ModelForm):
    class Meta:
        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = Genre
        fields = ['name']
        widgets = {
            'name':     forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Succinct name for this genre'})
            }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(GenreForm, self).__init__(*args, **kwargs)
        # Make sure some are not obligatory
        self.fields['name'].required = False


class ExpressionForm(forms.ModelForm):
    class Meta:
        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = Expression
        fields = ['full', 'score']
        widgets = {
            'full':     forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Enter the expression as plain text'}),
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


class WordlistForm(forms.ModelForm):
    class Meta:
        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = Wordlist
        fields = ['name', 'description', 'upload', 'sheet']
        widgets = {
            'name':         forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Name for this wordlist'}),
            'description':  forms.Textarea(attrs={'rows': 2, 'cols': 40, 'style': 'height: 80px; width: 100%;', 
                                                  'placeholder': 'Description of this wordlist...'}),
            'upload':       forms.FileInput(attrs={'style': 'width: 100%;', 'placeholder': 'Excel file'}),
            'sheet':        forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Name of worksheet within Excel file'}),
            }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(WordlistForm, self).__init__(*args, **kwargs)

        # Make sure some are not obligatory
        self.fields['name'].required = False
        self.fields['description'].required = False
        self.fields['upload'].required = False
        self.fields['sheet'].required = False


class WorddefForm(forms.ModelForm):
    class Meta:
        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = Worddef
        fields = ['stimulus', 'postag', 'm']
        widgets = {
            'stimulus':     forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Stimulus (word)'}),
            'postag':       forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'POS tag'}),
            'm':            forms.NumberInput(),
            }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(WorddefForm, self).__init__(*args, **kwargs)

        # Make sure some are not obligatory
        self.fields['stimulus'].required = False
        self.fields['postag'].required = False
        self.fields['m'].required = False


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

