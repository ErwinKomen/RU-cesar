"""
Definition of views for the SEEKER app.
"""

from django.forms import formset_factory
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.base import RedirectView
from django.views.generic import ListView

from formtools.wizard.views import SessionWizardView

from cesar.seeker.forms import GatewayForm, VariableForm
from cesar.seeker.models import *
from cesar.settings import APP_PREFIX

GATEWAY_FORMS = [
    ("step1", Form1),
    ("step2", Form2),
]
GATEWAY_TEMPLATES = { 
    "step1": "template/path/step1.html",
    "step2": "template/path/step2.html"
}


class SeekerGatewayWizard(SessionWizardView):
    # my awesome code
    x = 1

seeker_gateway_wizard_view = SeekerGatewayWizard.as_view(GATEWAY_FORMS)


class GatewayDetailView(DetailView):
    model = Gateway
    form_class = GatewayForm
    template_name = 'seeker/gateway_view.html'


class GatewayCreateView(CreateView):
    model = Gateway


class SeekerListView(ListView):
    model = Research
