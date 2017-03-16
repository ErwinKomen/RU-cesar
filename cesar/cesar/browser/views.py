"""
Definition of views.
"""

from django.views.generic.detail import DetailView
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, render
from django.http import HttpRequest, HttpResponse
from django.http import JsonResponse
from django.contrib import admin
from datetime import datetime
from cesar.settings import APP_PREFIX
from cesar.browser.services import *
from cesar.browser.models import *


def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'browser/index.html',
        {
            'title':'RU-Cesar',
            'year':datetime.now().year,
            'pfx': APP_PREFIX,
            'site_url': admin.site.site_url,
        }
    )

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'browser/contact.html',
        {
            'title':'Contact',
            'message':'Erwin Komen (E.komen@Let.ru.nl)',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'browser/about.html',
        {
            'title':'About',
            'message':'Radboud University CESAR utility.',
            'year':datetime.now().year,
        }
    )

def sync_crpp(request):
    """Synchronize information FROM /crpp"""

    assert isinstance(request, HttpRequest)
    # Add the information in the 'context' of the web page
    return render(
        request,
        'browser/crppsync.html',
        {
            'title':'Sync-Crpp',
            'message':'Radboud University CESAR utility.',
            'year':datetime.now().year
        }
    )

def sync_crpp_start(request):
    """Synchronize information FROM /crpp"""

    # Formulate a response
    data = {'status': 'done'}

    # Get the data from the CRPP api
    crpp_info = get_crpp_info()

    # Create a new synchronisation object that contains all relevant information
    oStatus = Status(status="loading")
    oStatus.save()

    # Start the 
    oResult = sync_crpp_process(crpp_info)
    if oResult == None or oResult['result'] == False:
        data.status = 'error'
    elif oResult != None:
        data['count'] = oResult

    # Return this response
    return JsonResponse(data)

def sync_crpp_progress(request):
    """Get the progress on the /crpp synchronisation process"""

    # Formulate a response
    data = {'status': 'unknown'}

    # Find the currently being used status
    oStatus = Status.objects.last()
    if oStatus != None:
        # Get the last status information
        data['status'] = oStatus.status
        data['count'] = oStatus.count

    # Return this response
    return JsonResponse(data)
