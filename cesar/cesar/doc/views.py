"""
Definition of views for the DOC app.
"""

import sys
import json
import re
from django import template
from django.apps import apps
from django.contrib.auth.models import User, Group
from django.db import models, transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from datetime import datetime
import os.path, io, shutil
import tarfile

from cesar.settings import APP_PREFIX
from cesar.basic.views import BasicList, BasicDetails, BasicPart
from cesar.browser.models import Status
from cesar.browser.views import nlogin
from cesar.seeker.views import csv_to_excel
from cesar.doc.models import FrogLink, FoliaDocs, Brysbaert, NexisDocs, NexisLink, NexisBatch, NexisProcessor
from cesar.doc.forms import UploadFilesForm, UploadNexisForm, UploadOneFileForm, NexisBatchForm
from cesar.utils import ErrHandle

# Global debugging 
bDebug = False


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

# Views belonging to the Cesar Document Processing app.

# ========== CONCRETENESS ==============================

def concrete_main(request):
    """The main page of working with documents."""

    assert isinstance(request, HttpRequest)
    template = 'doc/concrete_main.html'
    frmUpload = UploadFilesForm()
    frmBrysb = UploadOneFileForm()
    superuser = request.user.is_superuser
    # Get a list of already uploaded files too
    text_list = []
    for item in FrogLink.objects.filter(Q(fdocs__owner__username=request.user)):
        if item.concr == None or item.concr == "":
            text_list.append(None)
        else:
            obj = json.loads(item.concr)
            obj['id'] = item.id
            # obj['download'] = reverse('concrete_download', kwargs={'pk': item.id})
            text_list.append(obj)
    context = {'title': 'Document processing',
               'frmUpload': frmUpload,
               'frmBrysb': frmBrysb,
               'superuser': superuser,
               'message': 'Radboud University CESAR',
               'textlist': text_list,
               'intro_breadcrumb': 'Concreteness',
               'year': datetime.now().year}
    return render(request, template, context)


def import_brysbaert(request):
    """Ad-hoc procedure to allow importing Brysbaert tab-separated file into Model"""

    # Initialisations
    # NOTE: do ***not*** add a breakpoint until *AFTER* form.is_valid
    arErr = []
    error_list = []
    transactions = []
    data = {'status': 'ok', 'html': ''}
    template_name = 'doc/import_brys.html'
    obj = None
    data_file = ""
    bClean = False
    username = request.user.username
    statuscode = ""
    oErr = ErrHandle()

    try:
        # Check if the user is authenticated and if it is POST
        if request.user.is_authenticated and request.method == 'POST':

            # Remove previous status object for this user
            Status.objects.filter(user=username).delete()
            # Create a status object
            oStatus = Status(user=username, type="brysb", status="preparing", msg="please wait")
            oStatus.save()
        
            form = UploadOneFileForm(request.POST, request.FILES)
            lResults = []
            if form.is_valid():
                # NOTE: from here a breakpoint may be inserted!
                print('import_brysb: valid form')

                # Get the contents of the imported file
                file = request.FILES['file_field']

                # Clear whatever there was in Brysbaert
                Brysbaert.clear()

                # Read the file into a structure
                lLines = []
                bFirst = True
                for line in file:
                    if bFirst:
                        bFirst = False
                    else:
                        sLine = line.decode("utf-8-sig").strip()
                        if sLine != "":
                            lLines.append(sLine.split("\t"))
                # Create an iterator for this list
                lIter = iter(lLines)

                # Now we have it all, so indicate that
                oStatus.set("phase 2", msg="chunk-adding information")

                # Iterate over the contents in chunks
                iChunk = 0
                iChunkSize = 100
                iChunkLen = len(lLines) // iChunkSize + 1
                iNum = 0

                iCount = 0
                iPass = 0
                # Iterate over the chunks
                arPart = next(lIter)
                for chunk_this in range(iChunkLen):
                    iChunk += 1
                    # Show where we are
                    oStatus.set("chunking", msg="processing chunk {} of {}".format(iChunk, iChunkLen))
                    print("working Brysbaert #{}".format(iCount), file=sys.stderr)
                    # Treat the items from 
                    with transaction.atomic():
                        for idx in range(iChunkSize):
                            # Check if there is some meat
                            if arPart != None:
                                # Double check length
                                if len(arPart) == 7:
                                    try:
                                        # get the different parts
                                        stimulus = arPart[0]
                                        listnum = arPart[1]
                                        m = float( arPart[2].replace(",", "."))
                                        sd = float(arPart[3].replace(",", "."))
                                        ratings = float(arPart[4].replace(",", "."))
                                        responses = float(arPart[5].replace(",", "."))
                                        subjects = float(arPart[6].replace(",", "."))

                                        # Just add in one go
                                        obj = Brysbaert(stimulus=stimulus, list=listnum, m=m, sd=sd, ratings=ratings, responses=responses, subjects=subjects)
                                        obj.save()

                                        # Keep track of where we are
                                        iCount += 1
                                    except:
                                        iPass += 1
                                # Get to the next text
                                try:
                                    arPart = next(lIter)
                                except StopIteration as e:
                                    break

                if statuscode == "error":
                    data['status'] = "error"
                    print("error import_brysbaert #1", file=sys.stderr)
                else:
                    oStatus.set("ready", msg="Read all of Brysbaert: {}, skipped {}".format(iCount, iPass))
                # Get a list of errors
                error_list = [str(item) for item in arErr]

                # Create the context
                context = dict(
                    statuscode=statuscode,
                    result_count=iCount,
                    result_skip =iPass,
                    error_list=error_list
                    )

                if len(arErr) == 0:
                    # Get the HTML response
                    data['html'] = render_to_string(template_name, context, request)
                else:
                    data['html'] = "There are errors in importing Brysbaert"


            else:
                data['html'] = 'invalid form: {}'.format(form.errors)
                data['status'] = "error"
        else:
            data['html'] = 'Only use POST and make sure you are logged in'
            data['status'] = "error"
    except:
        msg = oErr.get_error_message()
        data['status'] = "error"
        data['html'] = "Import Brysbaert error: {}".format(msg)
 
    # Return the information
    return JsonResponse(data)

def import_concrete(request):
    """Import one or more TEXT (utf8) files that need to be transformed into FoLiA with FROG"""

    # Initialisations
    # NOTE: do ***not*** add a breakpoint until *AFTER* form.is_valid
    arErr = []
    error_list = []
    transactions = []
    data = {'status': 'ok', 'html': ''}
    template_name = 'doc/import_docs.html'
    obj = None
    data_file = ""
    bClean = False
    username = request.user.username
    oErr = ErrHandle()
    re_number = re.compile( r"^\d[.,\d]*$")

    # Check if the user is authenticated and if it is POST
    if request.user.is_authenticated and request.method == 'POST':

        # Remove previous status object for this user
        Status.objects.filter(user=username).delete()
        # Create a status object
        oStatus = Status(user=username, type="docs", status="preparing", msg="please wait")
        oStatus.save()

        # Other initialisations
        concretes = []
        
        form = UploadFilesForm(request.POST, request.FILES)
        lResults = []
        if form.is_valid():
            # NOTE: from here a breakpoint may be inserted!
            print('import_docs: valid form')

            # Get user name and password
            clamuser = request.POST.get("clamuser")
            clampw = request.POST.get("clampw")

            # Initialisations
            fd = None   # FoliaDocs

            # Get the contents of the imported file
            files = request.FILES.getlist('files_field')
            if files != None:
                for data_file in files:
                    filename = data_file.name

                    # Set the status
                    oStatus.set("reading", msg="file={}".format(filename))

                    # Get the source file
                    if data_file == None or data_file == "":
                        arErr.append("No source file specified for the selected project")
                    else:
                        # Check the extension
                        arFile = filename.split(".")
                        extension = arFile[len(arFile)-1]
                        sBare = arFile[0].strip().replace(" ", "_")

                        # Check the bare file name
                        if re_number.match(sBare):
                            # Invalid filename
                            statuscode = "error"
                            msg = "Please change the filename. It should start with a character."
                            arErr.append(msg)
                            oResult = {'status': 'error', 'msg': msg}
                        else:

                            # Further processing depends on the extension
                            oResult = None
                            if extension == "doc" or extension == "docx" or extension == "xml":
                                # Cannot process these
                                oResult = {'status': 'error', 'msg': 'cannot process non-text files'}
                            else:
                                # Assume this is a text file: create a froglink
                                fl, msg = FrogLink.create(name=sBare, username=username)
                                if fl == None:
                                    # Some error occurred
                                    statuscode = "error"
                                    oStatus.set("error", msg=msg)
                                    # Break out of the for-loop
                                    break
                                # Read and convert into folia.xml
                                oResult = fl.read_doc(username, data_file, filename, clamuser, clampw, arErr, oStatus=oStatus)
                                # Possibly get the link to the owner's FoliaDocs
                                if fd == None:
                                    # Get the foliadocs link
                                    fd = fl.fdocs

                            # Determine a status code
                            if oResult == None or oResult['status'] == "error" :
                                statuscode = "error"
                                msg = "" if oResult == None or 'msg' not in oResult else oResult['msg']
                                oStatus.set("error", msg=msg)
                                # Break out of the for-loop
                                break
                            else:
                                # Indicate that the folia.xml has been created
                                oStatus.set("working", msg="Created folia.xml file")
                                oErr.Status("Created folia.xml file")
                                # Next step: determine concreteness for this file
                                bResult, msg = fl.do_concreteness()
                                if bResult == False:
                                    arErr.append(msg)
                                    oStatus.set("error", msg=msg)
                                    statuscode = "error"
                                else:
                                    # Make sure we return the concreteness
                                    concretes.append(json.loads(fl.concr))
                                    # Show where we are
                                    statuscode = "completed"
                        if oResult == None:
                            arErr.append("There was an error. No manuscripts have been added")
                        else:
                            lResults.append(oResult)
            if statuscode == "error":
                data['status'] = "error"
            else:
                oStatus.set("ready", msg="Read all files")
            # Get a list of errors
            error_list = [str(item) for item in arErr if len(str(item)) > 0]

            # Create the context
            context = dict(
                statuscode=statuscode,
                results=lResults,
                object=fd,
                concretes=concretes,
                error_list=error_list
                )

            if len(arErr) == 0 or len(arErr[0]) == 0:
                # Get the HTML response
                data['html'] = render_to_string(template_name, context, request)
            else:
                lHtml = []
                lHtml.append("There are errors in importing this doc")
                for item in arErr:
                    lHtml.append("<br />- {}".format(str(item)))
                data['html'] = "\n".join(lHtml)


        else:
            data['html'] = 'invalid form: {}'.format(form.errors)
            data['status'] = "error"
    else:
        data['html'] = 'Only use POST and make sure you are logged in'
        data['status'] = "error"
 
    # Return the information
    return JsonResponse(data)

class FoliaDocumentDetailView(DetailView):
    model = FrogLink
    template_name = 'doc/foliadocs_view.html'

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
            if 'downloadtype' in self.qd:
                # Get the download type and the data itself
                dtype = self.qd['downloadtype']
            
                if dtype == "json":
                    dext = ".json"
                    sContentType = "application/json"
                    # Get the ddata
                    ddata = json.dumps(json.loads( self.object.concr), indent=2)
                elif dtype == "tsv":
                    dext = ".tsv"
                    sContentType = "text/tab-separated-values"
                    # Get the data as a CSV string
                    ddata = self.object.get_csv()
                elif dtype == "excel":
                    dext = ".xlsx"
                    sContentType = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    # Get the data as a CSV string
                    ddata = self.object.get_csv()

                # Determine a file name
                sBase = self.object.name
                sFileName = "{}_concreet{}".format(sBase, dext)

                # Excel needs additional conversion
                if dtype == "xlsx" or dtype == "excel":
                    # Convert 'compressed_content' to an Excel worksheet
                    response = HttpResponse(content_type=sContentType)
                    response['Content-Disposition'] = 'attachment; filename="{}"'.format(sFileName)    
                    response = csv_to_excel(ddata, response, delimiter="\t")
                else:
                    response = HttpResponse(ddata, content_type=sContentType)
                    response['Content-Disposition'] = 'attachment; filename="{}"'.format(sFileName)    

            else:
                response = self.render_to_response(context)
        # Return the response we have
        return response

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(FoliaDocumentDetailView, self).get_context_data(**kwargs)

        # Get parameters for the search (if it is GET)
        initial = self.request.GET

        status = ""
        if 'status' in initial:
            status = initial['status']
        context['status'] = status

        # Return what we have
        return context


# ================ NEXIS UNI ===========================
def nexis_main(request):
    """The main page of working with Nexis Uni documents."""

    # Initializations
    template = 'doc/nexis_main.html'
    frmUpload = UploadNexisForm()

    # Make sure this is just a HTTP request
    assert isinstance(request, HttpRequest)

    # Other initializations
    superuser = request.user.is_superuser
    username = request.user.username

    # Get a list of processed batches
    nd = NexisDocs.get_obj(username)
    batch_list = []
    if nd != None:
        batch_list = nd.ndocsbatches.all().order_by("-created")



    # Create the context
    context = {'title': 'Document processing',
               'frmUpload': frmUpload,
               'superuser': superuser,
               'message': 'Radboud University CESAR',
               'batchlist': batch_list,
               'intro_breadcrumb': 'Nexis Uni',
               'year': datetime.now().year}
    
    # Render the template as HTML
    return render(request, template, context)

def import_nexis(request):
    """Import one or more TEXT (utf8) files that need to be transformed into FoLiA with FROG"""

    # Initialisations
    # NOTE: do ***not*** add a breakpoint until *AFTER* form.is_valid
    arErr = []
    error_list = []
    transactions = []
    data = {'status': 'ok', 'html': ''}
    template_name = 'doc/import_nexis.html'
    obj = None
    data_file = ""
    bClean = False
    statuscode = ""
    username = request.user.username
    oErr = ErrHandle()
    re_number = re.compile( r"^\d[.,\d]*$")

    # Check if the user is authenticated and if it is POST
    if request.user.is_authenticated and request.method == 'POST':

        # Remove previous status object for this user
        Status.objects.filter(user=username).delete()
        # Create a status object
        oStatus = Status(user=username, type="docs", status="preparing", msg="please wait")
        oStatus.save()

        # Other initialisations
        lmeta = []
        
        form = UploadNexisForm(request.POST, request.FILES)
        lResults = []
        if form.is_valid():
            # NOTE: from here a breakpoint may be inserted!
            print('import_nexis: valid form')

            # Initialisations
            nd = None   # NexisDocs

            # Get the contents of the imported file
            files = request.FILES.getlist('files_field')
            if files != None:
                # Create a NexisBatch
                batch, msg = NexisBatch.create(username=username)
                for data_file in files:
                    filename = data_file.name

                    # Set the status
                    oStatus.set("reading", msg="file={}".format(filename))

                    # Get the source file
                    if data_file == None or data_file == "":
                        arErr.append("No source file specified for the selected project")
                    else:
                        # Check the extension
                        arFile = filename.split(".")
                        extension = arFile[len(arFile)-1]
                        sBare = arFile[0].strip().replace(" ", "_")

                        # Check the bare file name
                        if re_number.match(sBare):
                            # Invalid filename
                            statuscode = "error"
                            msg = "Please change the filename. It should start with a character."
                            arErr.append(msg)
                            oResult = {'status': 'error', 'msg': msg}
                        else:

                            # Further processing depends on the extension
                            oResult = None
                            if extension == "doc" or extension == "docx" or extension == "xml":
                                # Cannot process these
                                oResult = {'status': 'error', 'msg': 'cannot process non-text files'}
                            else:
                                # Assume this is a text file: create a froglink
                                fl, msg = NexisLink.create(name=sBare, username=username, batch=batch)
                                if fl == None:
                                    # Some error occurred
                                    statuscode = "error"
                                    oStatus.set("error", msg=msg)
                                    # Break out of the for-loop
                                    break
                                # Read and convert into folia.xml
                                oResult = fl.read_doc(username, data_file, filename, arErr, oStatus=oStatus)
                                # Possibly get the link to the owner's NexisDocs
                                if nd == None:
                                    # Get the foliadocs link
                                    nd = fl.ndocs
                                # Add the meta data
                                oResult['metadata'] = json.loads(fl.nmeta)
                                oResult['name'] = fl.name

                                # Show where we are
                                statuscode = "completed"

                        if oResult == None:
                            arErr.append("There was an error. No manuscripts have been added")
                        else:
                            lResults.append(oResult)
            if statuscode == "error":
                data['status'] = "error"
            else:
                # Set the number of files in this batch
                iCount = batch.batchlinks.all().count()
                batch.count = iCount
                batch.save()
                # Show we are ready
                oStatus.set("ready", msg="Read all files")
            # Get a list of errors
            error_list = [str(item) for item in arErr if len(str(item)) > 0]

            # Create the context
            context = dict(
                statuscode=statuscode,
                results=lResults,
                object=nd,
                error_list=error_list
                )

            if len(arErr) == 0 or len(arErr[0]) == 0:
                # Get the HTML response
                data['html'] = render_to_string(template_name, context, request)
            else:
                lHtml = []
                lHtml.append("There are errors in importing this doc")
                for item in arErr:
                    lHtml.append("<br />- {}".format(str(item)))
                data['html'] = "\n".join(lHtml)


        else:
            data['html'] = 'invalid form: {}'.format(form.errors)
            data['status'] = "error"
    else:
        data['html'] = 'Only use POST and make sure you are logged in'
        data['status'] = "error"
 
    # Return the information
    return JsonResponse(data)


class NexisBatchEdit(BasicDetails):
    """Details view for one batch"""

    model = NexisBatch
    mForm = NexisBatchForm
    prefix = "nbatch"
    title = "BatchEdit"
    rtype = "json"
    mainitems = []

    def add_to_context(self, context, instance):
        """Add to the existing context"""

        # Define the main items to show and edit
        context['mainitems'] = [
            {'type': 'plain', 'label': "Date:",             'value': instance.created,  'field_key': 'created'},
            {'type': 'plain', 'label': "Number of texts:",  'value': instance.count,    'field_key': 'count'}
            ]
        context['is_app_editor'] = user_is_ingroup(self.request, "nexis_editor")
        context['is_app_uploader'] = context['is_app_editor']
        # Return the context we have made
        return context


class NexisBatchDetails(NexisBatchEdit):
    rtype = "html"


class NexisBatchDownload(BasicPart):
    MainModel = NexisBatch
    templat_name = "seeker/download_status.html"
    dtype = "tar.gz"
    action = "download"

    def get_data(self, prefix, dtype):
        gzdata = None
        oErr = ErrHandle()
        try:
            # Who am I?
            username = self.request.user.username
            nexisProc = NexisProcessor(username)
            # What is the directory to use?
            dir = nexisProc.dir
            # Get the NexisBatch object
            batch = self.obj
            if batch != None:
                # Determine file name
                srcdir = os.path.join(dir, "nexisbatch_{}".format(batch.id))
                # Create dir if not existing
                os.mkdir(srcdir)
                # Get all the link objects as files in [srcdir]
                qs = batch.batchlinks.all()
                for obj in qs:
                    # Figure out where to put them
                    sbare = os.path.join(srcdir,"nexislink_{}".format(str(obj.id).zfill(6)))
                    fmeta = "{}.meta".format(sbare)
                    ftext = "{}.txt".format(sbare)
                    # Write the contents of metadata
                    oMeta = json.loads(obj.nmeta)
                    with open(fmeta, "w") as fp:
                        json.dump(oMeta, fp, indent=2)
                    # Write the text as UTF8
                    with io.open(ftext, 'w', encoding='utf8') as fp:
                        fp.write(obj.nbody)

                # Copy from [srcdir] into tar.gz
                ofname = "{}.tar.gz".format(srcdir)
                with tarfile.open(ofname, "w:gz") as tar:
                    tar.add(srcdir, arcname=os.path.basename(srcdir))

                # Now remove the source directory
                shutil.rmtree(srcdir)

                # Now read the file as binary data
                with io.open(ofname, "rb") as fp:
                    gzdata = fp.read()
        except:
            msg = oErr.get_error_message()

        # Return the data
        return gzdata


class NexisListView(BasicList):
    """Search and list nexis batches"""

    model = NexisBatch
    listform = NexisBatchForm
    prefix = "nbatch"
    new_button = False      # Don't show a new button, because new items can only be added by downloading
    plural_name = "Batches of Nexis text files"
    sg_name = "Nexis Batch"
    has_select2 = False     # Don't use Select2 here
    delete_line = True      # Allow deleting a line
    order_cols = ['created', 'count', '']
    order_default = ['-created', 'count']
    order_heads = [{'name': 'Date',  'order': 'o=1', 'type': 'str', 'custom': 'created', 'linkdetails': True},
                   {'name': 'Texts', 'order': 'o=2', 'type': 'int', 'field':  'count', 'linkdetails': True, 'main': True},
                   {'name': '',      'order': '',    'type': 'str', 'custom': 'links', 'align': 'right'}]
    filters = [
        {'name': 'Date', 'id': 'filer_created', 'enabled': False}
        ]
    searches = [
        {'section': '', 'filterlist': [
            {'filter': 'created',   'dbfield':  'created',  'keyS': 'created'}
            ]},
        {'section': 'other', 'filterlist': [
            {'filter': 'ndocs',     'fkfield': 'ndocs',  'keyFk': 'ndocs'}]}
        ]
    uploads = [{"title": "nbatch", "label": "Batch", "url": "import_nexis", "msg": "Upload Nexis text files", "type": "multiple"}]

    def get_field_value(self, instance, custom):
        sBack = ""
        sTitle = ""
        html = []

        # Figure out what to show
        if custom == "created":
            sBack = instance.created.strftime("%d/%B/%Y (%H:%M)")
        elif custom == "links":
            # Show the download links
            url = reverse('nexisbatch_download', kwargs={'pk': instance.id})
            html.append('<a href="#" title="Download compressed tar.gz" downloadtype="tar.gz" ajaxurl="{}" onclick="ru.basic.post_download(this);">'.format(url))
            html.append('<span class="glyphicon glyphicon-download"><span></a>')
            
            # COmbineer
            sBack = "\n".join(html)

        # Retourneer wat kan
        return sBack, sTitle

    def adapt_search(self, fields):
        # Initialisations
        lstExclude=None
        qAlternative = None
        # Make sure only batches are shown for which this user is the owner
        username = self.request.user.username
        ndocs = NexisDocs.objects.filter(owner=username).first()
        if ndocs != None:
            fields['ndocs'] = ndocs

        # Return standard
        return fields, lstExclude, qAlternative

    def add_to_context(self, context, initial):
        context['is_app_editor'] = user_is_ingroup(self.request, "nexis_editor")
        context['is_app_uploader'] = context['is_app_editor']
        return context

