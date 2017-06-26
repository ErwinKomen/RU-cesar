"""
Definition of forms for the SEEKER app.
"""

from django import forms
from django.forms import ModelForm, formset_factory, modelformset_factory
from cesar.seeker.models import *

WORD_ORIENTED = 'w'
CONSTITUENT_ORIENTED = 'c'
TARGET_TYPE_CHOICES = (
    (WORD_ORIENTED, 'Word(s)'),
    (CONSTITUENT_ORIENTED, 'Constituent(s)'),
)

SEARCHMAIN_WRD_FUNCTIONS = (
        ('w-m', 'Word matches'),
        ('wn-m', 'Next word matches'),
    )
SEARCHMAIN_CNS_FUNCTIONS = (
        ('c-m', 'Category matches'),
        ('c--m', 'Child category matches'),
    )


class VariableForm(ModelForm):
    class Meta:
        model = Variable
        fields = ['name', 'description']


class GatewayForm(ModelForm):
    class Meta:
        model = Gateway
        fields = ['name', 'description']


class ConstructionWrdForm(ModelForm):
    function_sc = forms.ChoiceField(choices=SEARCHMAIN_WRD_FUNCTIONS, required = True)
    value = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 1, 'cols': 40}))
    class Meta:
        model = Construction
        fields = ['name', 'search']


class ConstructionCnsForm(ModelForm):
    function_sc = forms.ChoiceField(choices=SEARCHMAIN_CNS_FUNCTIONS, required = True)
    value = forms.CharField(required=True)
    class Meta:
        model = Construction
        fields = ['name', 'search']
        widgets={
          'value': forms.Textarea(attrs={'rows': 2, 'cols': 40})
          }


class SeekerResearchForm(ModelForm):
    # A research form should also have the Word/Constituent choice
    targetType = forms.ChoiceField(choices=TARGET_TYPE_CHOICES, required=True)

    # Make sure we take over the actual Research elements
    class Meta:
        model = Research
        fields = '__all__'
        widgets={
          'purpose': forms.Textarea(attrs={'rows': 1, 'cols': 100})
          }


