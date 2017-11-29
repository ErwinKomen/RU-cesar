"""
Definition of forms for the SEEKER app.
"""

from django import forms
from django.db.models import Q
from django.forms import ModelForm, formset_factory, modelformset_factory
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _
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

def init_choices(obj, sFieldName, sSet, maybe_empty=False, bUseAbbr=False):
    if (obj.fields != None and sFieldName in obj.fields):
        if bUseAbbr:
            obj.fields[sFieldName].choices = build_abbr_list(sSet, maybe_empty=maybe_empty)
        else:
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


class KwicFilterForm(ModelForm):
    string_fields = ['Cat', 'TextId', 'Author', 'Title', 'Date']
    number_fields = ['Size']
    operator = forms.ChoiceField(choices=SEARCH_FILTEROPERATOR, required=True)
    field = forms.ChoiceField(choices=[], required=True)

    class Meta:
        model = KwicFilter
        fields = ['field', 'operator', 'value']
        widgets={ 'field': forms.Select() }

    def __init__(self, features, *args, **kwargs):
        # Start by executing the standard handling
        super(KwicFilterForm, self).__init__(*args, **kwargs)
        # Initialize the default 'fields' that can be chosen from
        choice_list = []
        for item in self.string_fields:
            choice_list.append( (item, item))
        for item in self.number_fields:
            choice_list.append( (item, item))
        for item in features:
            choice_list.append( (item, item))
        self.fields['field'].choices = choice_list
        init_choices(self, 'operator', SEARCH_FILTEROPERATOR, bUseAbbr=True)



class ConstructionWrdForm(ModelForm):
    # function_sc = forms.ChoiceField(choices=SEARCHMAIN_WRD_FUNCTIONS, required = True)
    value = forms.CharField(required=True, widget=SeekerTextarea(attrs={'rows': 1, 'cols': 40, 'style': 'height: 30px;'}))
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
    value = forms.CharField(required=True, widget=SeekerTextarea(attrs={'rows': 1, 'cols': 40, 'style': 'height: 30px;'}))
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
          'description': SeekerTextarea(attrs={'rows': 1, 'cols': 40, 'style': 'height: 30px;'}),
          'value': SeekerTextarea(attrs={'rows': 2, 'cols': 40, 'style': 'height: 30px;'})
          }

    def is_valid(self):
        """Return true if this form is valid"""
        valid = super(GvarForm, self).is_valid()
        return valid


class KwicForm(ModelForm):
    class Meta:
        model = Kwic
        fields = ['qc']


class VarDefForm(ModelForm):
    """The DEFINITION of construction variables (not their values)"""

    class Meta:
        model = VarDef
        fields = ['name', 'description']
        widgets={
          'description': SeekerTextarea(attrs={'rows': 1, 'cols': 70, 'style': 'height: 30px;'})
          }

    def is_valid(self):
        """Return true if this form is valid"""
        valid = super(VarDefForm, self).is_valid()
        return valid

    def clean_variable_ptr(self):
        data = self.cleaned_data['variable_ptr']



class CvarForm(ModelForm):
    """The VALUES of construction variables"""

    # copyto = forms.ChoiceField((), required=False)
    copyto = forms.ChoiceField()
    targetid = "research_part_43"
    target = "43"
    sumid = 'variable43'
    url_edit = ""
    url_new = ""
    url_summary = ""

    class Meta:
        model = ConstructionVariable
        fields = ['type', 'svalue', 'gvar', 'function', 'functiondef', 'construction']
        widgets={
          'svalue': SeekerTextarea(attrs={'rows': 1, 'cols': 70, 'style': 'height: 30px;'}),
          'functiondef': forms.Select(),
          'copyto': forms.Select()
          }

    def __init__(self, *args, **kwargs):
        super(CvarForm, self).__init__(*args, **kwargs)
        init_choices(self, 'type', SEARCH_VARIABLE_TYPE, bUseAbbr=True)
        # Set required and optional fields
        self.fields['type'].required = True
        self.fields['gvar'].required = False
        self.fields['function'].required = False
        self.fields['functiondef'].required = False
        self.fields['copyto'].required = False
        ## make sure only the 'gvar' elements under this particular gateway are shown
        #gateway = kwargs['instance'].construction.gateway
        #self.fields['gvar'].queryset = GlobalVariable.objects.filter(gateway=gateway)
        # make sure all the available function-definitions are shown
        self.fields['functiondef'].queryset = FunctionDef.get_list()
        # Provide values for url_edit and url_new if possible
        if self.instance and self.instance != None and self.instance.id != None:
            self.url_edit = reverse(self.targetid, kwargs={"object_id": self.instance.id})
            self.url_summary = reverse(self.sumid, kwargs={"object_id": self.instance.id})
        # THe url for new can always be given
        self.url_new = reverse(self.targetid)


class FunctionForm(ModelForm):
    """Specify the function the user wants to choose"""
    copyto = forms.ChoiceField((), required=False)

    class Meta:
        model = Function
        fields = ['functiondef', 'copyto']
        widgets={
            'functiondef': forms.Select(),
            'copyto': forms.Select()
            }

    def __init__(self, *args, **kwargs):
        super(FunctionForm, self).__init__(*args, **kwargs)
        self.fields['functiondef'].queryset=FunctionDef.get_list()
        self.fields['copyto'].required = False


class ArgumentDefForm(ModelForm):
    """The specification of an argument to a function"""

    argtype = forms.ChoiceField(choices=SEARCH_ARGTYPE, required=True)

    class Meta:
        model = ArgumentDef
        fields = ['name', 'text', 'order', 'argtype']
        widgets={
          'text': Textarea(attrs={'rows': 1, 'cols': 100, 'style': 'height: 30px;'})
          }

    def __init__(self, *args, **kwargs):
        super(ArgumentDefForm, self).__init__(*args, **kwargs)
        init_choices(self, 'argtype', SEARCH_ARGTYPE, bUseAbbr=True)


class ArgumentForm(ModelForm):
    """The argument to a function"""

    argtype = forms.ChoiceField(choices=SEARCH_ARGTYPE, required=True)
    targetid = ""   # e.g. research_part_44
    target = ""     # E.g. '44'
    url_edit = ""
    url_new = ""

    class Meta:
        model = Argument
        fields = ['argumentdef', 'argtype', 'argval', 'gvar', 'cvar', 'dvar', 'relation', 'function', 'functiondef']
        widgets={
          'argval': SeekerTextarea(attrs={'rows': 1, 'cols': 40, 'style': 'height: 30px;'})
          }

    def __init__(self, *args, **kwargs):
        super(ArgumentForm, self).__init__(*args, **kwargs)
        init_choices(self, 'argtype', SEARCH_ARGTYPE, bUseAbbr=True)
        # Set required and optional fields
        self.fields['argumentdef'].required = True
        self.fields['argtype'].required = True
        self.fields['cvar'].required = False
        self.fields['dvar'].required = False
        self.fields['gvar'].required = False
        self.fields['relation'].required = False
        self.fields['function'].required = False
        self.fields['functiondef'].required = False
        self.fields['functiondef'].queryset=FunctionDef.get_list()


class ConditionForm(ModelForm):
    """The argument to a function"""

    condtype = forms.ChoiceField(choices=SEARCH_CONDTYPE, required=True)
    targetid = "research_part_62"
    target = "62"
    sumid = 'condition63'
    url_edit = ""
    url_new = ""
    url_summary = ""

    class Meta:
        model = Condition
        fields = ['name', 'description', 'condtype', 'variable', 'function', 'functiondef']
        widgets={
          'description': SeekerTextarea(attrs={'rows': 1, 'cols': 40, 'style': 'height: 30px;'})
          }

    def __init__(self, gateway, *args, **kwargs):
        super(ConditionForm, self).__init__(*args, **kwargs)
        init_choices(self, 'condtype', SEARCH_CONDTYPE, bUseAbbr=True)
        # Set the initial querysets
        self.fields['variable'].queryset = gateway.get_vardef_list()
        self.fields['functiondef'].queryset = FunctionDef.get_list()
        # Set required and optional fields
        self.fields['name'].required = True
        self.fields['description'].required = False
        self.fields['condtype'].required = True
        self.fields['variable'].required = False
        self.fields['function'].required = False
        self.fields['functiondef'].required = False
        # Provide values for url_edit and url_new if possible
        if self.instance and self.instance != None and self.instance.id != None:
            self.url_edit = reverse(self.targetid, kwargs={"object_id": self.instance.id})
            self.url_summary = reverse(self.sumid, kwargs={"object_id": self.instance.id})
        # THe url for new can always be given
        self.url_new = reverse(self.targetid)


class SeekerResearchForm(ModelForm):
    # A research form should also have the Word/Constituent choice
    targetType = forms.ChoiceField(choices=TARGET_TYPE_CHOICES, required=True)

    # Make sure we take over the actual Research elements,
    #   but exclude the one-to-one 'gateway' link
    class Meta:
        model = Research
        fields = ['name', 'purpose', 'targetType']
        widgets={
          'purpose': SeekerTextarea(attrs={'rows': 1, 'cols': 100, 'style': 'height: 30px;'})
          }

    def __init__(self, *args, **kwargs):
        # Start by executing the standard handling
        super(SeekerResearchForm, self).__init__(*args, **kwargs)
        
    def is_valid(self):
        #if not self.gateway_form.is_valid():
        #    return False
        return super(SeekerResearchForm, self).is_valid()

class SharegForm(ModelForm):
    # A research form should also have the Word/Constituent choice
    permission = forms.ChoiceField(choices=SEARCH_PERMISSION, required=True)

    class Meta:
        model = ShareGroup
        fields = ['group', 'permission']

    def __init__(self, *args, **kwargs):
        super(SharegForm, self).__init__(*args, **kwargs)
        init_choices(self, 'permission', SEARCH_PERMISSION, bUseAbbr=True)


class QuantorSearchForm(ModelForm):

    # Additional fields
    textname = forms.CharField(label=_("Text name"))
    subcategory = forms.CharField(label=_("Sub category"))
    sortOrder = forms.CharField(label=_("Sort Order"), initial="text")
    minhits = forms.CharField(label=_("Minimum hits"))

    class Meta:

        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = Qsubinfo
        fields = "__all__"    # Standard fields

