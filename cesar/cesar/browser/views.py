"""
Definition of views.
"""

from django.views.generic.detail import DetailView
from django.views.generic.base import RedirectView
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, render
from django.http import HttpRequest, HttpResponse
from django.http import JsonResponse
from django.contrib import admin
from django.db.models import Q
from django.db.models.functions import Lower
from datetime import datetime
from cesar.settings import APP_PREFIX
from cesar.browser.services import *
from cesar.browser.models import *
from cesar.browser.forms import *
import fnmatch

# Global variables
paginateSize = 10
paginateEntries = 100
paginateValues = (1000, 500, 250, 100, 50, 40, 30, 20, 10, )



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
            'year':datetime.now().year,
            'lng_list': build_choice_list(CORPUS_LANGUAGE),
            'part_list': Part.objects.all(),
            'format_list': build_choice_list(CORPUS_FORMAT)
        }
    )

def sync_crpp_start(request):
    """Synchronize information FROM /crpp"""

    # Get the synchronization type
    get = request.GET
    synctype = ""
    if 'synctype' in get:
        synctype = get['synctype']

    if synctype == '':
        # Formulate a response
        data = {'status': 'no sync type specified'}

    else:
        # Formulate a response
        data = {'status': 'done'}

        if synctype == "corpora":
            # Get the data from the CRPP api
            crpp_info = get_crpp_info()

            # Create a new synchronisation object that contains all relevant information
            oStatus = Status(status="loading")
            oStatus.save()

            # Update the models with the new information
            oResult = process_corpusinfo(crpp_info)
            if oResult == None or oResult['result'] == False:
                data.status = 'error'
            elif oResult != None:
                data['count'] = oResult

        elif synctype == "texts":
            part = Part.objects.filter(id=get['part'])
            if len(part) > 0:
                sPart = part[0].dir
                sLng = choice_english(CORPUS_LANGUAGE, part[0].corpus.lng)
                sFormat = choice_english(CORPUS_FORMAT, get['format'])

                # Create a new synchronisation object that contains all relevant information
                oStatus = Status(status="contacting", msg="Obtaining data from /crpp" )
                oStatus.save()

                # Get the data from the CRPP api
                crpp_texts = get_crpp_texts(sLng, sPart, sFormat)               

                # Create a new synchronisation object that contains all relevant information
                oStatus.status="loading"
                oStatus.msg="Updating the existing models with this new information"
                oStatus.save()

                # Update the models with the /crpp/txtlist information
                oResult = process_textlist(crpp_texts, get)

                # Process the reply from [process_textlist()]
                if oResult == None or oResult['result'] == False:
                    data.status = 'error'
                elif oResult != None:
                    data['count'] = oResult

            else:
                # Create a new synchronisation object that contains all relevant information
                oStatus = Status(status="error", msg="Cannot find [part] information" )
                oStatus.save()
                data.status = 'error'



            # Update the models with the new information


    # Return this response
    return JsonResponse(data)

def sync_crpp_progress(request):
    """Get the progress on the /crpp synchronisation process"""

    # Get the synchronization type
    get = request.GET
    synctype = ""
    if 'synctype' in get:
        synctype = get['synctype']

    if synctype == '':
        # Formulate a response
        data = {'status': 'no sync type specified'}

    else:
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

def adapt_search(val):
    # First trim
    val = val.strip()
    # Then add start and en matter 
    val = '^' + fnmatch.translate(val) + '$'
    return val



class PartDetailView(DetailView):
    """Details of one part"""

    model = Part
    template_name = 'browser/part_view.html'


class PartListView(ListView):
    """Provide a list of corpus-parts"""

    model = Part
    template_name = 'browser/part_list.html'
    paginate_by = paginateEntries
    entrycount = 0
    qs = None

    def get_qs(self):
        """Get the Part elements that are selected"""
        if self.qs == None:
            # Get the Lemma PKs
            qs = self.get_queryset()
        else:
            qs = self.qs
        return qs

    def render_to_response(self, context, **response_kwargs):
        """Check if a CSV response is needed or not"""
        if 'Csv' in self.request.GET.get('submit_type', ''):
            """ Provide CSV response"""
            return export_csv(self.get_qs(), 'begrippen')
        else:
            return super(PartListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PartListView, self).get_context_data(**kwargs)

        # Get parameters for the search
        initial = self.request.GET
        search_form = PartSearchForm(initial)

        context['searchform'] = search_form

        # Determine the count 
        context['entrycount'] = self.entrycount #  self.get_queryset().count()

        # Make sure the paginate-values are available
        context['paginateValues'] = paginateValues

        if 'paginate_by' in initial:
            context['paginateSize'] = int(initial['paginate_by'])
            self.paginate_by = int(initial['paginate_by'])
        else:
            context['paginateSize'] = self.paginate_by

        # Set the prefix
        context['app_prefix'] = APP_PREFIX

        # Set the title
        context['title'] = "Cesar corpus-parts"

        # Return the calculated context
        return context

    def get_queryset(self):

        # Get the parameters passed on with the GET request
        get = self.request.GET

        lstQ = []

        # Fine-tuning: search string is the Part
        if 'search' in get and get['search'] != '':
            # Allow simple wildcard search of the Part Name
            val = adapt_search(get['search'])
            lstQ.append(qs(name__iregex=val))

        # Fine-tuning: search string is the corpus
        if 'corpus' in get and get['corpus'] != '':
            # Allow simple wildcard search
            val = adapt_search(get['corpus'])
            lstQ.append(qs(corpus__name__iregex=val))

        # Check for second search criterion: metavar
        if 'metavar' in get and get['metavar'] != '':
            # Allow simple wildcard search
            val = adapt_search(get['metavar'])
            lstQ.append(qs(metavar__name__iregex=val))

        # Make the query set available
        qs = Part.objects.filter(*lstQ).distinct().select_related().order_by(
            Lower('metavar__name'),
            Lower('corpus__name'),
            Lower('name'))
        self.qs = qs

        # Set the entry count
        self.entrycount = len(self.qs)

        # Return the resulting filtered and sorted queryset
        return qs


class TextListView(ListView):
    """Provide a list of texts (in a part)"""

    model = Text
    template_name = 'browser/text_list.html'
    paginate_by = paginateEntries
    entrycount = 0
    qs = None

    def get_qs(self):
        """Get the Texts that are selected"""
        if self.qs == None:
            # Get the Lemma PKs
            qs = self.get_queryset()
        else:
            qs = self.qs
        return qs

    def render_to_response(self, context, **response_kwargs):
        """Check if a CSV response is needed or not"""
        if 'Csv' in self.request.GET.get('submit_type', ''):
            """ Provide CSV response"""
            return export_csv(self.get_qs(), 'begrippen')
        else:
            return super(TextListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(TextListView, self).get_context_data(**kwargs)

        # Get parameters for the search
        initial = self.request.GET
        search_form = TextSearchForm(initial)

        context['searchform'] = search_form

        # Determine the count 
        context['entrycount'] = self.entrycount #  self.get_queryset().count()

        # Make sure the paginate-values are available
        context['paginateValues'] = paginateValues

        if 'paginate_by' in initial:
            context['paginateSize'] = int(initial['paginate_by'])
            self.paginate_by = int(initial['paginate_by'])
        else:
            context['paginateSize'] = self.paginate_by

        # Set the prefix
        context['app_prefix'] = APP_PREFIX

        # Set the title
        context['title'] = "Cesar texts"

        # Return the calculated context
        return context

    def get_queryset(self):

        # Get the parameters passed on with the GET request
        get = self.request.GET

        lstQ = []

        # Fine-tuning: search string is the Part
        if 'search' in get and get['search'] != '':
            # Allow simple wildcard search of the Part Name
            val = adapt_search(get['search'])
            lstQ.append(qs(fileName__iregex=val))

        # Fine-tuning: search string is the corpus
        if 'corpus' in get and get['corpus'] != '':
            # Allow simple wildcard search
            val = adapt_search(get['corpus'])
            lstQ.append(qs(part__corpus__name__iregex=val))

        # Check for second search criterion: part
        if 'part' in get and get['part'] != '':
            # Allow simple wildcard search
            val = adapt_search(get['part'])
            lstQ.append(qs(part__iregex=val))

        # Additional fine-tuning: title
        if 'title' in get and get['title'] != '':
            # Allow simple wildcard search
            val = adapt_search(get['title'])
            lstQ.append(qs(title__iregex=val))

        # Make the query set available
        qs = Text.objects.filter(*lstQ).distinct().select_related().order_by(
            Lower('part__corpus__name'),
            Lower('part__name'),
            Lower('name'))
        self.qs = qs

        # Set the entry count
        self.entrycount = len(self.qs)

        # Return the resulting filtered and sorted queryset
        return qs


