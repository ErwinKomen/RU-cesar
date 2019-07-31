"""
Definition of forms for the LINGO app.
"""

from django import forms
from django.forms import ModelForm, formset_factory, modelformset_factory, BaseFormSet
from django.forms.widgets import Textarea

# Application specific
from cesar.lingo.models import *

class ExperimentForm(ModelForm):
    class Meta:
        model = Experiment
        fields = ['title', 'home', 'msg', 'consent' ]
        widgets={'title':   forms.TextInput(attrs={'style': 'width: 100%;'}),
                 'home':    forms.TextInput(attrs={'style': 'width: 20%;'}),
                 'msg':     forms.Textarea(attrs={'rows': 2, 'cols': 40, 'style': 'height: 80px; width: 100%;'}),
                 'consent':     forms.Textarea(attrs={'rows': 2, 'cols': 40, 'style': 'height: 80px; width: 100%;'})
                 }
