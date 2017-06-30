"""
Definition of views for the SEEKER app.
"""

from django.forms import formset_factory
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.base import RedirectView
from django.views.generic import ListView

# from formtools.wizard.views import SessionWizardView

from cesar.seeker.forms import GatewayForm, VariableForm, SeekerResearchForm, ConstructionWrdForm, GvarForm, VarDefForm
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



def research_main(request, object_id=None):
    """Main entry point for the specification of a seeker research project"""

    # Check if the user is authenticated
    if not request.user.is_authenticated:
        # Simply redirect to the home page
        return redirect('home')

    # FOR FUTURE WORK:
    # Required for any view
    sForm = SeekerForm()
    sForm.add_formset(Gateway, Construction, ConstructionWrdForm)
    sForm.add_formset(Gateway, GlobalVariable, GvarForm)
    sForm.add_formset(Gateway, VarDef, VarDefForm)

    # This is required for any view
    ConstructionFormSet = inlineformset_factory(Gateway, Construction, form=ConstructionWrdForm, min_num=1, extra=0, can_delete=True, can_order=True)
    GvarFormSet = inlineformset_factory(Gateway, GlobalVariable, form=GvarForm, min_num=1, extra=0, can_delete=True, can_order=True)
    VardefFormSet = inlineformset_factory(Gateway, VarDef, form=VarDefForm, min_num=1, extra=0, can_delete=True, can_order=True)
    # Initialisation
    construction_formset = None
    gvar_formset = None
    vardef_formset = None
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
                arErr.append(gvar_formset.errors)
                # Delete the gateway we created
                gateway.delete()
        else:
            arErr.append(form.errors)

    else:
        # This is a GET request, so get an empty form
        if add:
            initial = get_changeform_initial_data(ModelForm, request)
            # form = SeekerResearchForm()
            form = ModelForm(initial=initial)
            # Create a completely new formset
            construction_formset = ConstructionFormSet(prefix='construction')
            gvar_formset = GvarFormSet(prefix='gvar')
            vardef_formset = VardefFormSet(prefix='vardef')
        elif '/delete/' in request.path:
            # We need to delete
            # TODO: ask for confirmation

            # Perform the deletion of the Research object
            obj.delete()
            # Redirect to the list of projects
            return redirect('seeker_list')
        else:
            form = ModelForm(instance=obj)
            # create a formset for this particular instance
            construction_formset = ConstructionFormSet(prefix='construction', instance=obj.gateway)
            gvar_formset = GvarFormSet(prefix='gvar', instance=obj.gateway)
            vardef_formset = VardefFormSet(prefix='vardef', instance=obj.gateway)

    # COnvert all lists of errors to a string
    sErr = '\n'.join(arErr).strip()


    # Start setting the context
    context = dict(
        object_id = object_id,
        original=obj,
        form = form,
        construction_formset = construction_formset,
        gvar_formset = gvar_formset,
        vardef_formset = vardef_formset,
        show_save = True,
        show_save_and_continue = True,
        show_save_and_add_another = True,
        show_delete_link = not add,
        delete_url=delete_url,
        error_list=sErr,
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
