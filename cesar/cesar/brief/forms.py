"""
Definition of forms for the BRIEF app.
"""

from django import forms
from django.forms import ModelForm, formset_factory, modelformset_factory, BaseFormSet
from django.forms.widgets import Textarea

# Application specific
from cesar.brief.models import *

class ProjectForm(ModelForm):

    class Meta:
        model = Project
        fields = ['name', 'description', 'status', 'ptype']
        widgets={'name':        forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'Name of this project...'}),
                 'description': forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'Description of the project...'}),
                 'status':      forms.Select(attrs={'style': 'width: 100%;'}),
                 'ptype':       forms.Select(attrs={'style': 'width: 100%;'})
                 }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(ProjectForm, self).__init__(*args, **kwargs)

        self.fields['name'].required = False
        self.fields['description'].required = False
        self.fields['ptype'].required = False
        self.fields['status'].required = False
        self.fields['status'].choices = build_abbr_list(PROJECT_STATUS)
        self.fields['ptype'].choices = build_abbr_list(PROJECT_PROGRESS)

