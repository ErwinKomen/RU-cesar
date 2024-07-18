"""
Definition of forms for the TSG app.
"""

from django import forms
from django.db.models import Q
from django.forms import ModelForm, BaseFormSet, ModelMultipleChoiceField, ModelChoiceField, formset_factory, modelformset_factory
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _
from django_select2.forms import ModelSelect2MultipleWidget

# Application specific
from cesar.tsg.models import *
from cesar.basic.forms import BasicForm
from cesar.browser.models import build_choice_list, get_help

STATUS_TYPE = [('', 'All'), ('spe', 'Author defined'), ('non', 'No author defined')]


# ================================== Widgets ======================================================


class TsgHandleWidget(ModelSelect2MultipleWidget):
    model = TsgHandle
    search_fields = [ 'code__icontains', 'url__icontains']

    def label_from_instance(self, obj):
        return obj.code

    def get_queryset(self):
        qs = self.queryset
        if qs is None:
            qs = TsgHandle.objects.exclude(status='ini').order_by('code', 'url')
        else:
            qs = qs.order_by('code', 'url')
        return qs


# ================================== Forms ========================================================


class TsgHandleForm(BasicForm):
    """Form that serves for TsgHandle details and list views, including searches"""

    handle_ta = forms.CharField(label=_("Handle"), required=False, 
                widget=forms.TextInput(attrs={'class': 'typeahead searching input-sm', 
                                              'placeholder': 'Handle (use wildcards)...', 'style': 'width: 100%;'}))
    url_ta = forms.CharField(label=_("URL"), required=False, 
                widget=forms.TextInput(attrs={'class': 'typeahead searching input-sm', 
                                              'placeholder': 'Url (use wildcards)...', 'style': 'width: 100%;'}))
    handlelist  = ModelMultipleChoiceField(queryset=None, required=False, 
                    widget=TsgHandleWidget(attrs={'data-minimum-input-length': 0, 'data-placeholder': 'Select multiple handles...', 
                                                'style': 'width: 100%;'}))
    statuslist  = forms.ChoiceField(label=_("Author type"), required=False, 
                widget=forms.Select(attrs={'class': 'input-sm', 'placeholder': 'Type of Author...',  'style': 'width: 100%;', 'tdstyle': 'width: 150px;'}))    

    class Meta:
        model = TsgHandle
        fields = ['url', 'notes']
        widgets={'url':      forms.TextInput(attrs={'style': 'width: 100%;'}),
                 'notes':     forms.Textarea(attrs={'rows': 2, 'cols': 40, 'style': 'height: 80px; width: 100%;'})
                 }

    def __init__(self, *args, **kwargs):
        # Start by executing the standard handling
        super(TsgHandleForm, self).__init__(*args, **kwargs)
        oErr = ErrHandle()
        try:
            # Set the querysets
            self.fields['handlelist'].queryset = TsgHandle.objects.exclude(status='ini').order_by('code', 'url')
            self.fields['statuslist'].queryset = TsgHandle.objects.exclude(status='ini').order_by('code', 'url')
        except:
            msg = oErr.get_error_message()
            oErr.DoError("TsgHandleForm-init")
        return None

