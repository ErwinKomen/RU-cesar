"""
Definition of views for the TRANS app.
"""

import sys
import json
import re
import io
import markdown

from django import template
from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.db import models, transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpRequest, StreamingHttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from datetime import datetime

from docx import Document
from htmldocx import HtmlToDocx

from cesar.settings import APP_PREFIX, WRITABLE_DIR, STATIC_ROOT
from cesar.basic.views import BasicList, BasicDetails, BasicPart
from cesar.trans.translit import TranslitChe
from cesar.trans.forms import TransForm
from cesar.utils import ErrHandle

app_user = "trans_user"
bDebug = False

def user_is_authenticated(request):
    # Is this user authenticated?
    username = request.user.username
    user = User.objects.filter(username=username).first()
    response = False if user == None else user.is_authenticated()
    return response

def user_is_ingroup(request, sGroup):
    # Is this user part of the indicated group?
    username = request.user.username
    user = User.objects.filter(username=username).first()

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

def user_is_superuser(request):
    bFound = False
    # Is this user part of the indicated group?
    username = request.user.username
    if username != "":
        user = User.objects.filter(username=username).first()
        if user != None:
            bFound = user.is_superuser
    return bFound


def home(request):
    """Show the homepage of the converter"""

    assert isinstance(request, HttpRequest)
    # Specify the template
    template_name = 'trans/index.html'

    # Define the initial context
    context =  {'title':'Transliterate','year':datetime.now().year,
                'intro_breadcrumb': 'Transliteration',
                'is_app_user': user_is_ingroup(request, app_user),
                'pfx': APP_PREFIX,'site_url': admin.site.site_url}

    # Make sure we add special group permission(s)
    context['is_in_tsg'] = user_is_ingroup(request, "radboud-tsg")
    context['is_superuser'] = user_is_superuser(request)
    context['transForm'] = TransForm()

    # Render and return the page
    return render(request, template_name, context)

def convert(request):

    oErr = ErrHandle()
    data = {'status': 'ok'}
    re_latin = re.compile( r'(\@[a-zA-Z\-\#\'\.\,\s]+)')
    oTranslit = TranslitChe()
    options = dict(vowel="macron", 
                   switches="ipa",
                   target="Phonemic",
                   target_cyrillic="Vernacular")

    if request.method.lower() == "post":
        qd = request.POST
        original = qd.get("original")
        if original != None and original != "":
            # Transform using markdown
            md = markdown.markdown(original, extensions=['tables'])


            # Figure out and transliterate
            lCombi = []
            previous = ""
            for item in re_latin.split(md):
                if len(item) > 0:
                    if item[0:2] == "@#":
                        # Make a phonemic transliteration
                        sResult = oTranslit.do_lat2phm(previous.replace("d'", "d"), options)
                        lCombi.append("<br /><span class='{}'>{}</span>".format(options['target'], sResult))
                    elif item[0] == "@":
                        # Keep this for the next time
                        previous = item[1:].replace("d.", "d'")
                        # Make cyrillic transliteration
                        sResult = oTranslit.do_lat2cyr(previous, options)
                        lCombi.append("<span class='{}'>{}</span>".format(options['target_cyrillic'], sResult))
                    else:
                        # No transliteration
                        lCombi.append(item)

            # Recombine the result
            transliteration = "".join(lCombi)
            # Adapt any table elements if needed
            transliteration = transliteration.replace("<table>", "<table style='width: 100%;'>")
            transliteration = transliteration.replace("<td>", "<td valign='top'>")

            # Return the result
            data['msg'] = transliteration
    else:
        data['status'] = 'error'
        data['msg'] = 'Use POST'

    # Return this response
    return JsonResponse(data)

def download(request):
    """Download a transliteration as document"""

    # Get the download type
    qd = request.POST
    if 'downloadtype' in qd and 'transliteration' in qd:
        # Get the download type and the data itself
        dtype = qd['downloadtype']
        transliteration = qd['transliteration']

        if dtype == "docx":
            dext = ".docx"
            sContentType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            # Transform HTML to DOC
            document = Document()
            new_parser = HtmlToDocx()
            new_parser.add_html_to_document(transliteration, document)

            buffer = io.BytesIO()   # Start memory stream
            document.save(buffer)   # Save to memory stream
            buffer.seek(0)          # Rewind the stream

        # Determine a file name
        sBase = self.object.name
        sFileName = "trans_{}{}".format(sBase, dext)

        if dtype == "docx":
            response = StreamingHttpResponse(streaming_content=buffer, content_type=sContentType)
            response['Content-Encoding'] = 'UTF-8'
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(sFileName)    
        else:
            response = HttpResponse(ddata, content_type=sContentType)
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(sFileName)    
    else:
        # Return something else
        response = None

    # Return the response we have
    return response
