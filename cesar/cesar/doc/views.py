"""
Definition of views for the DOC app.
"""

import sys
from django import template
from django.db import models, transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from datetime import datetime

from cesar.settings import APP_PREFIX
from cesar.browser.models import Status
from cesar.browser.views import nlogin
from cesar.doc.models import FrogLink, FoliaDocs, Brysbaert
from cesar.doc.forms import UploadFilesForm, UploadOneFileForm
from cesar.utils import ErrHandle


# Create your views here.
def doc(request):
    """The main page of working with documents."""

    assert isinstance(request, HttpRequest)
    template = 'doc/doc_main.html'
    frmUpload = UploadFilesForm()
    frmBrysb = UploadOneFileForm()
    superuser = request.user.is_superuser
    context = {'title': 'Document processing',
               'frmUpload': frmUpload,
               'frmBrysb': frmBrysb,
               'superuser': superuser,
               'message': 'Radboud University CESAR',
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
                    data['html'] = "Please log in before continuing"


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


def import_docs(request):
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

    # Check if the user is authenticated and if it is POST
    if request.user.is_authenticated and request.method == 'POST':

        # Remove previous status object for this user
        Status.objects.filter(user=username).delete()
        # Create a status object
        oStatus = Status(user=username, type="docs", status="preparing", msg="please wait")
        oStatus.save()
        
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
                        sBare = arFile[0]

                        # Further processing depends on the extension
                        oResult = None
                        if extension == "doc" or extension == "docx" or extension == "xml":
                            # Cannot process these
                            oResult = {'status': 'error', 'msg': 'cannot process non-text files'}
                        else:
                            # Assume this is a text file
                            fl = FrogLink.create(name=sBare, username=username)
                            oResult = fl.read_doc(username, data_file, filename, clamuser, clampw, arErr, oStatus=oStatus)
                            # Possibly get the FD
                            if fd == None:
                                fd = fl.docs

                        # Determine a status code
                        if oResult == None or oResult['status'] == "error" :
                            statuscode = "error"
                            msg = "" if oResult == None or 'msg' not in oResult else oResult['msg']
                            oStatus.set("error", msg=msg)
                            # Break out of the for-loop
                            break
                        else:
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
            error_list = [str(item) for item in arErr]

            # Create the context
            context = dict(
                statuscode=statuscode,
                results=lResults,
                object=fd,
                error_list=error_list
                )

            if len(arErr) == 0:
                # Get the HTML response
                data['html'] = render_to_string(template_name, context, request)
            else:
                data['html'] = "Please log in before continuing"


        else:
            data['html'] = 'invalid form: {}'.format(form.errors)
            data['status'] = "error"
    else:
        data['html'] = 'Only use POST and make sure you are logged in'
        data['status'] = "error"
 
    # Return the information
    return JsonResponse(data)

class FoliaDocsDetailView(DetailView):
    model = FoliaDocs
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
        context = super(FoliaDocsDetailView, self).get_context_data(**kwargs)

        # Get parameters for the search (if it is GET)
        initial = self.request.GET

        status = ""
        if 'status' in initial:
            status = initial['status']
        context['status'] = status

        # Return what we have
        return context
