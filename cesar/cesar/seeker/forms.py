"""
Definition of forms for the SEEKER app.
"""

from django import forms
#from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import ModelForm, formset_factory, modelformset_factory, BaseFormSet
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
SEARCHSIMPLE_POS = [('', 'first'), ('1', 'first'), ('2', 'second'), ('last()', 'last')]
SEARCHSIMPLE_SKIP = [('', 'none'), ('e', 'empty'), ('c', 'conj'), ('e_c', 'empty + conj')]


rAlphaNumeric = re.compile(r"^[0-9a-zA-Z_]*$")

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
    # WE USE A FIXED FUNCTION
    # OLD: function_sc = forms.ChoiceField(choices=SEARCHMAIN_CNS_FUNCTIONS, required = True)
    # Grammatical category to look for
    cat_incl = forms.CharField(required=True, widget=SeekerTextarea(attrs={'rows': 1, 'cols': 40, 'style': 'height: 30px;'}))
    # Optional category to exclude
    cat_excl = forms.CharField(required=False, widget=SeekerTextarea(attrs={'rows': 1, 'cols': 40, 'style': 'height: 30px;'}))

    class Meta:
        model = Construction
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(ConstructionCnsForm, self).__init__(*args, **kwargs)
        # Get the instance
        if 'instance' in kwargs and 'cat_incl' in self.fields:
            instance = kwargs['instance']

            # Get the obligatory [cat_incl] value
            sCatIncl = instance.search.value
            self.fields['cat_incl'].initial = sCatIncl
            # Get the optional [cat_excl] value
            if 'cat_excl' in self.fields:
                sCatExcl = instance.search.exclude
                self.fields['cat_excl'].initial = sCatExcl

    def is_valid(self):
        # Do default is valid
        valid = super(ConstructionCnsForm, self).is_valid()
        return valid


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

        # Initial validation
        valid = super(VarDefForm, self).is_valid()

        # Return the final validation
        return valid

    def clean_variable_ptr(self):
        data = self.cleaned_data['variable_ptr']

    def check_order(self):
        # Initialisations
        oErr = ErrHandle()
        valid = True
        # Make sure we get the cleaned_data
        cd = self.cleaned_data  # The cleaned data
        obj = self.instance     # This is a VarDef instance
        # Check the order
        return obj.check_order(cd['ORDER'])


class CvarForm(ModelForm):
    """The VALUES of construction variables"""

    file_source = forms.FileField(label="Specify which file should be loaded")
    # copyto = forms.ChoiceField((), required=False)
    copyto = None
    targetid = "research_part_43"
    target = "43"
    sumid = 'variable43'
    tableid = 'variable43t'
    url_edit = ""
    url_new = ""
    url_summary = ""
    url_table = ""

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
        self.fields['file_source'].required = False

        # nOT SURE if this is needed:
        # self.fields['file_source'].required = False

        # Get the gateway...
        if self.instance and self.instance.construction and self.instance.construction.gateway:
            gateway = self.instance.construction.gateway
            # Adapt the list of global variables
            self.fields['gvar'].queryset = GlobalVariable.objects.filter(gateway=gateway).order_by('name')
        # self.fields['copyto'].required = False
        # make sure all the available function-definitions are shown
        self.fields['functiondef'].queryset = FunctionDef.get_list()
        # Provide values for url_edit and url_new if possible
        if self.instance and self.instance != None and self.instance.id != None:
            self.url_edit = reverse(self.targetid, kwargs={"object_id": self.instance.id})
            self.url_summary = reverse(self.sumid, kwargs={"object_id": self.instance.id})
            self.url_table = reverse(self.tableid, kwargs={"object_id": self.instance.id})
        # THe url for new can always be given
        self.url_new = reverse(self.targetid)


class FunctionForm(ModelForm):
    """Specify the function the user wants to choose"""
    copyto = forms.ChoiceField(choices=(), required=False)

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
        fields = ['name', 'text', 'order', 'argtype', 'argval', 'obltype', 'hasoutputtype']
        widgets={
          'text': Textarea(attrs={'rows': 1, 'cols': 60, 'style': 'height: 30px;'}),
          'argval': Textarea(attrs={'rows': 1, 'cols': 10, 'style': 'height: 30px;'})
          }

    def __init__(self, *args, **kwargs):
        super(ArgumentDefForm, self).__init__(*args, **kwargs)
        init_choices(self, 'argtype', SEARCH_ARGTYPE, bUseAbbr=True)


class FunctionCodeForm(ModelForm):
    """The specification of the Xquery output of a function"""

    format = forms.ChoiceField(choices=build_abbr_list(CORPUS_FORMAT), required=True)

    class Meta:
        model = FunctionCode
        fields = ['format', 'xquery']
        widgets={
          'xquery': Textarea(attrs={'rows': 2, 'cols': 100, 'style': 'height: 30px; font-size: 13px; font-family: monospace; color: brown;'})
          }

    def __init__(self, *args, **kwargs):
        super(FunctionCodeForm, self).__init__(*args, **kwargs)
        init_choices(self, 'format', CORPUS_FORMAT, bUseAbbr=True)


class ArgumentForm(ModelForm):
    """The argument to a function"""

    argtype = forms.ChoiceField(choices=SEARCH_ARGTYPE, required=True)
    targetid = ""   # e.g. research_part_44
    target = ""     # E.g. '44'
    url_edit = ""
    url_new = ""

    class Meta:
        model = Argument
        fields = ['argumentdef', 'argtype', 'argval', 'gvar', 'cvar', 'dvar', 'raxis', 'rcond', 'rconst', 'function', 'functiondef']
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
        self.fields['raxis'].required = False
        self.fields['rcond'].required = False
        self.fields['rconst'].required = False
        self.fields['function'].required = False
        self.fields['functiondef'].required = False
        # define lists
        self.fields['functiondef'].queryset=FunctionDef.get_list()
        self.fields['raxis'].queryset=Relation.get_subset('axis')
        self.fields['rcond'].queryset=Relation.get_subset('cond')
        self.fields['rconst'].queryset=Relation.get_subset('const')


class ConditionForm(ModelForm):
    """The argument to a function"""

    file_source = forms.FileField(label="Specify which file should be loaded")
    condtype = forms.ChoiceField(choices=SEARCH_CONDTYPE, required=True)
    targetid = "research_part_62"
    target = "62"
    sumid = 'condition63'
    tableid = 'condition63t'
    url_edit = ""
    url_new = ""
    url_summary = ""
    url_table = ""

    class Meta:
        model = Condition
        fields = ['name', 'description', 'condtype', 'include', 'variable', 'function', 'functiondef']
        widgets={
          'description': SeekerTextarea(attrs={'rows': 1, 'cols': 40, 'style': 'height: 30px;'})
          }

    def __init__(self, gateway, *args, **kwargs):
        super(ConditionForm, self).__init__(*args, **kwargs)
        init_choices(self, 'condtype', SEARCH_CONDTYPE, bUseAbbr=True)
        # Set the initial querysets
        self.fields['variable'].queryset = VarDef.get_restricted_vardef_list( gateway.get_vardef_list(), 'bool')
        self.fields['functiondef'].queryset = FunctionDef.get_functions_with_type('bool') # FunctionDef.get_list()
        # Set required and optional fields
        self.fields['name'].required = True
        self.fields['description'].required = False
        self.fields['condtype'].required = True
        self.fields['variable'].required = False
        self.fields['function'].required = False
        self.fields['include'].required = False
        self.fields['functiondef'].required = False
        self.fields['file_source'].required = False
        # Provide values for url_edit and url_new if possible
        if self.instance and self.instance != None and self.instance.id != None:
            self.url_edit = reverse(self.targetid, kwargs={"object_id": self.instance.id})
            self.url_summary = reverse(self.sumid, kwargs={"object_id": self.instance.id})
            self.url_table = reverse(self.tableid, kwargs={"object_id": self.instance.id})
        # THe url for new can always be given
        self.url_new = reverse(self.targetid)


class FeatureForm(ModelForm):
    """The argument to a function"""

    file_source = forms.FileField(label="Specify which file should be loaded")
    feattype = forms.ChoiceField(choices=SEARCH_FEATTYPE, required=True)
    targetid = "research_part_72"
    target = "72"
    sumid = 'feature73'
    tableid = 'feature73t'
    url_edit = ""
    url_new = ""
    url_summary = ""
    url_table = ""

    class Meta:
        model = Feature
        fields = ['name', 'description', 'feattype', 'include', 'variable', 'function', 'functiondef']
        widgets={
          'description': SeekerTextarea(attrs={'rows': 1, 'cols': 40, 'style': 'height: 30px;'})
          }

    def __init__(self, gateway, *args, **kwargs):
        vardef_str_list = kwargs.pop('vardef_str_list', [])
        fundef_str_list = kwargs.pop('fundef_str_list', [])
        super(FeatureForm, self).__init__(*args, **kwargs)
        init_choices(self, 'feattype', SEARCH_FEATTYPE, bUseAbbr=True)
        # Set the initial querysets
        self.fields['variable'].queryset = vardef_str_list # VarDef.get_restricted_vardef_list( gateway.get_vardef_list(), 'str')
        self.fields['functiondef'].queryset = fundef_str_list # FunctionDef.get_functions_with_type('str') # FunctionDef.get_list()
        # Set required and optional fields
        self.fields['name'].required = True
        self.fields['description'].required = False
        self.fields['feattype'].required = True
        self.fields['variable'].required = False
        self.fields['function'].required = False
        self.fields['include'].required = False
        self.fields['functiondef'].required = False
        self.fields['file_source'].required = False
        # Provide values for url_edit and url_new if possible
        if self.instance and self.instance != None and self.instance.id != None:
            self.url_edit = reverse(self.targetid, kwargs={"object_id": self.instance.id})
            self.url_summary = reverse(self.sumid, kwargs={"object_id": self.instance.id})
            self.url_table = reverse(self.tableid, kwargs={"object_id": self.instance.id})
        # THe url for new can always be given
        self.url_new = reverse(self.targetid)

    def clean_name(self):
        """Check the 'name' field"""

        sName = self.cleaned_data['name']
        # Allow only alphanumeric and underscore
        if not rAlphaNumeric.match(sName):
            raise forms.ValidationError("The name of a feature must be alphanumeric")

        return sName


class SeekerResearchForm(ModelForm):
    # A research form should also have the Word/Constituent choice
    targetType = forms.ChoiceField(choices=TARGET_TYPE_CHOICES, required=True)

    # Make sure we take over the actual Research elements,
    #   but exclude the one-to-one 'gateway' link
    class Meta:
        model = Research
        fields = ['name', 'purpose', 'targetType', 'group']
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


class SeekerResGroupForm(ModelForm):
    class Meta:
        model = ResGroup
        fields = ['name', 'description', 'parent']
        widgets={
          'description': SeekerTextarea(attrs={'rows': 1, 'cols': 100, 'style': 'height: 30px;'})
          }


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


class SimpleSearchForm(forms.Form):
    baresimple = forms.CharField(label=_("Name"), required=False,
                    widget=forms.TextInput(attrs={'placeholder': 'Name for this simple search', 'style': 'width: 100%;'}))
    description = forms.CharField(label=_("Description"), required=False,
                    widget=forms.TextInput(attrs={'placeholder': 'Short description of this search', 'style': 'width: 100%;'}))
    targetType = forms.ChoiceField(label=_("Search type"), choices=TARGET_TYPE_CHOICES, required = True)
    searchwords = forms.CharField(label=_("Word(s) to be found"), required=False)
    searchlemma = forms.CharField(label=_("Lemma to be found"), required=False)
    searchpos = forms.CharField(label=_("Constituent categorie(s) to be found"), required = False)
    searchexc = forms.CharField(label=_("Constituent categorie(s) to be excluded"), required = False)
    searchrel = forms.CharField(label=_("Related constituent(s)"), required = False)
    searchcql = forms.CharField(required = False, widget=SeekerTextarea(attrs={'rows': 3, 'cols': 80, 'style': 'height: 90px;'}))


class RelatedForm(forms.Form):
    """One 'related' constituent definition for SimpleSearch"""

    name = forms.CharField(label=_("Short name"), required = True,
                           widget=forms.TextInput(attrs={'placeholder': 'Short name'}))
    cat = forms.CharField(label=_("Category"), required = False,
                           widget=forms.TextInput(attrs={'placeholder': 'Constituent category', 'style': 'width: 100%;'}))
    raxis = forms.ChoiceField(label=_("Relation"), required = True)
    towards = forms.ChoiceField(label=_("Towards constituent"), required = True)
    pos = forms.ChoiceField(label=_("Position"), required = False)
    skip = forms.ChoiceField(label=_("Skipping"), required=False)
    reltext = forms.CharField(label=_("Text like"), required=False,
                           widget=forms.TextInput(attrs={'placeholder': 'Constituent text', 'style': 'width: 100%;'}))
    rellemma = forms.CharField(label=_("Lemma"), required=False,
                           widget=forms.TextInput(attrs={'placeholder': 'Lemma', 'style': 'width: 100%;'}))

    def __init__(self, *args, **kwargs):
        super(RelatedForm, self).__init__(*args, **kwargs)
        # Initial choices for 'raxis'
        self.fields['raxis'].choices = Relation.get_choices('axis')
        # Initial default choice for 'towards'
        self.fields['towards'].choices = [ ('search', 'Search Hit') ]
        # Initial choices for 'pos'
        self.fields['pos'].choices = SEARCHSIMPLE_POS
        # Initial choices for 'skip'
        self.fields['skip'].choices = SEARCHSIMPLE_SKIP

    def get_raxis_display(self):
        if 'raxis' in self.initial:
            k = self.initial['raxis']
            v = next(tp[1] for tp in self.fields['raxis'].choices if str(tp[0]) == k)
        else:
            v = "Bad raxis: build afresh"
        return v

    def get_towards_display(self):
        if 'towards' in self.initial:
            k = self.initial['towards']
            v = next(tp[1] for tp in self.fields['towards'].choices if str(tp[0]) == k)
        else:
            v = "Bad towards: build afresh"
        return v

    def get_pos_display(self):
        if 'pos' in self.initial:
            k = self.initial['pos']
            v = next(tp[1] for tp in self.fields['pos'].choices if str(tp[0]) == k)
        else:
            v = "Bad pos: build afresh"
        return v

    def get_skip_display(self):
        if 'skip' in self.initial:
            k = self.initial['skip']
            v = next(tp[1] for tp in self.fields['skip'].choices if str(tp[0]) == k)
        else:
            v = "Bad skip: build afresh"
        return v

     
class UploadFileForm(forms.Form):
    file_source = forms.FileField(label="Specify which file should be loaded")
