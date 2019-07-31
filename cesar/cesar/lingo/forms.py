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


class ParticipantForm(ModelForm):

    class Meta:
        model = Participant
        fields = ['ptcpid', 'age', 'gender', 'engfirst', 'lngfirst', 'lngother', 'edu']
        widgets={'ptcpid':      forms.TextInput(attrs={'style': 'width: 20%;', 'placeholder':'Your participant ID'}),
                 'age':         forms.TextInput(attrs={'style': 'width: 20%;', 'placeholder':'Age (number)'}),
                 'gender':      forms.Select(),
                 'engfirst':    forms.Select(),
                 'lngfirst':    forms.TextInput(attrs={'style': 'width: 50%;', 'placeholder':'Your first language'}),
                 'lngother':    forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'List other languages you know'}),
                 'edu':         forms.Select()
                 }
