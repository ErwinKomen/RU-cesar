"""
Definition of views for the DOC app.
"""

from django.db.models import Q
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django import template
from datetime import datetime

from cesar.settings import APP_PREFIX



# Create your views here.
def doc(request):
    """The main page of working with documents."""

    assert isinstance(request, HttpRequest)
    template = 'doc/doc_main.html'
    context = {'title': 'Document processing',
               'message': 'Radboud University CESAR',
               'year': datetime.now().year}
    return render(request, template, context)

