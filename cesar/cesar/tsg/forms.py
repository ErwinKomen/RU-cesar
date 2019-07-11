"""
Definition of forms for the TSG app.
"""

from django import forms
from django.db.models import Q
from django.forms import ModelForm, formset_factory, modelformset_factory, BaseFormSet
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _

# Application specific
from cesar.tsg.models import *
from cesar.browser.models import build_choice_list, get_help

class TsgHandleForm(ModelForm):
    class Meta:
        model = TsgHandle
        fields = ['url', 'notes']
        widgets={'url':      forms.TextInput(attrs={'style': 'width: 100%;'}),
                 'notes':     forms.Textarea(attrs={'rows': 2, 'cols': 40, 'style': 'height: 80px; width: 100%;'})
                 }
