"""
Definition of views for the BRIEF app.
"""

from django import template
from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.db import models, transaction
from django.db.models import Q
from django.forms import formset_factory, modelformset_factory, inlineformset_factory, ValidationError
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
from cesar.brief.forms import ProjectForm, QuestionsForm, AnswerEntryForm
from cesar.utils import ErrHandle

# Global debugging 
bDebug = False

# Provide application-specific information
PROJECT_NAME = "brief"
app_user = "{}_user".format(PROJECT_NAME.lower())
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
def add_app_access(request, context):
    # Make sure we add special group permission(s)
    context['is_app_user'] = user_is_ingroup(request, app_user)
    context['is_app_editor'] = user_is_ingroup(request, app_editor)
    context['is_app_uploader'] = user_is_ingroup(request, app_uploader)
    context['is_app_userplus'] = user_is_ingroup(request, app_userplus)
    context['is_app_moderator'] = user_is_ingroup(request, app_moderator)
    context['is_superuser'] = user_is_superuser(request)

    return True

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
    add_app_access(request, context)

    # Render and return the page
    return render(request, template_name, context)

def about(request):
    """Renders the about page."""

    # Specify the template
    template_name = 'brief/about.html'
    assert isinstance(request, HttpRequest)
    breadcrumbs = [{'name': 'Home', 'url': reverse('brief_home')},
                   {'name': 'About this application'}]
    context =  {'title':'About',
                'message':'SIL-Bolshoi project brief utility.',
                'year':datetime.now().year,
                'breadcrumbs': breadcrumbs,
                'pfx': APP_PREFIX,
                'site_url': admin.site.site_url}

    # Make sure we add special group permission(s)
    add_app_access(request, context)

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

    def get_app_access(self, context):
        # Make sure we add special group permission(s)
        add_app_access(self.request, context)
        return True


class ProjectDetails(ProjectEdit):
    """Show the details of a [Project]"""
    rtype = "html"


class ProjectListView(BasicList):
    """Paginated view of project instances"""

    model = Project
    listform = ProjectForm
    extend_template = "brief/layout.html"
    order_cols = ['name', 'description']
    order_heads = [{'name': 'Name', 'order': 'o=1', 'type': 'str', 'field': 'name', 'linkdetails': True},
                   {'name': 'Progress', 'order': 'o=2', 'type': 'str', 'custom': 'progress', 'linkdetails': True},
                   {'name': 'Description', 'order': 'o=3', 'type': 'str', 'field': 'description', 'linkdetails': True, 'main': True},
                   {'name': 'Actions', 'order': '', 'type': 'str', 'custom': 'actions'}]

    def initializations(self):
        qs = BriefQuestion.objects.filter(ntype="")
        with transaction.atomic():
            for obj in qs:
                obj.ntype = "opt"
                obj.save()
        return None

    def get_app_access(self, context):
        # Make sure we add special group permission(s)
        add_app_access(self.request, context)
        return True

    def get_field_value(self, instance, custom):
        sBack = ""
        sTitle = ""
        html = []

        # Figure out what to show
        if custom == "actions":
            # The buttons for the actions that can be taken
            url = reverse("brief_master", kwargs={'pk': instance.id})
            html.append('<a href="{}" title="Project brief"><span class="glyphicon glyphicon-th-list"><span></a>'.format(url))
            # COmbineer
            sBack = "\n".join(html)
        elif custom == "progress":
            sBack = instance.get_ptype_display()

        # Retourneer wat kan
        return sBack, sTitle


class BriefEdit(BasicDetails):
    """Allow saving and processing the answers to project brief questions"""

    model = Project
    mForm = QuestionsForm
    prefix = "que"
    mainitems = []

    def get_app_access(self, context):
        # Make sure we add special group permission(s)
        add_app_access(self.request, context)
        return True

    def after_save(self, form, instance):
        msg = ""
        bResult = True
        oErr = ErrHandle()
        try:
            # Process the form instances
            if getattr(form, 'cleaned_data') != None:
                cleaned_data = form.cleaned_data
                # Walk all the cleaned_data, processing the answers to the brief questions
                for k,v in cleaned_data.items():
                    if "bq-" in k:
                        v = v.strip()
                        arK = k.split("-")
                        question_id = arK[1]
                        # See if there already was an answer to this question
                        answer = AnswerQuestion.objects.filter(project=instance, question_id=question_id).first()
                        if answer == None:
                            # Is this a new answer?
                            if v != "":
                                # Add this answer
                                answer = AnswerQuestion.objects.create(project=instance, question_id=question_id, content=v)
                        elif answer.content != v:
                            # Update the answer that is already there
                            answer.content = v
                            answer.save()
                # Calculate the 'todo' stuff of the sections
                lst_back = []
                for sec in BriefSection.objects.all():
                    todo = sec.get_todo_html(instance)
                    if todo != "":
                        todo_id = "todo_s_{}".format(sec.id)
                        oSection = dict(id=todo_id, todo=todo)
                        lst_back.append(oSection)
                self.lst_typeahead = lst_back
        except:
            msg = oErr.get_error_message()
            bResult = False
        return bResult, msg


class BriefMaster(BriefEdit):
    """Show the project brief modules and allow filling in the questions"""

    template_name = "brief/pb_master.html"
    rtype = "html"

    def add_to_context(self, context, instance):
        oErr = ErrHandle()
        try:
            # Look at the object_id
            context['object_id'] = "{}".format(instance.id)
            context['pname'] = instance.name
            
            # Make sure we add special group permission(s)
            add_app_access(self.request, context)

            # We need to have the form object too
            qform = context['queForm']

            lst_module = []
            for mod in BriefModule.objects.all().order_by("order"):
                # Start an object for this module
                oModule = dict(module=mod)
                # Find out what sections there are in this module
                lst_section = []
                for sec in mod.modulesections.all().order_by("order"):
                    # Start section object
                    oSection = dict(section=sec)
                    # Find all the questions in this section
                    lst_question = []
                    for question in sec.sectionquestions.all().order_by("order"):
                        # The main part of the question is the question itself
                        oQuestion = dict(question=question)
                        # The second part of the question is the field-name
                        formfieldname = "bq-{}".format(question.id)
                        if question.rtype == "entri":
                            # This means that the 'formfield' should contain a table with add possibilities
                            oQuestion['formfield'] = ""
                            oQuestion['entries']= question.questionentries.all().order_by('order')
                            # Get the existing answers
                            answers = []
                            aq = AnswerQuestion.objects.filter(project=instance, question=question).first()
                            if aq != None and aq != "" and aq[0] == "[":
                                answers = json.loads(aq.content)
                            oQuestion['answers'] = answers
                        else:
                            # The formfield is the normal form field
                            oQuestion['formfield'] = qform[formfieldname]

                        # Add question to list
                        lst_question.append(oQuestion)
                    # Add questions to section
                    oSection['questions'] = lst_question
                    # Calculate how many need to be done in this section
                    oSection['todo'] = sec.get_todo_html(instance)
                    # Add section
                    lst_section.append(oSection)
                # Add sections to this module
                oModule['sections'] = lst_section
                # Add module
                lst_module.append(oModule)
            # THis is what we pass on
            context['modules'] = lst_module
        except:
            msg = oErr.get_error_message()
            oErr.DoError("BriefMaster/add_to_context")

        # Return the context we have adapted
        return context

