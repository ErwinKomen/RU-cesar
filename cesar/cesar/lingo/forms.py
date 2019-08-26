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


class AnswerForm(forms.Form):
    # The ID of the Participant (assigned by the Django system)
    ptcp_id = forms.CharField(label="Participant id", max_length=100)
    # A number of different answers
    answer1 = forms.CharField(label="Answer1", max_length=255)
    answer2 = forms.CharField(label="Answer2", max_length=255)
    answer3 = forms.CharField(label="Answer3", max_length=255)
    answer4 = forms.CharField(label="Answer4", max_length=255)
    answer5 = forms.CharField(label="Answer5", max_length=255)
    answer6 = forms.CharField(label="Answer6", max_length=255)
    answer7 = forms.CharField(label="Answer7", max_length=255)
    answer8 = forms.CharField(label="Answer8", max_length=255)
    answer9 = forms.CharField(label="Answer9", max_length=255)
