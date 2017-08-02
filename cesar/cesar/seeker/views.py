"""
Definition of views for the SEEKER app.
"""

from django.db.models import Q
from django.forms import formset_factory
from django.forms import inlineformset_factory, BaseInlineFormSet, modelformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.core.exceptions import FieldDoesNotExist
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.base import RedirectView
from django.views.generic import ListView, View

# from formtools.wizard.views import SessionWizardView

from cesar.seeker.forms import GatewayForm, VariableForm, SeekerResearchForm, ConstructionWrdForm, GvarForm, VarDefForm, CvarForm, FunctionForm, ArgumentForm
from cesar.seeker.models import *
from cesar.settings import APP_PREFIX

paginateEntries = 20

class CustomInlineFormset(BaseInlineFormSet):
    def clean(self):
        super(CustomInlineFormset, self).clean()


class GatewayDetailView(DetailView):
    model = Gateway
    form_class = GatewayForm
    template_name = 'seeker/gateway_view.html'


class GatewayCreateView(CreateView):
    model = Gateway


class SeekerListView(ListView):
    model = Research
    template_name = 'seeker/research_list.html'
    paginate_by = paginateEntries
    entrycount = 0
    qs = None


def get_changeform_initial_data(model, request):
    """
    Get the initial form data.
    Unless overridden, this populates from the GET params.
    """
    initial = dict(request.GET.items())
    for k in initial:
        try:
            f = model._meta.get_field(k)
        except FieldDoesNotExist:
            continue
        # We have to special-case M2Ms as a list of comma-separated PKs.
        if isinstance(f, models.ManyToManyField):
            initial[k] = initial[k].split(",")
    return initial


class SeekerForm():
    """Forms to work with the Seeker App"""

    formset_list = []

    def add_formset(self, ModelFrom, ModelTo, FormModel):
        FactSet = inlineformset_factory(ModelFrom, ModelTo,form=FormModel, min_num=1, extra=0, can_delete=True, can_order=True)
        oFormset = {'factory': FactSet, 'formset': None}
        self.formset_list.append(oFormset)


class ResearchPart(View):
    # Initialisations:     
    arErr = []              # errors   
    template_name = None    # The template to be used
    form_validated = True   # Used for POST form validation
    savedate = None         # When saving information, the savedate is returned in the context
    add = False             # Are we adding a new record or editing an existing one?
    obj = None              # The instance of the MainModel
    MainModel = None        # The model that is mainly used for this form
    form_objects = []       # List of forms to be processed
    formset_objects = []    # List of formsets to be processed
    data = {'status': 'ok', 'html': ''}       # Create data to be returned    
    
    def post(self, request, object_id=None):
        # A POST request means we are trying to SAVE something
        self.initializations(request, object_id)

        if self.checkAuthentication(request):
            # Build the context
            context = dict(object_id = object_id, savedate=None)
            # Walk all the forms
            for formObj in self.form_objects:
                # Are we SAVING a NEW item?
                if self.add:
                    # We are saving a NEW item
                    formObj['forminstance'] = formObj['form'](request.POST, prefix=formObj['prefix'])
                else:
                    # We are saving an EXISTING item
                    # Determine the instance to be passed on
                    instance = self.get_instance(formObj['prefix'])
                    # Make the instance available in the form-object
                    formObj['instance'] = instance
                    # Get an instance of the form
                    formObj['forminstance'] = formObj['form'](request.POST, prefix=formObj['prefix'], instance=instance)
            # Iterate again
            for formObj in self.form_objects:
                # Check validity of form
                if formObj['forminstance'].is_valid():
                    # Save it preliminarily
                    instance = formObj['forminstance'].save(commit=False)
                    # The instance must be made available (even though it is only 'preliminary')
                    formObj['instance'] = instance
                    # Perform actions to this form BEFORE FINAL saving
                    self.before_save(formObj['prefix'], request, instance=instance)
                    # Perform the saving
                    instance.save()
                    # Put the instance in the form object
                    formObj['instance'] = instance
                    context['savedate']="saved at {}".format(datetime.now().strftime("%X"))
                else:
                    self.arErr.append(formObj['forminstance'].errors)
                    self.form_validated = False

                # Add instance to the context object
                context[formObj['prefix'] + "Form"] = formObj['forminstance']
            # Walk all the formset objects
            for formsetObj in self.formset_objects:
                formsetClass = formsetObj['formsetClass']
                prefix  = formsetObj['prefix']
                if self.add:
                    # Saving a NEW item
                    formset = formsetClass(request.POST, request.FILES, prefix=prefix)
                else:
                    # Saving an EXISTING item
                    instance = self.get_instance(prefix)
                    formset = formsetClass(request.POST, request.FILES, prefix=prefix, instance=instance)
                # Process all the forms in the formset
                self.process_formset(prefix, request, formset)
                # Store the instance
                formsetObj['formsetinstance'] = formset
                # Is the formset valid?
                if formset.is_valid():
                    # Make sure all changes are saved in one database-go
                    with transaction.atomic():
                        # Walk all the forms in the formset
                        for form in formset:
                            # Check if this form is valid
                            if form.is_valid():
                                # Check if anything has changed so far
                                has_changed = form.has_changed()
                                # Save it preliminarily
                                instance = form.save(commit=False)
                                # Any actions before saving
                                if self.before_save(prefix, request, instance, form):
                                    has_changed = True
                                # Save this construction
                                if has_changed: 
                                    instance.save()
                            else:
                                arErr.append(form.errors)
                else:
                    arErr.append(formset.errors)
                # Add the formset to the context
                context[prefix + "_formset"] = formset
                # Adapt the last save time
                context['savedate']="saved at {}".format(datetime.now().strftime("%X"))

            # Allow user to add to the context
            context = self.add_to_context(context)

            # Make sure we have a list of any errors
            error_list = [str(item) for item in self.arErr]
            context['error_list'] = error_list
            # Standard: add request user to context
            context['requestuser'] = request.user
            # Get the HTML response
            self.data['html'] = render_to_string(self.template_name, context, request)
        else:
            self.data['html'] = "Please log in before continuing"

        # Return the information
        return JsonResponse(self.data)
        
    def get(self, request, object_id=None): 
        # Perform the initializations that need to be made anyway
        self.initializations(request, object_id)
        if self.checkAuthentication(request):
            context = dict(object_id = object_id, savedate=None)
            # Walk all the form objects
            for formObj in self.form_objects:        
                # Used to populate a NEW research project
                # - CREATE a NEW research form, populating it with any initial data in the request
                initial = dict(request.GET.items())
                if self.add:
                    # Create a new form
                    formObj['forminstance'] = formObj['form'](initial=initial, prefix=formObj['prefix'])
                else:
                    # Used to show EXISTING information
                    instance = self.get_instance(formObj['prefix'])
                    # We should show the data belonging to the current Research [obj]
                    formObj['forminstance'] = formObj['form'](instance=instance, prefix=formObj['prefix'])
                # Add instance to the context object
                context[formObj['prefix'] + "Form"] = formObj['forminstance']
            # Walk all the formset objects
            for formsetObj in self.formset_objects:
                formsetClass = formsetObj['formsetClass']
                prefix  = formsetObj['prefix']
                if self.add:
                    # - CREATE a NEW formset, populating it with any initial data in the request
                    initial = dict(request.GET.items())
                    # Saving a NEW item
                    formset = formsetClass(initial=initial, prefix=prefix)
                else:
                    # show the data belonging to the current [obj]
                    instance = self.get_instance(prefix)
                    formset = formsetClass(prefix=prefix, instance=instance)
                # Process all the forms in the formset
                self.process_formset(prefix, request, formset)
                # Store the instance
                formsetObj['formsetinstance'] = formset
                # Add the formset to the context
                context[prefix + "_formset"] = formset
            # Allow user to add to the context
            context = self.add_to_context(context)
            # Make sure we have a list of any errors
            error_list = [str(item) for item in self.arErr]
            context['error_list'] = error_list
            # Standard: add request user to context
            context['requestuser'] = request.user
            
            # Get the HTML response
            self.data['html'] = render_to_string(self.template_name, context, request)
        else:
            self.data['html'] = "Please log in before continuing"

        # Return the information
        return JsonResponse(self.data)
      
    def checkAuthentication(self,request):
        # first check for authentication
        if not request.user.is_authenticated:
            # Simply redirect to the home page
            self.data['html'] = "Please log in to work on a research project"
            return False
        else:
            return True

    def initializations(self, request, object_id):
        # COpy the request
        self.request = request
        # Copy any object id
        self.object_id = object_id
        self.add = object_id is None

        # Find out what the Main Model instance is, if any
        if self.add:
            self.obj = None
        else:
            # Get the instance of the Main Model object
            self.obj =  self.MainModel.objects.get(pk=object_id)
            # Perform some custom initialisations
            self.custom_init()

    def get_instance(self, prefix):
        return self.obj

    def before_save(self, prefix, request, instance=None, form=None):
        return False

    def add_to_context(self, context):
        return context

    def process_formset(self, prefix, request, formset):
        pass

    def custom_init(self):
        pass


class ResearchPart1(ResearchPart):
    template_name = 'seeker/research_part_1.html'
    MainModel = Research
    form_objects = [{'form': GatewayForm, 'prefix': 'gateway'},
                    {'form': SeekerResearchForm, 'prefix': 'research'}]
             
    def get_instance(self, prefix):
        if prefix == 'research':
            return self.obj
        else:
            return self.obj.gateway

    def before_save(self, prefix, request, instance=None, form=None):
        has_changed = False
        if prefix == 'research':
            research = None
            gateway = None
            for formObj in self.form_objects:
                if formObj['prefix'] == 'gateway': gateway = formObj['instance']
                if formObj['prefix'] == 'research': research = formObj['instance']
            if research != None:
                research.gateway = gateway
                has_changed = True
                # Check for the owner
                if research.owner_id == None:
                    research.owner = request.user
        return has_changed

    def custom_init(self):
        if self.obj:
            gw = self.obj.gateway
            if gw:
                gw.check_cvar()
        return True


class ResearchPart2(ResearchPart):
    template_name = 'seeker/research_part_2.html'
    MainModel = Research
    ConstructionFormSet = inlineformset_factory(Gateway, Construction, 
                                                form=ConstructionWrdForm, min_num=1, 
                                                extra=0, can_delete=True, can_order=True)
    formset_objects = [{'formsetClass': ConstructionFormSet, 'prefix': 'construction'}]
             
    def get_instance(self, prefix):
        if prefix == 'construction':
            return self.obj.gateway

    def before_save(self, prefix, request, instance=None, form=None):
        has_changed = False
        if prefix == 'construction':
            # Add the correct search item
            instance.search = SearchMain.create_item("word-group", form.cleaned_data['value'], 'groupmatches')
            has_changed = True
        return has_changed

    def add_to_context(self, context):
        if self.obj == None:
            targettype = None
            currentowner = None
        else:
            targettype = self.obj.targetType
            currentowner = self.obj.owner
        context['targettype'] = targettype
        context['currentowner'] = currentowner
        return context

    def process_formset(self, prefix, request, formset):
        if prefix == 'construction':
            # Get the owner of the research project
            if self.obj == None:
                owner = None
            else:
                owner = self.obj.owner
            currentuser = request.user
            # Need to process all the forms here
            for form in formset:
                # Compare the owner with the current user
                if owner != None and owner != currentuser:
                    form.fields['name'].disabled = True
                    form.fields['value'].disabled = True


class ResearchPart3(ResearchPart):
    template_name = 'seeker/research_part_3.html'
    MainModel = Research
    GvarFormSet = inlineformset_factory(Gateway, GlobalVariable, 
                                        form=GvarForm, min_num=1, 
                                        extra=0, can_delete=True, can_order=True)
    formset_objects = [{'formsetClass': GvarFormSet, 'prefix': 'gvar'}]
                
    def get_instance(self, prefix):
        if prefix == 'gvar':
            return self.obj.gateway

    def add_to_context(self, context):
        if self.obj == None:
            currentowner = None
        else:
            currentowner = self.obj.owner
        context['currentowner'] = currentowner
        return context


class ResearchPart4(ResearchPart):
    template_name = 'seeker/research_part_4.html'
    MainModel = Research
    VardefFormSet = inlineformset_factory(Gateway, VarDef, 
                                          form=VarDefForm, min_num=1, extra=0, 
                                          can_delete=True, can_order=True)
    formset_objects = [{'formsetClass': VardefFormSet, 'prefix': 'vardef'}]
                
    def get_instance(self, prefix):
        if prefix == 'vardef':
            return self.obj.gateway

    def add_to_context(self, context):
        if self.obj == None:
            currentowner = None
            context['research_id'] = None
        else:
            currentowner = self.obj.owner
            context['research_id'] = self.obj.gateway.research.id
        context['currentowner'] = currentowner
        # We also need to make the object_id available
        context['object_id'] = self.object_id
        return context


class ResearchPart42(ResearchPart):
    template_name = 'seeker/research_part_42.html'
    MainModel = VarDef
    CvarFormSet = inlineformset_factory(VarDef, ConstructionVariable, 
                                          form=CvarForm, min_num=1, extra=0)
    formset_objects = [{'formsetClass': CvarFormSet, 'prefix': 'cvar'}]
                
    def get_instance(self, prefix):
        if prefix == 'cvar':
            return self.obj

    def add_to_context(self, context):
        if self.obj == None:
            currentowner = None
            researchid = None
        else:
            currentowner = self.obj.gateway.research.owner
            researchid = self.obj.gateway.research.id
        context['currentowner'] = currentowner
        # We also need to make the object_id available
        context['object_id'] = self.object_id
        context['research_id'] = researchid
        context['vardef_this'] = self.obj
        return context

    def before_save(self, prefix, request, instance=None, form=None):
        has_changed = False
        # When saving a CVAR, we need to check that the functions are okay
        if prefix == 'cvar':
            # Find all functions that are not pointed to from any of the construction variables
            lstCvarFun = [item.function.id for item in ConstructionVariable.objects.exclude(function=None)]
            lstFunDel = Function.objects.exclude(id__in=lstCvarFun)
            # Now delete those that need deleting (cascading is done in the function model itself)
            with transaction.atomic():
                for fun_this in lstFunDel:
                    fun_this.delete()
                    # Make sure that deletions get saved
                    has_changed = True
            # Find the function attached to me
            if instance.function != None:
                # Do the functiondef values match?
                if instance.functiondef != instance.function.functiondef:
                    # Remove the existing function
                    instance.function.delete()
                    # Create a new (obligatory) 'Function' instance, with accompanying Argument instances
                    instance.function = Function.create(instance.functiondef)
                    # Indicate that changes have been made
                    has_changed = True
        # Return the changed flag
        return has_changed

class ResearchPart43(ResearchPart):
    template_name = 'seeker/research_part_43.html'
    MainModel = ConstructionVariable
    form_objects = [{'form': FunctionForm, 'prefix': 'function'}]
    ArgFormSet = inlineformset_factory(Function, Argument, 
                                          form=ArgumentForm, min_num=1, extra=0)
    formset_objects = [{'formsetClass': ArgFormSet, 'prefix': 'arg'}]
                
    def get_instance(self, prefix):
        if prefix == 'function' or prefix == 'arg':
            # This returns the FUNCTION object we are linked to
            cvar = self.obj
            if cvar.function_id == None or cvar.function == None:
                # Check the function definition
                if cvar.functiondef_id == None:
                    # There is an error: we need to have a function definition here
                    return None
                # Make sure both changes are saved in one database-go
                with transaction.atomic():
                    # Create a new function 
                    function = Function(functiondef = cvar.functiondef)
                    # Make sure the function instance gets saved
                    function.save()
                    # Acc a link to this function from the CVAR object
                    cvar.function = function
                    # Make sure we save the CVAR object
                    cvar.save()
            return cvar.function

    def custom_init(self):
        """Make sure the formset gets the correct number of arguments"""

        # Check if we have a CVAR object
        if self.obj:
            # Check if the object type is Calculate
            if self.obj.type == str(choice_value(SEARCH_VARIABLE_TYPE,"Calculate")):
                # Get the function definition
                functiondef = self.obj.functiondef
                if functiondef != None:
                    # Get the number of arguments
                    argnum = functiondef.argnum
                    # Adapt the minimum number of items in the argument formset
                    self.ArgFormSet = inlineformset_factory(Function, Argument, 
                                          form=ArgumentForm, min_num=argnum, extra=0)
                    self.formset_objects[0]['formsetClass'] = self.ArgFormSet

        return True

    def add_to_context(self, context):
        context['function_template'] = ''
        if self.obj == None:
            currentowner = None
            context['research_id'] = None
            context['vardef_this'] = None
            context['construction_this'] = None
        else:
            currentowner = self.obj.variable.gateway.research.owner
            context['research_id'] = self.obj.variable.gateway.research.id
            context['vardef_this'] = self.obj.variable
            context['construction_this'] = self.obj.construction
            # if self.obj.type == str(choice_value(SEARCH_VARIABLE_TYPE,"Calculate")):
            if self.obj.type == "calc":
                # Need to specify the template for the function
                functiondef = self.obj.functiondef
                functionName = functiondef.name
                context['function_template'] = "seeker/function_" + functionName + ".html"

                # Adapt the arguments for this form
                arg_formset = context['arg_formset']
                arg_defs = ArgumentDef.objects.filter(function=functiondef)

                # Calculate the initial queryset for 'gvar'
                qs_gvar = GlobalVariable.objects.filter(gateway=self.obj.construction.gateway)

                # Calculate the initial queryset for 'cvar'
                lstQ = []
                lstQ.append(Q(construction=self.obj.construction))
                lstQ.append(Q(variable_id__lt=self.obj.variable.id))
                qs_cvar = ConstructionVariable.objects.filter(*lstQ)

                for index, arg_form in enumerate(arg_formset):
                    # Initialise the querysets
                    arg_form.fields['gvar'].queryset = qs_gvar
                    arg_form.fields['cvar'].queryset = qs_cvar
                    # Get the instance from this form
                    arg = arg_form.save(commit=False)
                    # Check if the argument definition is set
                    if arg.id == None or arg.argumentdef_id == None:
                        # Get the argument definition for this particular argument
                        arg.argumentdef = arg_defs[index]
                        arg_form.initial['argumentdef'] = arg_defs[index]
                        # Preliminarily save
                        arg_form.save(commit=False)

                # Put the results back again
                context['arg_formset'] = arg_formset

        context['currentowner'] = currentowner
        # We also need to make the object_id available
        context['object_id'] = self.object_id
        return context

    def before_save(self, prefix, request, instance=None, form=None):
        has_changed = False
        # When we save an ARG, we need to add a link to the Function it belongs to
        if prefix == 'arg':
            # Get the 'function' instance
            function = None
            for formObj in self.form_objects:
                if formObj['prefix'] == 'function': 
                    function = formObj['instance']
                    has_changed = True
            # Link to this function
            if function != None:
                instance.function = function
                has_changed = True
        elif prefix == 'function':
            if instance != None:
                if self.obj.function != instance:
                    # Link the function-instance to the  CVAR instance
                    self.obj.function = instance
                    # Save the adapted CVAR instance
                    self.obj.save()
                    # We have already saved the above, so 'has_changed' does not need to be touched
        # Return the change-indicator to trigger saving
        return has_changed




def get_spec_el(request):
    """Entry point for the creation/updating of a Specification Element construction"""

    # Specify the template to be used
    template = 'seeker/specel.html'

    # Get any information from the request
    instanceid = request.GET.get('instanceid', None)

    # Specific processing
    cvar = ConstructionVariable.objects.get(id=instanceid)
  
    # Specify the context
    context= {}
    context['instance'] = cvar
    context['vardef'] = cvar.variable
    context['construction'] = cvar.construction

    # Create HTML
    # sHtml = render_to_string(request, template, context)
    sHtml = render_to_string(template, context)

    # Create data to be returned
    data = {'status': 'ok', 'specelform': sHtml}
    # Return the information
    return JsonResponse(data)




def research_main(request, object_id=None):
    """Main entry point for the specification of a seeker research project"""

    # Check if the user is authenticated
    if not request.user.is_authenticated:
        # Simply redirect to the home page
        return redirect('home')

    # FOR FUTURE WORK (using a different method):
    # Required for any view
    sForm = SeekerForm()
    sForm.add_formset(Gateway, Construction, ConstructionWrdForm)
    sForm.add_formset(Gateway, GlobalVariable, GvarForm)
    sForm.add_formset(Gateway, VarDef, VarDefForm)
    # Note: adding CvarFormset needs a different way...

    # This is required for any view
    BaseConstructionFormSet = inlineformset_factory(Gateway, Construction, form=ConstructionWrdForm, min_num=1, extra=0, can_delete=True, can_order=True)
    GvarFormSet = inlineformset_factory(Gateway, GlobalVariable, form=GvarForm, min_num=1, extra=0, can_delete=True, can_order=True)
    VardefFormSet = inlineformset_factory(Gateway, VarDef, form=VarDefForm, min_num=1, extra=0, can_delete=True, can_order=True)
    CvarFormSet = modelformset_factory(ConstructionVariable, form=CvarForm, min_num=1, extra=0)
    # CvarFormSet = inlineformset_factory(VarDef, ConstructionVariable, form=CvarForm, min_num=1, extra=0)
    # FunctionFormSet = inlineformset_factory(ConstructionVariable, Function, form=FunctionForm, min_num=1, extra=0)
    FunctionFormSet = modelformset_factory(Function, form=FunctionForm, min_num=1, extra=0)

    class ConstructionFormSet(BaseConstructionFormSet):
        #def __init__(self, *args, **kwargs):
        #    self.user = 
        #    super(ConstructionFormSet, self).__init__(*args, **kwargs)

        def _construct_form(self, *args, **kwargs):
            kwargs['user'] = request.user
            return super(ConstructionFormSet, self)._construct_form(*args, **kwargs)

    # Initialisation
    construction_formset = None
    gvar_formset = None
    vardef_formset = None
    cvar_form_list = []
    cvar_formset_list = []
    function_formset = []
    template = 'seeker/research_edit.html'
    delete_url = ''
    arErr = []         # Start out with no errors

    # check for 'save-as-new'
    if request.method == "POST" and '_saveasnew' in request.POST:
        object_id = None

    # Do we need adding?
    add = object_id is None

    # Check if user has permission to add
    if add:
        obj = None
    else:
        # Get the instance of this research object
        obj = Research.objects.get(pk=object_id)
        # Create a delete url for this object
        delete_url = reverse('seeker_delete', args=[object_id])
        # TODO: act if this object does not exist

    # Some initialisations
    ModelForm = SeekerResearchForm
    form_validated = False

    # If POST, we need to SAVE data
    if request.method == 'POST':

        # First check the research form
        form = ModelForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():

            # First create and save a gateway (no form needed)
            if obj != None and obj.gateway != None:
                gateway = obj.gateway
            else:
                gatewayForm = GatewayForm(request.POST)
                if gatewayForm.is_valid():
                    gateway = gatewayForm.save(commit=False)
                    # TODO: possible changes to the gateway in the future...

                    # Save the gateway instance...
                    gateway.save()
            # NOTE: should add an ELSE statement

            # New method: one formset for each combination of cns/var
            vardef_list = gateway.get_vardef_list()
            cns_list = gateway.get_construction_list()
            for cns in cns_list:
                for var in vardef_list:
                    # Determine the prefix for this cns/var formset
                    pfx = "cvar_cns{}_var{}".format(cns.id, var.id)
                    # Get the formset for this cns/var formset
                    fs = CvarFormSet(request.POST, request.FILES, prefix=pfx)
                    # Walk the forms in this formset
                    for cvar_form in fs:
                        # Check if this form is valid
                        if cvar_form.is_valid():
                            # Save the model instance by calling the save method of the formset
                            cvar = cvar_form.save(commit=False)
                            cvar.construction = cns
                            cvar.variable = var
                            cvar.save()
                        else:
                            arErr.append(cvar_form.errors)


            # Also get all required formsets
            construction_formset = ConstructionFormSet(request.POST, request.FILES, prefix='construction', instance=gateway)

            # Are all the formsets valid?
            if construction_formset.is_valid() :

                # Walk the construction formset, in order to add more information per construction
                for cns_form in construction_formset:
                    # Check if this form is valid
                    if cns_form.is_valid():
                        # Save it preliminarily
                        cns = cns_form.save(commit=False)
                        # Add the correct search item
                        cns.search = SearchMain.create_item("word-group", cns_form.cleaned_data['value'], 'groupmatches')
                        # Save this construction
                        cns.save()
                       #  cns_form.save()
                    else:
                        arErr.append(construction_formset.errors)

                # Deal with the formset for global variables
                gvar_formset = GvarFormSet(request.POST, request.FILES, prefix='gvar', instance=gateway)
                if gvar_formset.is_valid():
                    # The global-variable formset can be saved just like that
                    gvar_formset.save()
                else:
                    arErr.append(gvar_formset.errors)

                # Deal with the formset for construction variable definitions
                vardef_formset = VardefFormSet(request.POST, request.FILES, prefix='vardef', instance=gateway)
                if vardef_formset.is_valid():
                    # The contruction-variable formset can be saved just like that
                    vardef_formset.save()
                else:
                    arErr.append(vardef_formset.errors)

                # Process the [ConstructionVariable] instances for
                #    each [Contruction] in the current Gateway that is connected with
                #    each [VarDef]      in the current Gateway
                for cvar_form_row in cvar_form_list:
                    for cvar_form_obj in cvar_form_row:
                        cvar_form = cvar_form_obj['fm']
                        if cvar_form.is_valid():
                            cvar = cvar_form.save()
                        else:
                            arErr.append(cvar_form.errors)
                            break

                ## New method: one formset for each combination of cns/var
                #vardef_list = gateway.get_vardef_list()
                #cns_list = gateway.get_construction_list()
                #for cns in cns_list:
                #    for var in vardef_list:
                #        # Determine the prefix for this cns/var formset
                #        pfx = "cvar_cns{}_var{}".format(cns.id, var.id)
                #        # Get the formset for this cns/var formset
                #        fs = CvarFormSet(request.POST, request.FILES, prefix=pfx)
                #        # Walk the forms in this formset
                #        for cvar_form in fs:
                #            # Check if this form is valid
                #            if cvar_form.is_valid():
                #                # Save the model instance by calling the save method of the formset
                #                cvar = cvar_form.save(commit=False)
                #                cvar.construction = cns
                #                cvar.variable = var
                #                cvar.save()

                # Prepare and save the RESEARCH
                research = form.save(commit=False)
                # Add the correct gateway
                research.gateway = gateway
                # Add the current user as the user
                research.owner = User.objects.get(id=request.user.id)
                research.save()

                # If the form is valid and the user pressed 'save' then show a summary
                if add:
                    # This is a new instance that is being added
                    # TODO: Show a summary
                    # Redirect to the list of projects
                    return redirect('seeker_list')
                else:
                    # This is an existing instance
                    # Redirect to the list of projects
                    return redirect('seeker_list')
            else:
                # Get the formset errors string
                arErr.append(construction_formset.errors)
                # Delete the gateway we created
                gateway.delete()
        else:
            arErr.append(form.errors)

    else:
        # This is a GET request
        if add:
            # We should CREATE a NEW form
            initial = get_changeform_initial_data(ModelForm, request)
            # form = SeekerResearchForm()
            form = ModelForm(initial=initial)
            # Create a completely new formset
            construction_formset = ConstructionFormSet(prefix='construction')
            gvar_formset = GvarFormSet(prefix='gvar')
            vardef_formset = VardefFormSet(prefix='vardef')
            # Sorry, for a totally new form, this is just not possible yet
            # Reason: the gateway is not known
            # Besides: there are no constructions or variables yet for this project
            if False:
                # Create a table of forms for each ConstructionVariable
                vardef_list = gateway.get_vardef_list()
                cns_list = gateway.get_construction_list()
                # Walk the vardef formset
                for vardef_fs in vardef_formset:
                    var = vardef_fs.instance
                    cvar_formset_list = []
                    for cns in cns_list:
                        # Create a variable
                        cvar = ConstructionVariable(construction=cns, variable=var)
                        # Determine the prefix for this cns/var formset
                        pfx = "cvar_cns{}_var{}".format(cns.id, var.id)
                        # Create a formset for this cns/var formset
                        fs = CvarFormSet(prefix=pfx)
                        fs.construction = cns
                        # Add the formset to the list of formsets for this vardef
                        cvar_formset_list.append(fs)
                    # Add the list of formset to this vardef
                    vardef_fs.cvar_formset_list = cvar_formset_list

        elif '/delete/' in request.path:
            # We need to delete
            # TODO: ask for confirmation

            # Perform the deletion of the Research object
            obj.delete()
            # Redirect to the list of projects
            return redirect('seeker_list')
        else:
            # We should show the data belonging to the current Research [obj]
            form = ModelForm(instance=obj)
            # create a formset for this particular instance
            construction_formset = ConstructionFormSet(prefix='construction', instance=obj.gateway)
            gvar_formset = GvarFormSet(prefix='gvar', instance=obj.gateway)
            vardef_formset = VardefFormSet(prefix='vardef', instance=obj.gateway)
            function_formset = FunctionFormSet(prefix='function')
            # Create a table of forms for each ConstructionVariable
            vardef_list = obj.gateway.get_vardef_list()
            cns_list = obj.gateway.get_construction_list()
            # Walk the vardef formset
            for vardef_fs in vardef_formset:
                var = vardef_fs.instance
                cvar_formset_list = []
                for cns in cns_list:
                    # Get or create cvar as instance for cns/var formset
                    cvar_qs = ConstructionVariable.objects.filter(construction=cns).filter(variable=var)
                    if cvar_qs.count() == 0:
                        # Doesn't exist: create a variable
                        cvar = ConstructionVariable(construction=cns, variable=var)
                    else:
                        cvar = cvar_qs[0]
                    # Determine the prefix for this cns/var formset
                    pfx = "cvar_cns{}_var{}".format(cns.id, var.id)
                    # Create a formset for this cns/var formset
                    fs = CvarFormSet(prefix=pfx, queryset=cvar_qs)
                    fs.construction = cns
                    ## Create and add a Cvar-Function formset
                    #fs.fun_formset = FunctionFormSet(instance=cvar)
                    ## Add a Function form
                    #fs.funform = FunctionForm(instance=cvar)
                    # Add the formset to the list of formsets for this vardef
                    cvar_formset_list.append(fs)
                # Add the list of formset to this vardef
                vardef_fs.cvar_formset_list = cvar_formset_list


    # COnvert all lists of errors to a string
    # sErr = '\n'.join([str(item) for item in arErr]).strip()
    # error_list = [item for item in arErr]
    error_list = [str(item) for item in arErr]


    # Start setting the context
    context = dict(
        object_id = object_id,
        original=obj,
        form = form,
        construction_formset = construction_formset,
        gvar_formset = gvar_formset,
        vardef_formset = vardef_formset,
        function_formset = function_formset,
        show_save = True,
        show_save_and_continue = True,
        show_save_and_add_another = True,
        show_delete_link = not add,
        delete_url=delete_url,
        error_list=error_list, #sErr,
        )

    # Hide the "Save" and "Save and continue" buttons if "Save as New" was
    # previously chosen to prevent the interface from getting confusing.
    if request.method == 'POST' and not form_validated and "_saveasnew" in request.POST:
        context['show_save'] = False
        context['show_save_and_continue'] = False
        # Use the change template instead of the add template.
        add = False

    # Open the template that allows Creating a new research project
    #   or editing the existing project
    return render(request, template, context)
