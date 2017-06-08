"""
Definition of forms for the SEEKER app.
"""

from django import forms
from django.forms import ModelForm, formset_factory, modelformset_factory
from cesar.seeker.models import *


class SeekerWizardForm1(forms.Form):
    WORD_ORIENTED = 'w'
    CONSTITUENT_ORIENTED = 'c'
    TARGET_TYPE_CHOICES = (
        (WORD_ORIENTED, 'Word(s)'),
        (CONSTITUENT_ORIENTED, 'Constituent(s)'),
    )

    searchTargetType = forms.ChoiceField(choices=TARGET_TYPE_CHOICES, required=True)


class SeekerWizardForm2(forms.Form):
    dit = forms.CharField()


class VariableForm(ModelForm):
    class Meta:
        model = Variable
        fields = ['name', 'description']


class GatewayForm(ModelForm):
    class Meta:
        model = Gateway
        fields = ['name', 'description']
