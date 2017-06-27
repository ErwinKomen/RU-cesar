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


def research_main(request):
    """Main entry point for the specification of a seeker research project"""

    # This is required for any view
    ConstructionFormSet = inlineformset_factory(Gateway, Construction, form=ConstructionWrdForm, extra=1, can_delete=True, can_order=True)
    # Initialisation
    construction_formset = None
    template = 'seeker/research_edit.html'

    # Find out how we get here
    if request.method == 'POST':
        # This is a POST request, so this is an existing form
        form = SeekerResearchForm(request.POST)
        # Also get all required formsets
        construction_formset = ConstructionFormSet(request.POST, request.FILES, prefix='construction')
        # If the form is valid we can save it
        if form.is_valid() and construction_formset.is_valid():
            # Save the form
            form.save()
            # If the form is valid and the user pressed 'save' then show a summary
            # TODO: Show a summary
            return redirect('home')
    else:
        # This is a GET request, so get an empty form
        form = SeekerResearchForm()
        construction_formset = ConstructionFormSet(prefix='construction')

    # Get the context
    context = {'form': form, 'construction_formset': construction_formset}

    # Open the template that allows Creating a new research project
    #   or editing the existing project
    return render(request, template, context)
