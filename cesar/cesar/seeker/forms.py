"""
Definition of forms for the SEEKER app.
"""

from django import forms
from django.forms import ModelForm, formset_factory, modelformset_factory
from cesar.seeker.widgets import SeekerTextarea
from cesar.seeker.models import *
from cesar.browser.models import build_choice_list, get_help

SEARCHMAIN_WRD_FUNCTIONS = (
        ('w-m', 'Word matches'),
        ('wn-m', 'Next word matches'),
    )
SEARCHMAIN_CNS_FUNCTIONS = (
        ('c-m', 'Category matches'),
        ('c--m', 'Child category matches'),
    )

def init_choices(obj, sFieldName, sSet, maybe_empty=False):
    if (obj.fields != None and sFieldName in obj.fields):
        obj.fields[sFieldName].choices = build_choice_list(sSet, maybe_empty=maybe_empty)
        obj.fields[sFieldName].help_text = get_help(sSet)


class VariableForm(ModelForm):
    class Meta:
        model = Variable
        fields = ['name', 'description']


class GatewayForm(ModelForm):
    class Meta:
        model = Gateway
        fields = ['name', 'description']

    def is_valid(self):
        # Do default is valid
        valid = super(GatewayForm, self).is_valid()

        # If it's False, return
        if not valid: return valid

        # Otherwise: try myself.
        cd = self.cleaned_data
        obj = self.instance
        if obj == None or obj.name == "":
            return False
        else:
            return True


class ConstructionWrdForm(ModelForm):
    # function_sc = forms.ChoiceField(choices=SEARCHMAIN_WRD_FUNCTIONS, required = True)
    value = forms.CharField(required=True, widget=SeekerTextarea(attrs={'rows': 1, 'cols': 40}))
    class Meta:
        model = Construction
        fields = ['name']

    def __init__(self, *args, **kwargs):
        # Start by executing the standard handling
        super(ConstructionWrdForm, self).__init__(*args, **kwargs)
        # Get the instance
        if 'instance' in kwargs and 'value' in self.fields:
            instance = kwargs['instance']

            # Get the value
            sValue = instance.search.value
            # Get the number of lines to display it properly
            iLines = len( sValue.split('\n'))
            if iLines == 0: iLines = 1
            # Set the number of lines
            self.fields['value'].widget.attrs['rows'] = iLines
            # Set the initial value

            self.fields['value'].initial = sValue

    def is_valid(self):
        # Do default is valid
        valid = super(ConstructionWrdForm, self).is_valid()
        return valid
            

class ConstructionCnsForm(ModelForm):
    function_sc = forms.ChoiceField(choices=SEARCHMAIN_CNS_FUNCTIONS, required = True)
    value = forms.CharField(required=True, widget=SeekerTextarea(attrs={'rows': 1, 'cols': 40}))
    class Meta:
        model = Construction
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(ConstructionCnsForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance:
            owner = instance.gateway


class GvarForm(ModelForm):
    """The definition and value of global variables"""

    class Meta:
        model = GlobalVariable
        fields = ['name', 'description', 'value']
        widgets={
          'description': SeekerTextarea(attrs={'rows': 1, 'cols': 40}),
          'value': SeekerTextarea(attrs={'rows': 2, 'cols': 40})
          }

    def is_valid(self):
        """Return true if this form is valid"""
        valid = super(GvarForm, self).is_valid()
        return valid


class VarDefForm(ModelForm):
    """The DEFINITION of construction variables (not their values)"""

    class Meta:
        model = VarDef
        fields = ['name', 'description']
        widgets={
          'description': SeekerTextarea(attrs={'rows': 1, 'cols': 70})
          }

    def is_valid(self):
        """Return true if this form is valid"""
        valid = super(VarDefForm, self).is_valid()
        return valid


class CvarForm(ModelForm):
    """The VALUES of construction variables"""
    # type = forms.ChoiceField(choices=build_choice_list(SEARCH_VARIABLE_TYPE), required=True)

    class Meta:
        model = ConstructionVariable
        fields = ['type', 'svalue', 'gvar', 'function', 'functiondef']
        widgets={
          'svalue': SeekerTextarea(attrs={'rows': 1, 'cols': 70}),
          'functiondef': forms.Select()
          }

    def __init__(self, *args, **kwargs):
        super(CvarForm, self).__init__(*args, **kwargs)
        init_choices(self, 'type', SEARCH_VARIABLE_TYPE)
        # Set required and optional fields
        self.fields['type'].required = True
        self.fields['gvar'].required = False
        self.fields['function'].required = False
        self.fields['functiondef'].required = False
        self.fields['functiondef'].queryset = FunctionDef.objects.all()


class FunctionForm(ModelForm):
    """Specify the function the user wants to choose"""

    class Meta:
        model = Function
        fields = ['functiondef']
        widgets={
            'functiondef': forms.Select()
            }

    def __init__(self, *args, **kwargs):
        super(FunctionForm, self).__init__(*args, **kwargs)
        self.fields['functiondef'].queryset=FunctionDef.objects.all()


class ArgumentDefForm(ModelForm):
    """The specification of an argument to a function"""

    class Meta:
        model = ArgumentDef
        fields = ['name', 'text']


class ArgumentForm(ModelForm):
    """The argument to a function"""

    class Meta:
        model = Argument
        fields = ['argtype', 'argval', 'gvar', 'cvar', 'function']


class SeekerResearchForm(ModelForm):
    # A research form should also have the Word/Constituent choice
    targetType = forms.ChoiceField(choices=TARGET_TYPE_CHOICES, required=True)

    # Make sure we take over the actual Research elements,
    #   but exclude the one-to-one 'gateway' link
    class Meta:
        model = Research
        fields = ['name', 'purpose', 'targetType']
        widgets={
          'purpose': SeekerTextarea(attrs={'rows': 1, 'cols': 100})
          }

    def __init__(self, *args, **kwargs):
        # Start by executing the standard handling
        super(SeekerResearchForm, self).__init__(*args, **kwargs)

        ## get the post-data
        #data = args[0] if args else kwargs.get('data', None)

        ## Do we have data?
        #gw = None
        #if data:
        #    # There is POST data, so fill the forms with the required information
        #    self.gateway_data = {key: data[key] for key in data if key.startswith('gateway-')}
        #    if hasattr(self.instance, 'gateway'):
        #        gw = self.instance.gateway
        #    elif 'gateway-name' in self.gateway_data:
        #        gw = Gateway(name=self.gateway_data['gateway-name'], description=self.gateway_data['gateway-description'])
        #        gw.save()
        #    if gw == None:
        #        self.gateway_form = GatewayForm(prefix='gateway', data=self.gateway_data)
        #    else:
        #        self.gateway_form = GatewayForm(
        #            instance = gw,
        #            prefix='gateway',
        #            data=self.gateway_data
        #    )
        #else:
        #    # Didn't get any POST data: process the GET instance
        #    # Fill the form with the gateway data, or create a blank form
        #    if hasattr(self.instance, 'gateway') and  self.instance.gateway:
        #        # There is a gateway, so use it
        #        self.gateway_form = GatewayForm(
        #            instance = self.instance.gateway,
        #            prefix='gateway'
        #        )
        #    else:
        #        # Create a new form
        #        self.gateway_form = GatewayForm(prefix='gateway')

    def is_valid(self):
        #if not self.gateway_form.is_valid():
        #    return False
        return super(SeekerResearchForm, self).is_valid()

    #def clean(self):
    #    if not self.gateway_form.is_valid():
    #        raise forms.ValidationError("Gateway not valid")



    #def has_changed(self):
    #    return super(SeekerResearchForm,self).has_changed() or self.gateway_form.has_changed()


