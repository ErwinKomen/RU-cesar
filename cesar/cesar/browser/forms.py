"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from cesar.browser.models import *

class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'User name'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder':'Password'}))


class VariableForm(forms.ModelForm):
    """Definition of one variable that is part of a set of variables under a [metavar]"""

    class Meta:
        model = Variable
        fields = "__all__"
        widgets={
          'value': forms.Textarea(attrs={'rows': 1, 'cols': 100})
          }


class GroupingForm(forms.ModelForm):
    """Definition of one variable that is part of a set of variables under a [metavar]"""

    class Meta:
        model = Grouping
        fields = "__all__"
        widgets={
          'value': forms.Textarea(attrs={'rows': 1, 'cols': 100})
          }


class TagsetForm(forms.ModelForm):
    """Definition of one tagset (part of a [metavar])"""

    class Meta:
        model = Tagset
        fields = "__all__"
        widgets={
          'definition': forms.TextInput(attrs={'size': 100})
          }


class PartForm(forms.ModelForm):
    """Size the input boxes and textarea for the form"""

    class Meta:
        model = Part
        fields = "__all__"
        widgets={'name': forms.TextInput(attrs={'size': 15}),
                 'dir':  forms.TextInput(attrs={'size': 15}),
                 'descr': forms.Textarea(attrs={'rows': 1}),
                 'url': forms.TextInput(attrs={'size': 40}),
                 'metavar': forms.Select(attrs={'size': 1}),
                 'corpus': forms.Select(attrs={'size': 1})
            }


class ConstituentNameTransForm(forms.ModelForm):
    """Constituent name sizing"""

    class Meta:
        model = ConstituentNameTrans
        fields = "__all__"
        widgets={'lng': forms.Select(attrs={'size': 1}),
                 'descr': forms.Textarea(attrs={'rows': 1})
            }
