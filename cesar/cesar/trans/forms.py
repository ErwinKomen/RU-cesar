"""
Definition of forms for the TRANS app.
"""

from django import forms
from django.forms import ModelForm, formset_factory, modelformset_factory, BaseFormSet
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _

# Application specific
from cesar.woord.models import *

class TransForm(forms.Form):
    """This contains the text to be transliterated"""

    original = forms.CharField(label=_("Text"), required=False, 
                widget=forms.Textarea(attrs={'rows': 2, 'cols': 40, 'style': 'height: 80px; width: 100%;', 
                'placeholder':'The text that you would like to transliterate (may use markdown)...'}))

