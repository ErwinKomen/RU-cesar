"""
Definition of views for the BRIEF app.
"""

from django import template
from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.db import models, transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from datetime import datetime
import sys
import json
import re
import os.path, io, shutil
import tarfile

from cesar.settings import APP_PREFIX, WRITABLE_DIR
from cesar.basic.views import BasicList, BasicDetails, BasicPart
from cesar.browser.views import nlogin
from cesar.seeker.views import csv_to_excel
from cesar.brief.models import AnswerEntry, AnswerQuestion, BriefEntry, BriefModule, BriefQuestion, BriefSection, Project, qids
from cesar.brief.forms import ProjectForm
from cesar.utils import ErrHandle

# Global debugging 
bDebug = False

def get_application_name():
    """Try to get the name of this application"""

    # Walk through all the installed apps
    for app in apps.get_app_configs():
        # Check if this is a site-package
        if "site-package" not in app.path:
            # Get the name of this app
            name = app.name
            # Take the first part before the dot
            project_name = name.split(".")[0]
            return project_name
    return "unknown"
# Provide application-specific information
PROJECT_NAME = get_application_name()
app_uploader = "{}_uploader".format(PROJECT_NAME.lower())
app_editor = "{}_editor".format(PROJECT_NAME.lower())
app_userplus = "{}_userplus".format(PROJECT_NAME.lower())
app_moderator = "{}_moderator".format(PROJECT_NAME.lower())


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

def user_is_superuser(request):
    bFound = False
    # Is this user part of the indicated group?
    username = request.user.username
    if username != "":
        user = User.objects.filter(username=username).first()
        if user != None:
            bFound = user.is_superuser
    return bFound

# Views belonging to the Cesar Brief Processing app.

def home(request):
    """Renders the home page."""

    assert isinstance(request, HttpRequest)
    # Specify the template
    template_name = 'brief/index.html'
    # Define the initial context
    context =  {'title':'ProjectBrief','year':datetime.now().year,
                'pfx': APP_PREFIX,'site_url': admin.site.site_url}

    # Statistics
    context['pcount'] = Project.objects.count()
    context['acount'] = AnswerQuestion.objects.count()

    # Make sure we add special group permission(s)
    context['is_app_editor'] = user_is_ingroup(request, app_editor)
    context['is_superuser'] = user_is_superuser(request)
    # Render and return the page
    return render(request, template_name, context)

def about(request):
    """Renders the about page."""

    # Specify the template
    template_name = 'brief/about.html'
    assert isinstance(request, HttpRequest)
    context =  {'title':'About',
                'message':'Radboud University passim utility.',
                'year':datetime.now().year,
                'pfx': APP_PREFIX,
                'site_url': admin.site.site_url}
    context['is_app_editor'] = user_is_ingroup(request, app_editor)
    context['is_superuser'] = user_is_superuser(request)

    # Process this visit
    context['breadcrumbs'] = get_breadcrumbs(request, "About", True)

    return render(request,template_name, context)

def brief_load(request):
    """Load the project brief definition and adapt what is there"""

    oErr = ErrHandle()
    response = reverse('brief_home')
    brief_name = "pbrief_structure.json"
    brief_lst = []
    
    try:
        if not user_is_superuser(request):
            return response
        # Figure out where the JSON is situated
        brief_file = os.path.abspath(os.path.join(WRITABLE_DIR, brief_name))

        # Now read the brief as a json document
        with io.open(brief_file, "r", encoding="utf-8") as fp:
            brief_lst = json.load(fp)

        # 1 - Initialisations
        #modules = dict()

        # 2 - make keys lower case
        brief = []
        for item in brief_lst:
            oNew = {}
            for k,v in item.items():
                oNew[k.lower()] = v
            brief.append(oNew)

        # 3 - read brief elements
        for item in brief:
            # Get information from the item
            type = item.get("type")
            mod = item.get("module", "")
            sec = item.get("section", "")
            qid = item.get("questionid", "")
            rtype = item.get("response", "")
            help = item.get("help", "")
            contents = item.get("contents", "")
            entry = item.get("entry", "")
            entries = []
            if entry != "": entries = entry

            # 3.a is this a heading?
            if type == "heading":
                # Heading for section or module?
                if mod != "" and sec == "":
                    # Module item
                    name = contents.strip()
                    short = item['label'].strip()
                    order = mod + 1
                    # Create or update the module
                    module = BriefModule.update(name, short, order)
                elif mod != "" and sec != "":
                    # section within a module
                    mod += 1
                    #module = modules[mod]
                    name = contents.strip()
                    order = sec
                    # Create or update the module
                    section = BriefSection.update(name, order, module)

            elif type == "paragraph":
                # Get the right object
                obj = None
                if mod != "" and sec == "":
                    obj = BriefModule.objects.filter(order = mod+1).first()
                elif mod != "" and sec != "":
                    obj = BriefSection.objects.filter(order=sec, module__order=mod+1).first()
                if obj == None:
                    # Create a section without name
                    obj = BriefSection.objects.create(name="-", order=sec, module=module)
                # Add the paragraph to what is already there as intro
                intro = obj.intro
                if intro == None or intro == "":
                    intro = contents
                else:
                    intro = "{}\n{}".format(intro, contents)
                obj.intro = intro
                obj.save()

            elif type == "question" and sec != "":
                # Get the current section
                section = BriefSection.objects.filter(order=sec, module__order=mod+1).first()
                if section == None:
                    # Create a section without name
                    section = BriefSection.objects.create(name="-", order=sec, module=module)
                order = qids[qid]
                rtype = rtype[0:5]
                # Get or create this question
                obj = BriefQuestion.update(section, order, contents, help, rtype, entries)

    except:
        msg = oErr.get_error_message()
        oErr.DoError("brief_load")
    return response


class ProjectEdit(BasicDetails):
    """Details view for one batch"""

    model = Project
    mForm = ProjectForm
    prefix = "prj"
    rtype = "json"
    mainitems = []
    extend_template = "brief/layout.html"

    def add_to_context(self, context, instance):
        """Add to the existing context"""

        # Define the main items to show and edit
        context['mainitems'] = [
            {'type': 'plain', 'label': "Name:",         'value': instance.name,                 'field_key': 'name'},
            {'type': 'plain', 'label': "Description:",  'value': instance.description,          'field_key': 'description'},
            {'type': 'plain', 'label': "Status:",       'value': instance.get_status_display(), 'field_key': 'status'},
            {'type': 'plain', 'label': "Progress:",     'value': instance.get_ptype_display(),  'field_key': 'ptype'},
            {'type': 'plain', 'label': "Created:",      'value': instance.get_created()  },
            {'type': 'plain', 'label': "Saved:",        'value': instance.get_saved()}
            ]
        # Return the context we have made
        return context


class ProjectDetails(ProjectEdit):
    """Show the details of a [Project]"""
    rtype = "html"


class ProjectListView(BasicList):
    """Paginated view of project instances"""

    model = Project
    extend_template = "brief/layout.html"
    order_cols = ['name', 'description']
    order_heads = [{'name': 'Name', 'order': 'o=1', 'type': 'str', 'field': 'name', 'main': True, 'linkdetails': True},
                   {'name': 'Description', 'order': 'o=2', 'type': 'str', 'field': 'description'},
                   {'name': 'Actions', 'order': '', 'type': 'str', 'custom': 'actions'}]

    def initializations(self):
        qs = BriefQuestion.objects.filter(ntype="")
        with transaction.atomic():
            for obj in qs:
                obj.ntype = "opt"
                obj.save()
        return None

    def get_field_value(self, instance, custom):
        sBack = ""
        sTitle = ""
        html = []

        # Figure out what to show
        if custom == "actions":
            # The buttons for the actions that can be taken
            url = reverse("brief_master", kwargs={'pk': instance.id})
            html.append('<a href="{}" title="Project brief"><span class="glyphicon glyphicon-download"><span></a>'.format(url))
            # COmbineer
            sBack = "\n".join(html)

        # Retourneer wat kan
        return sBack, sTitle


class BriefMaster(ProjectDetails):
    """Show the project brief modules and allow filling in the questions"""

    template_name = "brief/pb_master.html"
    form_objects = []   # [{'form': SeekerResGroupForm, 'prefix': 'resgroup', 'readonly': False}]

    def add_to_context(self, context, instance):

        # Look at the object_id
        context['object_id'] = "{}".format(instance.id)
        context['pname'] = instance.name
        context['modules'] = BriefModule.objects.all().order_by("order")

        # Return the context we have adapted
        return context
