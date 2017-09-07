"""
Definition of views for the SEEKER app.
"""

from django.db.models import Q
from django.forms import formset_factory
from django.forms import inlineformset_factory, BaseInlineFormSet, modelformset_factory
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.core.exceptions import FieldDoesNotExist
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.base import RedirectView
from django.views.generic import ListView, View

from cesar.seeker.forms import *
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


class FunctionListView(ListView):
    """List all the functions that are available"""

    model = FunctionDef
    template_name = 'seeker/function_list.html'
    paginate_by = paginateEntries
    entrycount = 0
    qs = None

    def render_to_response(self, context, **response_kwargs):

        currentuser = self.request.user

        context['object_list'] = FunctionDef.objects.all().order_by('name')
        context['authenticated'] = currentuser.is_authenticated()
        # Make sure the correct URL is being displayed
        return super(FunctionListView, self).render_to_response(context, **response_kwargs)



class SeekerListView(ListView):
    """List all the research projects available"""

    model = Research
    template_name = 'seeker/research_list.html'
    paginate_by = paginateEntries
    entrycount = 0
    qs = None

    def render_to_response(self, context, **response_kwargs):
        sType = self.request.GET.get('listtype', '')
        if 'copyerror' not in context:
            if 'copyerror' in response_kwargs:
                context['copyerror'] = response_kwargs['copyerror']
            else:
                context['copyerror'] = None
        if sType == 'copy':
            # Can we change the path?
            self.request.path = reverse('seeker_list')
            # Need to make a copy
            if 'object_id' in self.kwargs:
                object_id = self.kwargs['object_id']
                sMsg = research_copy(object_id)
            else:
                sMsg = "The [object_id] is not passed along in the HTML call"
            # If needed, adapt the context
            if sMsg != None and sMsg != '':
                context['copyerror'] = sMsg
            ## Redirect appropriately
            #return HttpResponseRedirect(reverse('seeker_list', kwargs={'copyerror': sMsg}))
        elif sType == 'del':
            # We can delete this one
            if 'object_id' in self.kwargs:
                object_id = self.kwargs['object_id']
                # Try to delete it
                sMsg = research_del(object_id)
            else:
                sMsg = "The [object_id] is not passed along in the HTML call"

        currentuser = self.request.user
        # Is this user logged in?
        if currentuser.is_authenticated():
            # Get the correct list of research projects:
            # - All my own projects
            # - All projects shared with the groups I belong to
            my_projects = Research.objects.filter(Q(owner=currentuser))
            lstQ = []
            lstQ.append(~Q(owner=currentuser))
            lstQ.append(~Q(sharegroups__group__in=currentuser.groups.all()))
            # research_list = Research.objects.filter(Q(owner=self.request.user) | Q(sharegroups_group))
            research_list = Research.objects.exclude(*lstQ)
            combi_list = []
            for item in research_list:
                may_read = item.has_permission(currentuser, 'r')
                may_write = item.has_permission(currentuser, 'w')
                may_delete = item.has_permission(currentuser, 'd')
                combi_list.append({"project": item, 
                                   "may_read":may_read,
                                   "may_write": may_write,
                                   "may_delete": may_delete})
            authenticated = True
        else:
            combi_list = []
            research_list = []
            authenticated = False
        context['combi_list'] = combi_list
        context['object_list'] = research_list
        context['authenticated'] = authenticated
        # Make sure the correct URL is being displayed
        return super(SeekerListView, self).render_to_response(context, **response_kwargs)


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
            # Walk all the forms for preparation of the formObj contents
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

            # Initially we are assuming this just is a review
            context['savedate']="reviewed at {}".format(datetime.now().strftime("%X"))

            # Iterate again
            for formObj in self.form_objects:
                prefix = formObj['prefix']
                # Adapt if it is not readonly
                if not formObj['readonly']:
                    # Check validity of form
                    if formObj['forminstance'].is_valid():
                        # Save it preliminarily
                        instance = formObj['forminstance'].save(commit=False)
                        # The instance must be made available (even though it is only 'preliminary')
                        formObj['instance'] = instance
                        # Perform actions to this form BEFORE FINAL saving
                        bNeedSaving = formObj['forminstance'].has_changed()
                        if self.before_save(prefix, request, instance=instance): bNeedSaving = True
                        if formObj['forminstance'].instance.id == None: bNeedSaving = True
                        if bNeedSaving:
                            # Perform the saving
                            instance.save()
                            # Set the context
                            context['savedate']="saved at {}".format(datetime.now().strftime("%X"))
                            # Put the instance in the form object
                            formObj['instance'] = instance
                            # Any action after saving this form
                            self.after_save(prefix, instance)
                    else:
                        self.arErr.append(formObj['forminstance'].errors)
                        self.form_validated = False

                # Add instance to the context object
                context[prefix + "Form"] = formObj['forminstance']
            # Walk all the formset objects
            for formsetObj in self.formset_objects:
                formsetClass = formsetObj['formsetClass']
                prefix  = formsetObj['prefix']
                form_kwargs = self.get_form_kwargs(prefix)
                if self.add:
                    # Saving a NEW item
                    formset = formsetClass(request.POST, request.FILES, prefix=prefix, form_kwargs = form_kwargs)
                else:
                    # Saving an EXISTING item
                    instance = self.get_instance(prefix)
                    formset = formsetClass(request.POST, request.FILES, prefix=prefix, instance=instance, form_kwargs = form_kwargs)
                # Process all the forms in the formset
                self.process_formset(prefix, request, formset)
                # Store the instance
                formsetObj['formsetinstance'] = formset
                # Adapt the formset contents only, when it is NOT READONLY
                if not formsetObj['readonly']:
                    # Is the formset valid?
                    if formset.is_valid():
                        # Make sure all changes are saved in one database-go
                        with transaction.atomic():
                            # Walk all the forms in the formset
                            for form in formset:
                                # At least check for validity
                                if form.is_valid():
                                    # Should we delete?
                                    if form.cleaned_data['DELETE']:
                                        # Delete this one
                                        form.instance.delete()
                                        # NOTE: the template knows this one is deleted by looking at form.DELETE
                                        # form.delete()
                                    else:
                                        # Check if anything has changed so far
                                        has_changed = form.has_changed()
                                        # Save it preliminarily
                                        instance = form.save(commit=False)
                                        # Any actions before saving
                                        if self.before_save(prefix, request, instance, form):
                                            has_changed = True
                                        # Save this construction
                                        if has_changed: 
                                            # Save the instance
                                            instance.save()
                                            # Adapt the last save time
                                            context['savedate']="saved at {}".format(datetime.now().strftime("%X"))
                                else:
                                    self.arErr.append(form.errors)
                    else:
                        self.arErr.append(formset.errors)
                # Add the formset to the context
                context[prefix + "_formset"] = formset

            # Allow user to add to the context
            context = self.add_to_context(context)

            # Make sure we have a list of any errors
            error_list = [str(item) for item in self.arErr]
            context['error_list'] = error_list
            context['errors'] = self.arErr
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
                form_kwargs = self.get_form_kwargs(prefix)
                if self.add:
                    # - CREATE a NEW formset, populating it with any initial data in the request
                    initial = dict(request.GET.items())
                    # Saving a NEW item
                    formset = formsetClass(initial=initial, prefix=prefix, form_kwargs=form_kwargs)
                else:
                    # show the data belonging to the current [obj]
                    instance = self.get_instance(prefix)
                    formset = formsetClass(prefix=prefix, instance=instance, form_kwargs=form_kwargs)
                # Process all the forms in the formset
                ordered_forms = self.process_formset(prefix, request, formset)
                if ordered_forms:
                    context[prefix + "_ordered"] = ordered_forms
                # Store the instance
                formsetObj['formsetinstance'] = formset
                # Add the formset to the context
                context[prefix + "_formset"] = formset
            # Allow user to add to the context
            context = self.add_to_context(context)
            # Make sure we have a list of any errors
            error_list = [str(item) for item in self.arErr]
            context['error_list'] = error_list
            context['errors'] = self.arErr
            # Standard: add request user to context
            context['requestuser'] = request.user
            
            # Get the HTML response
            self.data['html'] = render_to_string(self.template_name, context, request)
            # x = context['arg_formset'][0].instance.functionparent.all()[0].parent_id
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
        # Clear errors
        self.arErr = []
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

    def get_form_kwargs(self, prefix):
        return None

    def before_save(self, prefix, request, instance=None, form=None):
        return False

    def after_save(self, prefix, instance=None):
        return True

    def add_to_context(self, context):
        return context

    def process_formset(self, prefix, request, formset):
        return None

    def custom_init(self):
        pass


class ResearchPart1(ResearchPart):
    template_name = 'seeker/research_part_1.html'
    MainModel = Research
    form_objects = [{'form': GatewayForm, 'prefix': 'gateway', 'readonly': False},
                    {'form': SeekerResearchForm, 'prefix': 'research', 'readonly': False}]
    SharegFormSet = inlineformset_factory(Research, ShareGroup, 
                                        form=SharegForm, min_num=0, 
                                        extra=0, can_delete=True, can_order=False)
    formset_objects = [{'formsetClass': SharegFormSet, 'prefix': 'shareg', 'readonly': False}]
             
    def get_instance(self, prefix):
        if prefix == 'research':
            # Return the Research instance
            return self.obj
        elif prefix == 'shareg':
            # A sharegroup is mainly interested in the Research
            return self.obj
        else:
            # The other option is 'gateway': return the gateway instance
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
        # Set the 'saved' one
        self.obj.save()
        return has_changed

    def after_save(self, prefix, instance=None):
        if prefix == 'research' and self.obj == None:
            # Capture the object
            self.obj = instance
            # Adapt the instanceid and the ajaxurl
            object_id = "{}".format(instance.id)
            self.data['instanceid'] = object_id

    def add_to_context(self, context):
        if context['object_id'] == None:
            if self.obj != None:
                context['object_id'] = "{}".format(self.obj.id)
        if self.obj == None:
            currentowner = None
        else:
            currentowner = self.obj.owner
        context['currentowner'] = currentowner
        return context

    def custom_init(self):
        if self.obj:
            gw = self.obj.gateway
            if gw:
                # Check and repair CVAR instances
                gw.check_cvar()
                # Make sure DVAR instances are ordered
                gw.order_dvar()
                # Make sure GVAR instances are ordered
                gw.order_gvar()
        return True

    def process_formset(self, prefix, request, formset):
        if prefix == 'shareg':
            currentuser = request.user
            # Need to process all the forms here
            for form in formset:
                x = form.fields['permission'].help_text
        return None


class ResearchPart2(ResearchPart):
    template_name = 'seeker/research_part_2.html'
    MainModel = Research
    ConstructionFormSet = inlineformset_factory(Gateway, Construction, 
                                                form=ConstructionWrdForm, min_num=1, 
                                                extra=0, can_delete=True, can_order=True)
    formset_objects = [{'formsetClass': ConstructionFormSet, 'prefix': 'construction', 'readonly': False}]
             
    def get_instance(self, prefix):
        if prefix == 'construction':
            return self.obj.gateway

    def before_save(self, prefix, request, instance=None, form=None):
        has_changed = False
        if prefix == 'construction':
            # Add the correct search item
            instance.search = SearchMain.create_item("word-group", form.cleaned_data['value'], 'groupmatches')
            has_changed = True
        # Set the 'saved' one
        self.obj.save()
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
        return None


class ResearchPart3(ResearchPart):
    template_name = 'seeker/research_part_3.html'
    MainModel = Research
    GvarFormSet = inlineformset_factory(Gateway, GlobalVariable, 
                                        form=GvarForm, min_num=1, 
                                        extra=0, can_delete=True, can_order=True)
    formset_objects = [{'formsetClass': GvarFormSet, 'prefix': 'gvar', 'readonly': False}]
                
    def get_instance(self, prefix):
        if prefix == 'gvar':
            return self.obj.gateway

    def before_save(self, prefix, request, instance=None, form=None):
        # Set the 'saved' one
        self.obj.save()
        return False

    def add_to_context(self, context):
        if self.obj == None:
            currentowner = None
            targettype = ""
        else:
            currentowner = self.obj.owner
            targettype = self.obj.targetType
        context['currentowner'] = currentowner
        context['targettype'] = targettype
        return context


class ResearchPart4(ResearchPart):
    template_name = 'seeker/research_part_4.html'
    MainModel = Research
    VardefFormSet = inlineformset_factory(Gateway, VarDef, 
                                          form=VarDefForm, min_num=1, extra=0, 
                                          can_delete=True, can_order=True)
    formset_objects = [{'formsetClass': VardefFormSet, 'prefix': 'vardef', 'readonly': False}]
                
    def get_instance(self, prefix):
        if prefix == 'vardef':
            return self.obj.gateway

    def add_to_context(self, context):
        if self.obj == None:
            currentowner = None
            context['research_id'] = None
            targettype = ""
        else:
            currentowner = self.obj.owner
            context['research_id'] = self.obj.gateway.research.id
            targettype = self.obj.targetType
        context['currentowner'] = currentowner
        context['targettype'] = targettype
        # We also need to make the object_id available
        context['object_id'] = self.object_id
        return context

    def process_formset(self, prefix, request, formset):
        if prefix == 'vardef':
            # Sorting: see https://wiki.python.org/moin/HowTo/Sorting
            ordered_forms = sorted(formset.forms, key=lambda item: item.instance.order)
            # Make sure the initial values of the 'order' in the forms are set correctly
            for form in ordered_forms:
                form.fields['ORDER'].initial = form.instance.order
            return ordered_forms
        else:
            return None

    def before_save(self, prefix, request, instance=None, form=None):
        has_changed = False
        if prefix == 'vardef':
            # Retrieve the 'order' field
            if instance.order != form.cleaned_data['ORDER']:
                instance.order = form.cleaned_data['ORDER']
                has_changed = True
        # Set the 'saved' one
        self.obj.save()
        return has_changed
    

class ResearchPart42(ResearchPart):
    template_name = 'seeker/research_part_42.html'
    MainModel = VarDef
    CvarFormSet = inlineformset_factory(VarDef, ConstructionVariable, 
                                          form=CvarForm, min_num=1, extra=0)
    formset_objects = [{'formsetClass': CvarFormSet, 'prefix': 'cvar', 'readonly': False}]
                
    def get_instance(self, prefix):
        if prefix == 'cvar':
            return self.obj

    def add_to_context(self, context):
        if self.obj == None:
            currentowner = None
            researchid = None
            targettype = ""
        else:
            currentowner = self.obj.gateway.research.owner
            researchid = self.obj.gateway.research.id
            targettype = self.obj.gateway.research.targetType
        context['currentowner'] = currentowner
        # We also need to make the object_id available
        context['object_id'] = self.object_id
        context['research_id'] = researchid
        context['vardef_this'] = self.obj
        context['targettype'] = targettype
        return context

    def before_save(self, prefix, request, instance=None, form=None):
        # NOTE: the 'instance' here is the CVAR instance

        has_changed = False
        # When saving a CVAR, we need to check that the functions are okay
        if prefix == 'cvar':
            # Find all functions that are not pointed to from any of the construction variables
            lstCvarId = [item.id for item in ConstructionVariable.objects.exclude(function=None)]
            lstFunDel = Function.objects.exclude(root__in=lstCvarId)
            # Now delete those that need deleting (cascading is done in the function model itself)
            with transaction.atomic():
                for fun_this in lstFunDel:
                    fun_this.delete()
                    # Make sure that deletions get saved
                    has_changed = True
            # Find the function attached to me - only if applicable!!
            if instance.type == "calc" and instance.functiondef != None:
                # Two situations:
                # - THere is no function yet
                # - There is a function, but with the wrong functiondef
                if instance.function == None or (instance.function != None and instance.functiondef != instance.function.functiondef):
                    # Does a previous function exist?
                    if instance.function:
                        # Remove the existing function
                        instance.function.delete()
                    # Create a new (obligatory) 'Function' instance, with accompanying Argument instances
                    instance.function = Function.create(instance.functiondef, instance, None, None)
                    # Indicate that changes have been made
                    has_changed = True
        # Set the 'saved' one
        self.obj.gateway.research.save()
        # Return the changed flag
        return has_changed


class ResearchPart43(ResearchPart):
    """Starting from a CVAR of type 'function', allow defining that function"""

    MainModel = ConstructionVariable
    template_name = 'seeker/research_part_43.html'
    form_objects = [{'form': FunctionForm, 'prefix': 'function', 'readonly': False}]
    ArgFormSet = inlineformset_factory(Function, Argument, 
                                          form=ArgumentForm, min_num=1, extra=0)
    CvarFunctionFormSet = inlineformset_factory(ConstructionVariable, Function, 
                                          form=FunctionForm, min_num=1, extra=0)
    formset_objects = [{'formsetClass': ArgFormSet, 'prefix': 'arg', 'readonly': False},
                       {'formsetClass': CvarFunctionFormSet, 'prefix': 'cvarfunction', 'readonly': False}]
                
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
                    # function = Function(functiondef = cvar.functiondef, root = cvar)
                    function = Function.create(cvar.functiondef, cvar, None, None)
                    # Make sure the function instance gets saved
                    # function.save()
                    # Acc a link to this function from the CVAR object
                    cvar.function = function
                    # Make sure we save the CVAR object
                    cvar.save()
            return cvar.function
        elif prefix == "cvarfunction":
            # The 'instance' of CvarFunction is the Cvar
            return self.obj

    def custom_init(self):
        """Make sure the arg-formset gets the correct number of arguments"""

        # Check if we have a CVAR object
        if self.obj:
            # Check if the object type is Calculate
            if self.obj.type == "calc":
                # Get the function definition
                functiondef = self.obj.functiondef
                if functiondef != None:
                    # Get the number of arguments
                    argnum = functiondef.argnum
                    # Adapt the minimum number of items in the argument formset
                    self.ArgFormSet = inlineformset_factory(Function, Argument, 
                                          form=ArgumentForm, min_num=argnum, extra=0)
                    self.formset_objects[0]['formsetClass'] = self.ArgFormSet
                # Prepare the CvarFunction formset by getting the exact number of functions
                function_list = self.obj.get_functions()
                funcnum = len(function_list)
                self.CvarFunctionFormSet = inlineformset_factory(ConstructionVariable, Function, 
                                          form=FunctionForm, min_num=funcnum, extra=0)
                self.formset_objects[1]['formsetClass'] = self.CvarFunctionFormSet

        return True

    def add_to_context(self, context):
        if self.obj == None:
            currentowner = None
            context['research_id'] = None
            context['vardef_this'] = None
            context['construction_this'] = None
            targettype = ""
        else:
            currentowner = self.obj.variable.gateway.research.owner
            context['research_id'] = self.obj.variable.gateway.research.id
            context['vardef_this'] = self.obj.variable
            context['construction_this'] = self.obj.construction
            targettype = self.obj.variable.gateway.research.targetType
            # Further action if this is a calculation
            if self.obj.type == "calc":
                # Need to specify the template for the function
                functiondef = self.obj.functiondef
                if functiondef == None:
                    # Provide a break point for debugging
                    iStop = 1

                # Adapt the arguments for this form
                arg_formset = context['arg_formset']
                arg_defs = ArgumentDef.objects.filter(function=functiondef)

                # Calculate the initial queryset for 'gvar'
                qs_gvar = GlobalVariable.objects.filter(gateway=self.obj.construction.gateway)

                # Calculate the initial queryset for 'cvar'
                # NOTE: we take into account the 'order' field, which must have been defined properly...
                lstQ = []
                lstQ.append(Q(construction=self.obj.construction))
                lstQ.append(Q(variable__order__lt=self.obj.variable.order))
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
                        arg_form.initial['argtype'] = arg_defs[index].argtype
                        # Preliminarily save
                        arg_form.save(commit=False)

                # Put the results back again
                context['arg_formset'] = arg_formset

        context['currentowner'] = currentowner
        # We also need to make the object_id available
        context['object_id'] = self.object_id
        context['targettype'] = targettype
        return context

    def before_save(self, prefix, request, instance=None, form=None):
        # NOTE: the 'instance' is the CVAR instance

        has_changed = False
        # When we save an ARG, we need to add a link to the Function it belongs to
        if prefix == 'arg':
            # Get the 'function' instance
            function = None
            for formObj in self.form_objects:
                if formObj['prefix'] == 'function':
                    # Get the function object 
                    function = formObj['instance']
            # Link to this function
            if function != None and instance.function != function:
                instance.function = function
                has_changed = True
            # Check the argtype of this argument: is it NOT a function any more?
            if instance.argtype != "func":
                # Then REmove all functions pointing to me
                func_child = instance.functionparent.first()
                if func_child != None:
                    func_child.delete()
                    has_changed = True
            else:
                # THis is a function: check if the function definition has not changed
                func_child = instance.functionparent.first()
                if func_child == None or instance.functiondef != func_child.functiondef:
                    # The function definition changed >> replace the child with a completely NEW version
                    # [1] remove the child
                    if func_child != None:
                        func_child.delete()
                    # [2] Create a new version
                    func_child = Function.create(instance.functiondef, instance.function.root, None, instance)
                    # [3] Save it
                    func_child.save()
                    # Indicate changes
                    has_changed = True
        elif prefix == 'function':
            if instance != None:
                if self.obj.function != instance:
                    # Link the function-instance to the  CVAR instance
                    self.obj.function = instance
                    # Save the adapted CVAR instance
                    self.obj.save()
                    # We have already saved the above, so 'has_changed' does not need to be touched
        # Save the research object
        self.obj.variable.gateway.research.save()
        # Return the change-indicator to trigger saving
        return has_changed


class ResearchPart44(ResearchPart):
    """Starting from an Argument of type 'function', allow defining that function"""

    MainModel = Argument
    template_name = 'seeker/research_part_44.html'
    ArgFormSet = inlineformset_factory(Function, Argument, 
                                          form=ArgumentForm, min_num=1, extra=0)
    # Two forms:
    # - the 'parent' form is view-only and contains the argument we are supplying a function for
    # - the 'function' form is editable and contains the function for the argument 
    form_objects = [{'form': FunctionForm, 'prefix': 'parent', 'readonly': True},
                    {'form': FunctionForm, 'prefix': 'function', 'readonly': False}]
    # Two formsets:
    # - the 'arg'  formset belongs to the 'function' (see above)
    # - the 'parg' formset belongs to the 'parent'
    formset_objects = [{'formsetClass': ArgFormSet, 'prefix': 'arg', 'readonly': False},
                       {'formsetClass': ArgFormSet, 'prefix': 'parg', 'readonly': True}]
                
    def get_instance(self, prefix):
        # NOTE: For '44' the self.obj is an Argument!!

        if prefix == 'function' or prefix == 'arg':
            # This returns the EXISTING or NEW function object belonging to the argument
            qs = Function.objects.filter(parent=self.obj)
            # Does it exist?
            if qs.count() == 0:
                # It does not yet exist: create it
                # Make sure both changes are saved in one database-go
                with transaction.atomic():
                    # Create a new function 
                    function = Function(functiondef = self.obj.functiondef, 
                                        root = self.obj.function.root,
                                        parent = self.obj)
                    # Make sure the function instance gets saved
                    function.save()
            else:
                # It exists, so assign it
                function = qs[0]
            return function
        elif prefix == 'parent' or prefix == 'parg':
            # This returns the PARENT function object the argument belongs to
            return self.obj.function

    def custom_init(self):
        """Make sure the ARG formset gets the correct number of arguments"""

        # Check if we have a FUNCTION object
        fun_this = self.get_instance('function')
        if fun_this:
            # Get the function definition
            functiondef = fun_this.functiondef
            if functiondef != None:
                # Get the number of arguments
                argnum = functiondef.argnum
                # Adapt the minimum number of items in the argument formset
                self.ArgFormSet = inlineformset_factory(Function, Argument, 
                                        form=ArgumentForm, min_num=argnum, extra=0)
                # The 'arg' object is the one with index '0'
                self.formset_objects[0]['formsetClass'] = self.ArgFormSet

        return True

    def add_to_context(self, context):
        # NOTE: the instance (self.obj) for the '44' form is an ARGUMENT
        pfun_this = self.get_instance('parent')
        if pfun_this == None:
            currentowner = None
            context['research_id'] = None
            context['vardef_this'] = None
            context['construction_this'] = None
            context['cvar_this'] = None
            targettype = ""
        else:
            # Get to the CVAR instance
            cvar = pfun_this.root
            gateway = cvar.construction.gateway
            currentowner = gateway.research.owner
            context['research_id'] = gateway.research.id
            context['vardef_this'] = cvar.variable
            context['construction_this'] = cvar.construction
            context['cvar_this'] = cvar
            targettype = gateway.research.targetType

            # Since this is a '44' form, we know this is a calculation

            # Calculate the initial queryset for 'gvar'
            #   (These are the variables available for this GATEWAY)
            qs_gvar = GlobalVariable.objects.filter(gateway=gateway)

            # Calculate the initial queryset for 'cvar'
            lstQ = []
            lstQ.append(Q(construction=cvar.construction))
            lstQ.append(Q(variable__order__lt=cvar.variable.order))
            qs_cvar = ConstructionVariable.objects.filter(*lstQ)

            # Calculate the initial queryset for 'dvar'
            lstQ = []
            lstQ.append(Q(gateway=gateway))
            lstQ.append(Q(order__lt=cvar.variable.order))
            qs_dvar = VarDef.objects.filter(*lstQ).order_by('order')

            # - adapting the 'parg_formset' for the 'parent' form (view-only)
            context['parg_formset'] = self.check_arguments(context['parg_formset'], pfun_this.functiondef, qs_gvar, qs_cvar, qs_dvar)

            # - adapting the 'arg_formset' for the 'function' form (editable)
            fun_this = self.get_instance('function')
            if fun_this != None:
                context['arg_formset'] = self.check_arguments(context['arg_formset'], fun_this.functiondef, qs_gvar, qs_cvar, qs_dvar)

            # Get a list of all ancestors
            context['anc_list'] = fun_this.get_ancestors()

        context['currentowner'] = currentowner
        # We also need to make the object_id available
        context['object_id'] = self.object_id
        context['targettype'] = targettype
        return context

    def check_arguments(self, arg_formset, functiondef, qs_gvar, qs_cvar, qs_dvar):
        # Take the functiondef as available in this argument
        arg_defs = functiondef.arguments.all()

        for index, arg_form in enumerate(arg_formset):
            # Initialise the querysets
            arg_form.fields['gvar'].queryset = qs_gvar
            arg_form.fields['cvar'].queryset = qs_cvar
            arg_form.fields['dvar'].queryset = qs_dvar
            # Get the instance from this form
            arg = arg_form.save(commit=False)
            # Check if the argument definition is set
            if arg.id == None or arg.argumentdef_id == None:
                # Get the argument definition for this particular argument
                arg.argumentdef = arg_defs[index]
                arg_form.initial['argumentdef'] = arg_defs[index]
                arg_form.initial['argtype'] = arg_defs[index].argtype
                # Preliminarily save
                arg_form.save(commit=False)

        # Return the adatpted formset
        return arg_formset

    def before_save(self, prefix, request, instance=None, form=None):
        has_changed = False
        # When we save an ARG, we need to add a link to the Function it belongs to
        if prefix == 'arg':
            # The instance is the argument instance

            # Check the argtype of this argument: is it NOT a function any more?
            if instance.argtype != "func":
                # Then REmove all functions pointing to me
                func_child = instance.functionparent.first()
                if func_child != None:
                    func_child.delete()
                    has_changed = True
            else:
                # THis is a function: check if the function definition has not changed
                func_child = instance.functionparent.first()
                if func_child == None or instance.functiondef != func_child.functiondef:
                    # The function definition changed >> replace the child with a completely NEW version
                    # [1] remove the child
                    if func_child != None:
                        func_child.delete()
                    # [2] Create a new version
                    func_child = Function.create(instance.functiondef, instance.function.root, None, instance)
                    # [3] Save it here (or that is done one level up)
                    func_child.save()
                    # Indicate changes have been made
                    has_changed = True
        # Save the related RESEARCH object
        self.obj.function.root.construction.gateway.research.save()
        # Return the change-indicator to trigger saving
        return has_changed


class ResearchPart6(ResearchPart):
    template_name = 'seeker/research_part_6.html'
    MainModel = Research
    CondFormSet = inlineformset_factory(Gateway, Condition, 
                                        form=ConditionForm, min_num=1, 
                                        extra=0, can_delete=True, can_order=True)
    formset_objects = [{'formsetClass': CondFormSet, 'prefix': 'cond', 'readonly': False}]

    def get_instance(self, prefix):
        if prefix == 'cond':
            # We need to have the gateway
            return self.obj.gateway

    def get_form_kwargs(self, prefix):
        if prefix == 'cond':
            return {"gateway":  self.obj.gateway}
        else:
            return None


    def add_to_context(self, context):
        # Note: the self.obj is the Research project
        if self.obj == None:
            currentowner = None
            targettype = ""
        else:
            # gateway = self.obj.gateway
            currentowner = self.obj.owner
            targettype = self.obj.targetType

            #try:
            #    # Calculate the initial queryset for 'dvar'
            #    # NOTE: we take into account the 'order' field, which must have been defined properly...
            #    lstQ = []
            #    lstQ.append(Q(gateway=gateway))
            #    qs_dvar = gateway.definitionvariables.filter(*lstQ).order_by('order')

            #    # Determine the possible functiondefs
            #    qs_fdef = FunctionDef.objects.all().order_by('name')

            #    # Walk all the forms in the formset
            #    cond_formset = context['cond_formset']
            #    for cond_form in cond_formset:
            #        # Initialise the querysets
            #        cond_form.fields['variable'].queryset = qs_dvar
            #        cond_form.fields['functiondef'].queryset = qs_fdef
            #    # Also set the values for the empty-form
            #    # eform = cond_formset.empty_form
            #    cond_formset.empty_form.fields['variable'].queryset = qs_dvar
            #    cond_formset.empty_form.fields['functiondef'].queryset = qs_fdef
            #    # Replace the empty form
            #    # cond_formset.empty_form = eform
            #    # Put the formset back again
            #    context['cond_formset'] = cond_formset
            #except:
            #    lInfo = sys.exc_info()
            #    if len(lInfo) == 1:
            #        sMsg = lInfo[0]
            #    else:
            #        sMsg = "{}<br>{}".format(lInfo[0], lInfo[1])

            context['currentowner'] = currentowner
            context['targettype'] = targettype
        # Return the context
        return context
    

class ResearchPart62(ResearchPart):
    MainModel = Condition
    template_name = 'seeker/research_part_62.html'
    # Provide a form that allows filling in the specifics of a function
    form_objects = [{'form': FunctionForm, 'prefix': 'function', 'readonly': False}]
    # The function that is provided contains a particular number of arguments
    ArgFormSet = inlineformset_factory(Function, Argument, 
                                          form=ArgumentForm, min_num=1, extra=0)
    formset_objects = [{'formsetClass': ArgFormSet,  'prefix': 'arg',  'readonly': False}]

    def get_instance(self, prefix):
        if prefix == 'function' or prefix == 'arg':
            # This returns the FUNCTION object we are linked to
            condition = self.obj
            if condition.function_id == None or condition.function == None:
                # Check the function definition
                if condition.functiondef_id == None:
                    # There is an error: we need to have a function definition here
                    return None
                # Make sure both changes are saved in one database-go
                with transaction.atomic():
                    # Create a new function 
                    function = Function.create(condition.functiondef, None, condition, None)
                    # Add a link to this function from the condition object
                    condition.function = function
                    # Make sure we save the condition object
                    condition.save()
            return condition.function

    def custom_init(self):
        """Make sure the ARGUMENT formset gets the correct number of arguments"""

        # Check if we have a Condition object
        if self.obj:
            # Check if the condition-object type is 'func' - functiewaarde
            if self.obj.condtype == "func":
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
        # Note: the self.obj is a Condition
        condition = self.obj

        if condition == None:
            currentowner = None
            context['research_id'] = None
            context['condition_this'] = None
            targettype = ""
        else:
            context['condition_this'] = condition
            gateway = condition.gateway
            currentowner = gateway.research.owner
            context['research_id'] = gateway.research.id
            targettype = gateway.research.targetType

            # Further action if this condition is of the 'func' type
            if condition.condtype == "func":

                # Need to specify the template for the function
                functiondef = condition.functiondef
                # Adapt the arguments for this form
                arg_formset = context['arg_formset']
                arg_defs = ArgumentDef.objects.filter(function=functiondef)

                # Calculate the initial queryset for 'gvar'
                qs_gvar = GlobalVariable.objects.filter(gateway=gateway)


                # Calculate the initial queryset for 'dvar'
                lstQ = []
                lstQ.append(Q(gateway=gateway))
                qs_dvar = VarDef.objects.filter(*lstQ).order_by('order')

                for index, arg_form in enumerate(arg_formset):
                    # Initialise the querysets
                    arg_form.fields['gvar'].queryset = qs_gvar
                    arg_form.fields['dvar'].queryset = qs_dvar
                    # Get the instance from this form
                    arg = arg_form.save(commit=False)
                    # Check if the argument definition is set
                    if arg.id == None or arg.argumentdef_id == None:
                        # Get the argument definition for this particular argument
                        arg.argumentdef = arg_defs[index]
                        arg_form.initial['argumentdef'] = arg_defs[index]
                        arg_form.initial['argtype'] = arg_defs[index].argtype
                        # Preliminarily save
                        arg_form.save(commit=False)

                # Put the results back again
                context['arg_formset'] = arg_formset

        context['currentowner'] = currentowner
        # We also need to make the object_id available
        context['object_id'] = self.object_id
        context['targettype'] = targettype
        return context


class ResearchPart63(ResearchPart):
    MainModel = Argument
    template_name = 'seeker/research_part_63.html'
    ArgFormSet = inlineformset_factory(Function, Argument, 
                                          form=ArgumentForm, min_num=1, extra=0)
    # Two forms:
    # - the 'parent' form is view-only and contains the argument we are supplying a function for
    # - the 'function' form is editable and contains the function for the argument 
    form_objects = [{'form': FunctionForm, 'prefix': 'parent', 'readonly': True},
                    {'form': FunctionForm, 'prefix': 'function', 'readonly': False}]
    # Two formsets:
    # - the 'arg'  formset belongs to the 'function' (see above)
    # - the 'parg' formset belongs to the 'parent'
    formset_objects = [{'formsetClass': ArgFormSet, 'prefix': 'arg', 'readonly': False},
                       {'formsetClass': ArgFormSet, 'prefix': 'parg', 'readonly': True}]



class ObjectCopyMixin:
    model = None
    data = {'status': 'ok', 'html': ''}       # Create data to be returned    

    def post(self, request, object_id=None):
        # Copying is only possible through a POST request
        obj = get_object_or_404(self.model, id=object_id)
        # Create a copy of the object
        kwargs = {'currentuser': request.user}
        copy_obj = obj.get_copy(**kwargs)
        sMsg = ""
        # Check result
        if copy_obj == None:
            sMsg = "There was a problem copying the object"
            self.data['html'] = sMsg
            self.data['status'] = "error" 
        else:
            # Save the new object
            copy_obj.save()
        # Return the information
        return JsonResponse(self.data)


class ResearchCopy(ObjectCopyMixin, View):
    """Copy one 'Research' object"""
    model = Research
    success_url = reverse_lazy('seeker_list')


class ObjectDeleteMixin:
    model = None
    data = {'status': 'ok', 'html': ''}       # Create data to be returned    

    def post(self, request, object_id=None):
        # Note: deleting is only possible through a POST request
        obj = get_object_or_404(self.model, id=object_id)
        try:
            obj.delete()
        except:
            lInfo = sys.exc_info()
            if len(lInfo) == 1:
                sMsg = lInfo[0]
            else:
                sMsg = "{}<br>{}".format(lInfo[0], lInfo[1])
            self.data['html'] = sMsg
            self.data['status'] = "error" 
        # Return the information
        return JsonResponse(self.data)


class ResearchDelete(ObjectDeleteMixin, View):
    """Delete one 'Research' object"""
    model = Research
    
    
def research_edit(request, object_id=None):
    """Main entry point for the specification of a seeker research project"""

    # Initialisations
    template = 'seeker/research_details.html'
    arErr = []         # Start out with no errors

    # Check if the user is authenticated
    if not request.user.is_authenticated:
        # Simply redirect to the home page
        return redirect('nlogin')

    # Get the 'obj' to this project (or 'None' if it is a new one)
    if object_id is None:
        obj = None
        intro_message = "Create a new project"
        intro_breadcrumb = "New Project"
        sTargetType = ""
    else:
        # Get the instance of this research object
        obj = Research.objects.get(pk=object_id)
        intro_message = "Research project: <b>{}</b>".format(obj.name)
        intro_breadcrumb = "[{}]".format(obj.name)
        sTargetType = obj.targetType

    # Get a list of errors
    error_list = [str(item) for item in arErr]

    # Create the context
    context = dict(
        object_id = object_id,
        original=obj,
        intro_message=intro_message,
        intro_breadcrumb=intro_breadcrumb,
        targettype=sTargetType,
        error_list=error_list
        )

    # Open the template that allows Editing an existing or Creating a new research project
    #   or editing the existing project
    return render(request, template, context)
