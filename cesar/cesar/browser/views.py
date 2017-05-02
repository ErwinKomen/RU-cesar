"""
Definition of views.
"""

from django.views.generic.detail import DetailView
from django.views.generic.base import RedirectView
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpRequest, HttpResponse
from django.http import JsonResponse
from django.contrib import admin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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
paginateEntries = 20
paginateSentences = 30
paginateValues = (1000, 500, 250, 100, 50, 40, 30, 20, 10, )


def get_item_list(lVar, lFun, qs):
    """Turn the queryset [qs] into a list of Items that have first and last information"""

    # Initialize the variables whose changes are important
    oVariable = {}
    for i, key in enumerate(lVar):
        oVariable[key] = "" # {'name': key, 'fun': lFun[i]}
    lItem = []
    iLast = len(qs)-1
    # Iterate over the entries looking for first, last etc
    for i, entry in enumerate(qs):
        bIsLastEntry = (i==iLast)
        oItem = {'entry': entry}
        for k in lVar:
            oItem[k] = {'first':False, 'last':False}
        bIsDict = isinstance(entry, dict)
        bVarIsLast = False
        # Check for changes in all the variables
        for j, k in enumerate(lVar):
            fun = lFun[j]
            if callable(fun):
                sValue = fun(entry)
            else:
                for idx, val in enumerate(fun):
                    if idx==0:
                        if bIsDict:
                            sValue = entry[val]
                        else:
                            sValue = getattr(entry, val)
                    else:
                        if bIsDict:
                            sValue = sValue[val]
                        else:
                            sValue = getattr(sValue, val)
            # Check for changes in the value of the variable 
            # if sValue != oVariable[k]:
            if sValue != oVariable[k] or bVarIsLast or (i>0 and lItem[i-1][k]['last']):
                # Check if the previous one's [last] must be changed
                if oVariable[k] != "": lItem[i-1][k]['last'] = True
                # Adapt the current one's [first] property
                oItem[k]['first']= True
                # Adapt the variable
                oVariable[k] = sValue      
                # Indicate that the next ones should be regarded as 'last'
                bVarIsLast = True      
            # Check if this is the last
            if bIsLastEntry: oItem[k]['last'] = True
        # Add this object to the list of items
        lItem.append(oItem)
    # Return the list we have made
    return lItem

def get_int_choice(lGetDict, sKey):
    if lGetDict == None or sKey == None or sKey == "":
        return -1
    if sKey in lGetDict and lGetDict[sKey] != "":
        return int(lGetDict[sKey])
    else:
        return -1

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

def get_text_lines(instText):
    """Retrieve the lines for this text"""

    # Find out which part this is
    part = instText.part
    # Get the necessary parameters: lng, ext, dir
    sLng = part.corpus.get_lng_display()
    sDir = part.dir
    sName = instText.fileName
    sFormat = instText.get_format_display()
    # Now try to get the information
    oBack = get_crpp_text(sLng, sDir, sFormat, sName)
    # Prepare what we return
    if oBack == None or oBack['status'] == 'error':
        return None
    else:
        return oBack


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


class SentenceListView(ListView):
    """Show the sentences in one particular text"""

    model = Sentence
    template_name = 'browser/sentence_list.html'
    paginate_by = paginateSentences
    entrycount = 0
    qs = None
    line_list = None
    lines = None
    linecount = 0
    text = None

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SentenceListView, self).get_context_data(**kwargs)

        # Get parameters for the search
        initial = self.request.GET

        # Make sure the paginate-values are available
        context['paginateValues'] = paginateValues

        if 'paginate_by' in initial:
            context['paginateSize'] = int(initial['paginate_by'])
            self.paginate_by = int(initial['paginate_by'])
        else:
            context['paginateSize'] = self.paginate_by

        # Set other needed values
        context['text'] = self.text
        context['linecount'] = self.entrycount

        # Set the prefix
        context['app_prefix'] = APP_PREFIX

        # Return what we have
        return context

    def get_queryset(self):

        # Get the parameters passed on with the GET request
        get = self.request.GET

        # Get the Text object
        textlist = Text.objects.filter(id=self.kwargs['pk'])
        if textlist != None and textlist.count() >0:
            self.text = textlist[0]
            self.qs = self.text.get_sentences()
            # Set the entry count
            self.entrycount = self.qs.count()
        else:
            self.qs = None
            self.entrycount = 0

        # Return the resulting filtered and sorted queryset
        return self.qs


class TextDetailView(DetailView):
    """Allow viewing and editing details of one text"""

    model = Text
    form_class = TextForm
    template_name = 'browser/text_view.html'
    last_url = ''

    def post(self, request, pk):
        text = get_object_or_404(Text, pk=pk)
        bound_form = self.form_class(request.POST, instance=text)
        oUser = self.request.user
        if oUser.is_superUser:
          if bound_form.is_valid():
              new_text = bound_form.save()
              # Find out what to do next
              if '_save' in request.POST:
                  if 'last_url' in request.POST:
                      return redirect(request.POST['last_url'])
                  else:
                      return redirect('text_list')
              elif '_continue' in request.POST:
                  # return redirect(new_text, status = 'save_continue')

                  # return render(request, new_text.get_absolute_url(), {'status': 'save_continue'})

                  #context = {'form': bound_form,
                  #           'text': new_text,
                  #           'status': 'save_continue'}
                  #return render( request, self.template_name, context)
                  return redirect(new_text.get_absolute_url() + "?status=save_continue")
          else:
              context = {'form': bound_form,
                         'text': text,
                         'status': 'error'}
              return render( request, self.template_name, context)
        else:
          # Not the superuser
          context = {'form': bound_form,
                      'text': text,
                      'status': 'error',
                      'msg': 'Need to be super-user'}
          return render( request, self.template_name, context)


    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(TextDetailView, self).get_context_data(**kwargs)

        # Get parameters for the search
        initial = self.request.GET

        # Pass on the form
        context['form'] = self.form_class(instance=self.object)

        # Establish the 'last_url' part
        if 'last_url' in initial:
            context['last_url'] = initial['last_url']
        else:
            context['last_url'] = ''

        status = ""
        if 'status' in initial:
            status = initial['status']
        context['status'] = status

        # Return what we have
        return context

    def get_queryset(self):

        # Get the parameters passed on with the GET request
        get = self.request.GET

        self.queryset = super(TextDetailView,self).get_queryset()

        # Return the resulting filtered and sorted queryset
        return self.queryset

      
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

        # Specify the search form
        search_form = TextSearchForm(initial)
        context['searchform'] = search_form

        # REcall integer choices
        context['partchoice'] = get_int_choice(initial, 'part')
        context['formatchoice'] = get_int_choice(initial, 'format')

        # Set the options for the <select> boxes
        # context['lng_list'] = build_choice_list(CORPUS_LANGUAGE)
        # context['corpus_list'] = [crp for crp in Corpus.objects.all().order_by('name')]

        # Get a list with 'first' and 'last values for each item in the PART queryset
        context['part_list'] = self.get_partlist()

        # Need to have a list of possible formats
        context['format_list'] = build_choice_list(CORPUS_FORMAT)

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


        # Remember where we are
        # ONLY GIVES PARTIAL: context['url'] = self.request.resolver_match.url_name
        context['url'] = self.request.get_full_path()

        # Return the calculated context
        return context

    def get_partlist(self):
        """Get a list of Part elements + first/last information"""

        # REtrieve the correct queryset, sorted on the correct levels
        qs = [prt for prt in Part.objects.all().order_by('corpus__lng', 'corpus__name', 'name')]
        # Start the output
        html = []
        # Initialize the variables whose changes are important
        lVars = ["corpus_lng", "corpus_name", "name"]
        lFuns = [Part.language, ["corpus", "name"], ["name"]]
        # Get a list of items containing 'first' and 'last' information
        lItem = get_item_list(lVars, lFuns, qs)
        # REturn this list
        return lItem
      
    def get_queryset(self):

        # Get the parameters passed on with the GET request
        get = self.request.GET

        lstQ = []

        # Filter on text Format
        if 'format' in get and get['format'] != '':
            lstQ.append(Q(format=get['format']))

        # Filter on text Part
        if 'part' in get and get['part'] != '':
            lstQ.append(Q(part=get['part']))

        # Filter on text Name
        if 'fileName' in get and get['fileName'] != '':
            # Allow simple wildcard search
            val = adapt_search(get['fileName'])
            lstQ.append(Q(fileName__iregex=val))

        # Filter on text Genre
        if 'genre' in get and get['genre'] != '':
            # Allow simple wildcard search
            val = adapt_search(get['genre'])
            lstQ.append(Q(genre__iregex=val))

        # Filter on text date
        if 'date' in get and get['date'] != '':
            # Allow simple wildcard search
            val = adapt_search(get['date'])
            lstQ.append(Q(date__iregex=val))

        # Filter on text Title
        if 'title' in get and get['title'] != '':
            # Allow simple wildcard search
            val = adapt_search(get['title'])
            lstQ.append(Q(title__iregex=val))

        # Filter on text Author
        if 'author' in get and get['author'] != '':
            # Allow simple wildcard search
            val = adapt_search(get['author'])
            lstQ.append(Q(author__iregex=val))

        # Filter on text Subtype
        if 'subtype' in get and get['subtype'] != '':
            # Allow simple wildcard search
            val = adapt_search(get['subtype'])
            lstQ.append(Q(subtype__iregex=val))

        # Make the query set available
        qs = Text.objects.filter(*lstQ).distinct().select_related().order_by(
            Lower('part__corpus__name'),
            Lower('part__name'),
            Lower('fileName'))
        self.qs = qs

        # Set the entry count
        self.entrycount = len(self.qs)

        # Return the resulting filtered and sorted queryset
        return qs


