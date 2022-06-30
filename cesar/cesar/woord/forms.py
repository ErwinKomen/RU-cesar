"""
Definition of forms for the WOORD app.
"""

from django import forms
from django.forms import ModelForm, formset_factory, modelformset_factory, BaseFormSet
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _

# Application specific
from cesar.woord.models import *

class UserForm(forms.Form):
    """Allow a user to enter"""

    username = forms.CharField(label=_("Name"), required=False, widget=forms.TextInput(attrs={'style': 'width: 100%;', 
                'placeholder':'De gebruikersnaam die u heeft ontvangen...'}))

