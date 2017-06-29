"""
Definition of views for the SEEKER app.
"""

from django.forms import formset_factory
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.base import RedirectView
from django.views.generic import ListView

# from formtools.wizard.views import SessionWizardView

from cesar.seeker.forms import GatewayForm, VariableForm, SeekerResearchForm, ConstructionWrdForm
from cesar.seeker.models import *
from cesar.settings import APP_PREFIX

TO_FIELD_VAR = '_to_field'

#GATEWAY_FORMS = [
#    ("step1", Form1),
#    ("step2", Form2),
#]
#GATEWAY_TEMPLATES = { 
#    "step1": "template/path/step1.html",
#    "step2": "template/path/step2.html"
#}


#class SeekerGatewayWizard(SessionWizardView):
#    # my awesome code
#    x = 1

#seeker_gateway_wizard_view = SeekerGatewayWizard.as_view(GATEWAY_FORMS)


class GatewayDetailView(DetailView):
    model = Gateway
    form_class = GatewayForm
    template_name = 'seeker/gateway_view.html'


class GatewayCreateView(CreateView):
    model = Gateway


class SeekerListView(ListView):
    model = Research


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



def research_main(request, object_id=None):
    """Main entry point for the specification of a seeker research project"""

    # This is required for any view
    ConstructionFormSet = inlineformset_factory(Gateway, Construction, form=ConstructionWrdForm, extra=1, can_delete=True, can_order=True)
    # Initialisation
    construction_formset = None
    template = 'seeker/research_edit.html'

    # copied from django/contrib/admin/options.py changeform_view()
    # to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))

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
        # obj = Research.get_object(request, unquote(object_id), to_field)
        obj = Research.objects.filter(pk=object_id)
        # TODO: act if this object does not exist

    # Some initialisations
    ModelForm = SeekerResearchForm
    form_validated = False

    # Find out how we get here
    if request.method == 'POST':
        gatewayForm = GatewayForm(request.POST)
        if gatewayForm.is_valid():
            gateway = gatewayForm.save(commit=False)
            # TODO: possible changes to the gateway...

            # Save the gateway instance...
            gateway.save()
        # This is a POST request, so this is an existing form
        # BUT: the [obj] may not exist if this is a new object
        if obj == None:
            form = ModelForm(request.POST, request.FILES)
        else:
            form = ModelForm(request.POST, request.FILES, instance=obj)


        # Also get all required formsets
        construction_formset = ConstructionFormSet(request.POST, request.FILES, prefix='construction')
        # Walk the formset
        for cns_form in construction_formset:
            # Check if this form is valid
            if cns_form.is_valid():
                # Save it preliminarily
                cns = cns_form.save(commit=False)
                # Add the correct search item
                cns.search = SearchMain.create_item("word-group", cns_form.cleaned_data['value'], 'groupmatches')
                # Add the link to the correct gateway
                cns.gateway = gateway
                # Save this construction
                cns.save()
                cns_form.save()
        # If the form is valid we can save it
        if form.is_valid():
            form_validated = True
            # Save the form
            new_object = form.save(commit=False)
            new_object.gateway = gateway
        else:
            new_object = form.instance
            # Remove any gateway that was created
            gateway.delete()
        # Are we valid?
        if construction_formset.is_valid() and form_validated:
            # All valid: 
            # - save the model instance
            new_object.save()
            # construction_formset.save()
            # If the form is valid and the user pressed 'save' then show a summary
            # TODO: Show a summary
            if add:
                return redirect('home')
            else:
                return redirect('home')
        else:
            sErr = construction_formset.errors
    else:
        # This is a GET request, so get an empty form
        if add:
            initial = get_changeform_initial_data(ModelForm, request)
            # form = SeekerResearchForm()
            form = ModelForm(initial=initial)
            # Create a completely new formset
            construction_formset = ConstructionFormSet(prefix='construction')
        else:
            form = ModelForm(instance=obj)
            # create a formset for this particular instance
            construction_formset = ConstructionFormSet(prefix='construction', instance=obj)


    # Start setting the context
    context = dict(
        object_id = object_id,
        original=obj,
        form = form,
        construction_formset = construction_formset,
        show_save = True,
        show_save_and_continue = True,
        show_save_and_add_another = True,
        show_delete_link = not add,
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
