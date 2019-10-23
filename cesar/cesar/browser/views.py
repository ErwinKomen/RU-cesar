"""
Definition of views for the BROWSER app.
"""

from django.contrib import admin
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import Group
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.views.generic.detail import DetailView
from django.views.generic.base import RedirectView
from django.views.generic import ListView, View
from datetime import datetime
from time import sleep

from cesar.settings import APP_PREFIX
from cesar.browser.services import *
from cesar.browser.models import *
from cesar.browser.forms import *
from cesar.utils import ErrHandle
from cesar.viewer.models import NewsItem
import fnmatch
import sys
import base64
import re

# Global variables
paginateSize = 10
paginateEntries = 20
paginateSentences = 30
paginateValues = (1000, 500, 250, 100, 50, 40, 30, 20, 10, )
bDebug = True

# ============================= LOCAL CLASSES ======================================
errHandle = ErrHandle()


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

def get_current_userid():
    sDefaultUser = 'erkomen'
    sDefaultUser = 'cesarbr'
    return sDefaultUser

def treat_bom(sHtml):
    """REmove the BOM marker except at the beginning of the string"""

    # Check if it is in the beginning
    bStartsWithBom = sHtml.startswith(u'\ufeff')
    # Remove everywhere
    sHtml = sHtml.replace(u'\ufeff', '')
    # Return what we have
    return sHtml

def adapt_htable(oHtable):
    """Adapt a hierarchical table object"""

    # Starting the summary
    summary = ""
    # Get any text at this level
    if 'txt' in oHtable:
        if 'type' in oHtable and oHtable['type'] != 'Star' and oHtable['type'] != 'Zero':
            if summary != "": summary += " "
            summary += oHtable['txt']
    # Walk all the [child] tables
    if 'child' in oHtable:
        # Do this depth-first
        for chTable in oHtable['child']:
            # First go down
            oBack = adapt_htable(chTable)
            # Add the summary
            if 'summary' in oBack:
                if summary != "": summary += " "
                summary += oBack['summary']
    # Then set the summary link
    oHtable['summary'] = summary

    # Return the result
    return oHtable

def user_is_authenticated(request):
    # Is this user authenticated?
    username = request.user.username
    user = User.objects.filter(username=username).first()
    return user.is_authenticated

def user_is_ingroup(request, sGroup):
    # Is this user part of the indicated group?
    username = request.user.username
    user = User.objects.filter(username=username).first()
    # glist = user.groups.values_list('name', flat=True)

    # Only look at group if the user is known
    if user == None:
        glist = []
    else:
        glist = [x.name for x in user.groups.all()]

        # Only needed for debugging
        if bDebug:
            ErrHandle().Status("User [{}] is in groups: {}".format(user, glist))
    # Evaluate the list
    bIsInGroup = (sGroup in glist)
    return bIsInGroup

def home(request):
    """Renders the home page."""

    assert isinstance(request, HttpRequest)
    # Specify the template
    template_name = 'index.html'

    # Define the initial context
    context =  {'title':'RU-Cesar','year':datetime.now().year,
                'is_longdale_user': user_is_ingroup(request, 'longdale_user'),
                'pfx': APP_PREFIX,'site_url': admin.site.site_url}

    # Double check who this is
    username = request.user.username
    if username != None and username != "":
        valid = re.match('^[\w-]+$', username) is not None
        if not valid:
            context['message'] = "Your username contains symbols other than letters and digits. " +\
                "This means you may not be able to get results when running Cesar. " +\
                "<p>Two options:" + \
                "<ul><li>Log off and sign up under a new name. That user will not contain the projects you have made.</li>" + \
                "<li>Mail the Cesar administrator with a request to change your username. You will keep all your search projects.</li></ul></p>"

    # Create the list of news-items
    lstQ = []
    lstQ.append(Q(status='val'))
    newsitem_list = NewsItem.objects.filter(*lstQ).order_by('-saved', '-created')
    context['newsitem_list'] = newsitem_list
    # Make sure we add special group permission(s)
    context['is_in_tsg'] = user_is_ingroup(request, "radboud-tsg")
    # Render and return the page
    return render(request, template_name, context)

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'contact.html',
        {   'is_longdale_user': user_is_ingroup(request, 'longdale_user'),
            'title':'Contact',
            'message':'Henk van den Heuvel',
            'year':datetime.now().year,
        }
    )

def more(request):
    """Renders the more page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'more.html',
        {   'is_longdale_user': user_is_ingroup(request, 'longdale_user'),
            'title':'More',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'about.html',
        {   'is_longdale_user': user_is_ingroup(request, 'longdale_user'),
            'title':'About',
            'message':'Radboud University CESAR utility.',
            'year':datetime.now().year,
        }
    )

def short(request):
    """Renders the page with the short instructions."""

    assert isinstance(request, HttpRequest)
    template = 'short.html'
    context = {'title': 'Short overview',
               'is_longdale_user': user_is_ingroup(request, 'longdale_user'),
               'message': 'Radboud University CESAR short intro',
               'year': datetime.now().year}
    return render(request, template, context)

def nlogin(request):
    """Renders the not-logged-in page."""
    assert isinstance(request, HttpRequest)
    context =  {    'title':'Not logged in', 
                    'message':'Radboud University CESAR utility.',
                    'year':datetime.now().year,}
    return render(request,'nlogin.html', context)

def signup(request):
    """Provide basic sign up and validation of it """

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Save the form
            form.save()
            # Create the user
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            # also make sure that the user gets into the STAFF,
            #      otherwise he/she may not see the admin pages
            user = authenticate(username=username, 
                                password=raw_password,
                                is_staff=True)
            user.is_staff = True
            user.save()
            # Add user to the "RegistryUser" group
            gQs = Group.objects.filter(name="seeker_user")
            if gQs.count() > 0:
                g = gQs[0]
                g.user_set.add(user)
            # Log in as the user
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def sync_crpp(request):
    """Synchronize information FROM /crpp"""

    assert isinstance(request, HttpRequest)

    # Gather info
    context =  { 'title':'Sync-Crpp',
            'message':'Radboud University CESAR utility.',
            'year':datetime.now().year,
            'lng_list': build_choice_list(CORPUS_LANGUAGE),
            'part_list': Part.get_parts(),
            'format_list': build_choice_list(CORPUS_FORMAT)
        }
    template_name = 'browser/crppsync.html'

    # Add the information in the 'context' of the web page
    return render(request, template_name, context)



def sync_crpp_start(request):
    """Synchronize information FROM /crpp"""

    oErr = ErrHandle()
    data = {'status': 'starting'}
    try:
        # Get the user
        username = request.user.username
        # Get the synchronization type
        get = request.GET
        synctype = ""
        if 'synctype' in get:
            synctype = get['synctype']

        if synctype == '':
            # Formulate a response
            data['status'] = 'no sync type specified'

        else:
            # Remove previous status objects for this combination of user/type
            lstQ = []
            lstQ.append(Q(user=username))
            lstQ.append(Q(type=synctype))
            qs = Status.objects.filter(*lstQ)
            qs.delete()

            # Create a status object for this combination of synctype/user
            oStatus = Status(user=username, type=synctype, status="preparing")
            oStatus.save()

            # Formulate a response
            data['status'] = 'done'

            if synctype == "corpora":
                # Get the data from the CRPP api
                crpp_info = get_crpp_info()

                # Use the synchronisation object that contains all relevant information
                oStatus.set("loading")

                # Update the models with the new information
                oResult = process_corpusinfo(oStatus, crpp_info)
                if oResult == None or oResult['result'] == False:
                    data.status = 'error'
                elif oResult != None:
                    data['count'] = oResult

            elif synctype == "texts":
                # Update texts from a particular part and a particular format
                part = Part.objects.filter(id=get['part']).first()
                if part != None:
                    sPart = part.dir
                    sLng = choice_english(CORPUS_LANGUAGE, part.corpus.lng)
                    sFormat = choice_english(CORPUS_FORMAT, get['format'])

                    # Updating options
                    bUpdateOnly = 'updateonly' in get
                    bDeleteFirst = 'deletefirst' in get

                    # Use the appropriate synchronisation object that contains all relevant information
                    oStatus.set("contacting", msg="Obtaining data from /crpp")

                    # Get the data from the CRPP api: this only returns a JOBID
                    crpp_texts = get_crpp_texts(sLng, sPart, sFormat, oStatus)

                    # Check what we get here
                    if 'status' in crpp_texts and crpp_texts['status'] == 'error':
                        # There is an error
                        data['status'] = 'error'
                        data['msg'] = json.dumps(crpp_texts)
                        oStatus.set("error", msg=data['msg'] )
                    else:
                        # Seem to have a good response

                        # Create a new synchronisation object that contains all relevant information
                        oStatus.set("loading", msg="Updating the existing models with this new information")

                        # Update the models with the /crpp/txtlist information
                        bNoDeleting = not bDeleteFirst
                        options = {'nodeleting': bNoDeleting, 'updating': bUpdateOnly, 'update_field': 'words'}
                        oResult = process_textlist(crpp_texts, part, sFormat, oStatus, options)

                        # Process the reply from [process_textlist()]
                        if oResult == None or ('result' in oResult and oResult['result'] == False):
                            data['status'] = 'error'
                        elif not 'total' in oResult:
                            data['status'] = 'error'
                        elif oResult != None:
                            data['count'] = oResult

                        # Completely ready
                        oStatus.set("done", oResult)

                else:
                    # Create a new synchronisation object that contains all relevant information
                    oStatus.set("error", msg="Cannot find [part] information" )
                    data['status'] = 'error'

            elif synctype == "alltexts":
                # Create a new synchronisation object that contains all relevant information
                oStatus.set("contacting", msg="Obtaining data from /crpp")

                data['count'] = 0
                oBack = {}

                # ================ IMPORTANT ===========================
                # Delete everything that is already theres
                oStatus.set("deleting")
                Text.objects.all().delete()

                # Only now do we start in full
                oStatus.set("continuing")

                # We are going to try and update ALL the texts in the entire application
                for part in Part.objects.all():
                    sPart = part.dir
                    sLng = choice_english(CORPUS_LANGUAGE, part.corpus.lng)
                    # Walk all available text formats
                    for sFormat in ['folia', 'psdx']:
                        # Note what we are doing
                        data['lng'] = sLng
                        data['part'] = sPart
                        data['format'] = sFormat

                        # Update the synchronisation object that contains all relevant information
                        oBack['lng'] = sLng
                        oBack['part'] = sPart
                        oBack['format'] = sFormat
                        oStatus.set("crpp", oBack)

                        # Get the data from the CRPP api
                        crpp_texts = get_crpp_texts(sLng, sPart, sFormat, oStatus)               

                        # Check the status of what has been returned
                        if crpp_texts['status'] != "error":
                            # Status is ok, so continue.

                            # Update the models with the /crpp/txtlist information
                            oResult = process_textlist(crpp_texts, part, sFormat, oStatus, True)

                            # Process the reply from [process_textlist()]
                            if oResult == None or oResult['result'] == False:
                                data.status = 'error'
                                oStatus.set("error")
                            elif oResult != None:
                                data['count'] += oResult['total']
                                oResult['alltexts'] = data['count']
                                oStatus.set("okay", oResult)
                                oBack = oResult
                # Completely ready
                oStatus.set("done", oBack)

            elif synctype == "clearsentences":
                # Clear all the Sentence elements
                oStatus.set("contacting", msg="Obtaining data from /crpp")
                oBack = {}

                # ================ IMPORTANT ===========================
                # Delete everything that is already theres
                oStatus.set("deleting")
                Sentence.objects.all().delete()

                # Completely ready
                oStatus.set("done", oBack)
                

    except:
        oErr.DoError("sync_crpp_start error")
        data['status'] = "error"

    # Return this response
    return JsonResponse(data)

def sync_crpp_progress(request):
    """Get the progress on the /crpp synchronisation process"""

    oErr = ErrHandle()
    data = {'status': 'preparing'}

    try:
        # Get the user
        username = request.user.username
        # Get the synchronization type
        get = request.GET
        synctype = ""
        if 'synctype' in get:
            synctype = get['synctype']

        if synctype == '':
            # Formulate a response
            data['status'] = 'error'
            data['msg'] = "no sync type specified" 

        else:
            # Formulate a response
            data['status'] = 'UNKNOWN'

            # Get the appropriate status object
            # sleep(1)
            oStatus = Status.objects.filter(user=username, type=synctype).first()

            # Check what we received
            if oStatus == None:
                # There is no status object for this type
                data['status'] = 'error'
                data['msg'] = "Cannot find status for {}/{}".format(
                    username, synctype)
            else:
                # Get the last status information
                data['status'] = oStatus.status
                data['msg'] = oStatus.msg
                data['count'] = oStatus.count

        # Return this response
        return JsonResponse(data)
    except:
        oErr.DoError("sync_crpp_start error")
        data = {'status': 'error'}

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
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated: 
            return nlogin(request)
        return super(PartDetailView).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated: 
            return nlogin(request)
        return super(PartDetailView).post(request, *args, **kwargs)


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
        if not self.request.user.is_authenticated:
            # Do not allow to get a good response
            return nlogin(self.request)
        elif 'Csv' in self.request.GET.get('submit_type', ''):
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

        # Add some information
        context['is_in_tsg'] = user_is_ingroup(self.request, "radboud-tsg")
        
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
            Lower('corpus__name'),
            Lower('name'),
            )
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
    error_msg = ""
    text = None

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Do not allow to get a good response
            return nlogin(request)
        else:
            response = super(SentenceListView, self).get(request, *args, **kwargs)
        return response

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Do not allow to get a good response
            return nlogin(request)
        else:
            response = super(SentenceListView, self).post(request, *args, **kwargs)
        return response

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SentenceListView, self).get_context_data(**kwargs)

        # Get parameters for the search
        initial = self.request.GET

        # Check for objects
        if context['object_list'] == None or self.error_msg != "":
            if self.error_msg != "":
                context['error_msg'] = self.error_msg
                errHandle.Status("SentenceListView error: "+self.error_msg)
            else:
                context['error_msg'] = "No data could be retrieved"
        else:
            context['error_msg'] = ""

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
        self.error_msg = ""

        # Initialize the reply as empty
        self.entrycount = 0
        self.qs = []

        # Get the Text object
        textlist = Text.objects.filter(id=self.kwargs['pk'])
        if textlist != None and textlist.count() >0:
            self.text = textlist[0]
            oSent = self.text.get_sentences()
            if oSent == None:
                self.error_msg = "The reply from 'get_sentences()' was empty"
            elif not 'status' in oSent or not 'qs' in oSent:
                if 'code' in oSent:
                    self.error_msg = oSent['code']
                else:
                    self.error_msg = "The reply from 'get_sentences()' is no object: {}".format(oSent)
            else:
                # Set the QS
                self.qs = oSent['qs']
                # Set the entry count
                self.entrycount = self.qs.count()

        # Return the resulting filtered and sorted queryset
        return self.qs


class SentenceDetailView(DetailView):
    """Get and show the details of one sentence"""

    model = Sentence
    template_name = 'browser/sentence_view.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Do not allow to get a good response
            response = nlogin(request)
        else:
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            response = self.render_to_response(context)
            #response.content = treat_bom(response.rendered_content)
        return response

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Do not allow to get a good response
            response = nlogin(request)
        else:
            self.object = self.get_object()
            # Initialize
            response = None
            context = self.get_context_data(object=self.object)
            # Get the download type
            self.qd = request.POST
            if 'downloadtype' in self.qd and 'downloaddata' in self.qd:
                # Get the download type and the data itself
                dtype = self.qd['downloadtype']
                ddata = self.qd['downloaddata']
            
                if dtype == "tree":
                    dext = ".svg"
                    sContentType = "application/svg"
                elif dtype == "htable":
                    dext = ".html"
                    sContentType = "application/html"
                elif (dtype == "htable-png" or dtype == "tree-png"):
                    dext = ".png"
                    # sContentType = "application/octet-stream"
                    sContentType = "image/png"
                    # Read base64 encoded part
                    arPart = ddata.split(";")
                    dSecond = arPart[1]
                    # Strip off the preceding "base64," part
                    ddata = dSecond.replace("base64,", "")
                    # Convert string to bytestring
                    ddata = ddata.encode()
                    # Decode base64 into binary
                    ddata = base64.decodestring(ddata)
                    # Strip -png off
                    dtype = dtype.replace("-png", "")


                # Determine a file name
                sBase = self.object.text.fileName
                sIdt = self.object.identifier
                if not sBase in sIdt:
                    sIdt = "{}_{}".format( sBase, sIdt)
                sFileName = "{}_{}{}".format(sIdt, dtype, dext)

                response = HttpResponse(ddata, content_type=sContentType)
                response['Content-Disposition'] = 'attachment; filename="{}"'.format(sFileName)    

            else:
                response = self.render_to_response(context)
        # Return the response we have
        return response

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SentenceDetailView, self).get_context_data(**kwargs)

        # Get parameters for the search
        initial = self.request.GET

        # Establish the 'last_url' part
        if 'last_url' in initial:
            context['last_url'] = initial['last_url']
        else:
            context['last_url'] = ''

        status = ""
        if 'status' in initial:
            status = initial['status']
        context['status'] = status

        # Fetch the TREE belonging to this sentence
        sentence = context['sentence']
        options = {'userid': get_current_userid(),
                   'lng': sentence.text.part.corpus.get_lng_display(),
                   'dir': sentence.text.part.dir,
                   'ext': sentence.text.get_format_display(),
                   'name': sentence.text.fileName,
                   'locs': sentence.identifier,
                   'locw': '',
                   'type': 'syntax_svg_tree'}
        oInfo = get_crpp_sent_info(options)
        if oInfo != None and oInfo['status'] == "ok":
            # Make sure that 'object' sections are translated to proper JSON
            oSentInfo = oInfo['info']
            if 'code' in oSentInfo and 'ERROR' in oSentInfo['code']:
                # There is an error nevertheless
                context['sent_info'] = oSentInfo['code']
            else:
                # Get the sentence tree and extract any top-node features from it
                treeSent = oSentInfo['allT']
                context['eng'] = ""
                if treeSent != None and treeSent['f'] != None:
                    f = treeSent['f']
                    if 'eng' in f and f['eng'] != "":
                        # We have an 'eng' translation: make it available
                        context['eng'] = f['eng']
                # oSentInfo['allT'] = adapt_htable(treeSent)
                # Replace the 'allT' and 'hitT' with STRING json
                if 'allT' in oSentInfo: 
                    oSentInfo['allTs'] = json.dumps(oSentInfo['allT'])
                if 'hitT' in oSentInfo: oSentInfo['hitT'] = json.dumps(oSentInfo['hitT'])
                context['sent_info'] = oSentInfo
        else:
            context['sent_info'] = None

        self.context = context

        # Return what we have
        return context


class TextDetailInfo(View):
    """Make sure"""

    MainModel = Text
    template_name = 'browser/text_info.html'
    data = {'status': 'ok', 'html': '', 'statuscode': ''}       # Create data to be returned   
    oErr = ErrHandle()

    def post(self, request, pk=None):
        self.initializations(request, pk)
        if self.checkAuthentication(request):
            # Define the context
            sStatusCode = "none"
            context = dict(object_id = pk, savedate=None, statuscode=sStatusCode)
            # Do we have an object?
            if self.obj != None:
                # Put all required information in the data 
                context['fileName'] = self.obj.fileName
                context['format'] = self.obj.get_format_display()
                context['part'] = self.obj.part.name
                context['lines'] = self.obj.lines
                context['words'] = self.obj.words
                context['title'] = self.obj.title
                context['date'] = self.obj.date
                context['author'] = self.obj.author
                context['genre'] = self.obj.genre
                context['subtype'] = self.obj.subtype
            # Make sure we have a list of any errors
            error_list = [str(item) for item in self.arErr]
            self.data['error_list'] = error_list
            self.data['errors'] = self.arErr
            if len(self.arErr) >0:
                # Pass on the statuscode to the context for the template rendering
                context['status'] = "error"
                # Pass on the status to the calling function through [self.data]
                self.data['status'] = "error"
                self.data['statuscode'] = "error"
                context['statuscode'] = "error"
            else:
                # Pass on the statuscode
                self.data['statuscode'] = sStatusCode
                context['status'] = self.data['status']

            # Add items to context
            context['error_list'] = error_list
            
            # Get the HTML response
            sHtml = render_to_string(self.template_name, context, request)
            sHtml = treat_bom(sHtml)
            self.data['html'] = sHtml
           
        else:
            self.data['html'] = "Please log in before continuing"

        # Return the information
        return JsonResponse(self.data)

    def initializations(self, request, object_id):
        # Clear errors
        self.arErr = []
        self.data['status'] = "ok"
        self.data['html'] = ""
        self.data['statuscode'] = ""
        # COpy the request
        self.request = request
        # Copy any object id
        self.object_id = object_id
        # Get the instance of the Main Model object
        self.obj =  self.MainModel.objects.get(pk=object_id)
        # Get the parameters
        if request.POST:
            self.qd = request.POST
        else:
            self.qd = request.GET
        # Perform some custom initialisations
        self.custom_init()

    def custom_init(self):
        pass

    def checkAuthentication(self,request):
        # first check for authentication
        if not request.user.is_authenticated:
            # Simply redirect to the home page
            self.data['html'] = "Please log in to work on a research project"
            return False
        else:
            return True





class TextDetailView(DetailView):
    """Allow viewing and editing details of one text"""

    model = Text
    form_class = TextForm
    template_name = 'browser/text_view.html'
    last_url = ''

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return nlogin(request)
        return super(TextDetailView, self).get(request, *args, **kwargs)

    def post(self, request, pk):
        text = get_object_or_404(Text, pk=pk)
        bound_form = self.form_class(request.POST, instance=text)
        oUser = self.request.user
        if oUser.is_superuser:
          if bound_form.is_valid():
              new_text = bound_form.save()
              # Find out what to do next
              if '_save' in request.POST:
                  if 'last_url' in request.POST:
                      return redirect(request.POST['last_url'])
                  else:
                      return redirect('text_list')
              elif '_continue' in request.POST:
                  return redirect(new_text.get_absolute_url() + "?status=save_continue")
          else:
              context = {'form': bound_form,
                         'text': text,
                         'status': 'error'}
              return render( request, self.template_name, context)
        elif not request.user.is_authenticated:
            # Do not allow to get a good response
            return nlogin(request)
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
        if not self.request.user.is_authenticated:
            # Do not allow to get a good response
            return nlogin(self.request)
        elif 'Csv' in self.request.GET.get('submit_type', ''):
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

        # Longdale check
        longdale_user = user_is_ingroup(self.request, "longdale_user")
        # REtrieve the correct queryset, sorted on the correct levels
        if longdale_user:
            qs = [prt for prt in Part.objects.all().order_by('corpus__lng', 'corpus__name', 'name')]
        else:
            longdale = "Longdale"
            qs = [prt for prt in Part.objects.exclude(Q(name__istartswith=longdale)).order_by('corpus__lng', 'corpus__name', 'name')]
        # REtrieve the correct queryset, sorted on the correct levels
        # qs = [prt for prt in Part.objects.all().order_by('corpus__lng', 'corpus__name', 'name')]
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


