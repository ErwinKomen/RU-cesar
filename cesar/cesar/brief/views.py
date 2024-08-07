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
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import sys
import json
import re
import os.path, io, shutil
import tarfile

from cesar.settings import APP_PREFIX, WRITABLE_DIR, STATIC_ROOT
from cesar.basic.views import BasicList, BasicDetails, BasicPart
from cesar.browser.views import nlogin
from cesar.seeker.views import csv_to_excel
from cesar.brief.models import AnswerEntry, AnswerQuestion, BriefEntry, BriefModule, BriefQuestion, BriefSection, Project, qids, \
                            BriefProduct, History, adapt_markdown
from cesar.brief.forms import ProjectForm, QuestionsForm, AnswerEntryForm, ProductForm
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
    response = False if user == None else user.is_authenticated
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
            ErrHandle().Status("brief: User [{}] is in groups: {}".format(user, glist))
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

# @csrf_exempt
def set_section(request):
    """Set the section for a particular user viewing a particular project brief"""

    oData = dict(status="fail")
    if request.is_ajax() and request.method == "POST":
        oErr = ErrHandle()
        try:
            qd = request.POST
            # Get the project id
            project_id = qd.get("project_id", "")
            module_no = qd.get("module_no", "")
            section_no = qd.get("section_no", "")
            # Validate project
            if project_id != "":
                project = Project.objects.filter(id=project_id).first()
                # Validate module/section
                if module_no != "" and section_no != "": 
                    location = dict(module=int(module_no), 
                                    section=int(section_no),
                                    date=timezone.now().strftime("%Y-%m-%dT%H:%M:%S"))
                    # Set this information in the project information
                    project.info = json.dumps(location)
                    project.save()
                    # Also set a history note
                    History.add_action(request.user.username, project, location)
                    oData['status'] = "ok"
                else:
                    oData['msg'] = "no module or section specified"
            else:
                oData['msg'] = "no project specified"
        except:
            msg = oErr.get_error_message()
            oData['msg'] = msg
            oErr.DoError("set_section")
    else:
        oData['msg'] = "Request is not ajax"
    mimetype = "application/json"
    data = json.dumps(oData)
    return HttpResponse(data, mimetype)


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
            {'type': 'plain', 'label': "Saved:",        'value': instance.get_saved()},
            {'type': 'safe',  'label': "Brief",         'value': self.get_brief_button(instance)},
            {'type': 'safe',  'label': "Report",        'value': self.get_report_button(instance)}
            ]

        # CHeck if this user has edit access to this particular item
        user = User.objects.filter(username=self.request.user.username).first()
        if user != instance.user:
            # Switch off access
            context['is_app_editor'] = False
            context['is_app_uploader'] = False
            context['is_app_userplus'] = False

        # Return the context we have made
        return context

    def get_brief_button(self, instance):
        sBack = ""
        html = []

        # The buttons for the actions that can be taken
        url = reverse("brief_master", kwargs={'pk': instance.id})
        html.append('<a href="{}" title="Project brief"><span class="glyphicon glyphicon-th-list"><span></a>'.format(url))
        # COmbineer
        sBack = "\n".join(html)

        # Retourneer wat kan
        return sBack

    def get_report_button(self, instance):
        sBack = ""
        html = []

        # The buttons for the actions that can be taken
        url = reverse("brief_report", kwargs={'pk': instance.id})
        html.append('<a href="{}" title="Project brief - REPORT"><span class="glyphicon glyphicon-th-list"><span></a>'.format(url))
        # COmbineer
        sBack = "\n".join(html)

        # Retourneer wat kan
        return sBack

    def get_app_access(self, context):
        # Make sure we add special group permission(s)
        add_app_access(self.request, context)
        return True

    def before_save(self, form, instance):
        # Make sure the user is filled in
        if form != None and instance.user_id == None or instance.user == None:
            # Figure out who I am
            user = User.objects.filter(username= self.request.user.username).first()
            # Set me
            form.instance.user = user
        return True, "" 


class ProjectDetails(ProjectEdit):
    """Show the details of a [Project]"""
    rtype = "html"


class ProjectListView(BasicList):
    """Paginated view of project instances"""

    model = Project
    listform = ProjectForm
    extend_template = "brief/layout.html"
    order_cols = ['user__username', 'name', 'description']
    order_heads = [{'name': 'User', 'order': 'o=1', 'type': 'str', 'custom': 'user', 'linkdetails': True},
                   {'name': 'Name', 'order': 'o=2', 'type': 'str', 'field': 'name', 'linkdetails': True},
                   {'name': 'Progress', 'order': 'o=3', 'type': 'str', 'custom': 'progress', 'linkdetails': True},
                   {'name': 'Description', 'order': 'o=4', 'type': 'str', 'field': 'description', 'linkdetails': True, 'main': True},
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
            # REPORT
            url = reverse("brief_report", kwargs={'pk': instance.id})
            html.append('<a href="{}" title="Project brief - REPORT"><span class="glyphicon glyphicon-th-list"><span></a>'.format(url))
            # COmbineer
            sBack = "\n".join(html)
        elif custom == "progress":
            sBack = instance.get_ptype_display()
        elif custom == "user":
            sBack = instance.user.username

        # Retourneer wat kan
        return sBack, sTitle


class BriefEdit(BasicDetails):
    """Allow saving and processing the answers to project brief questions"""

    model = Project
    mForm = QuestionsForm
    prefix = "que"
    mainitems = []

    def add_to_context(self, context, instance):
        # CHeck if this user has edit access to this particular item
        user = User.objects.filter(username=self.request.user.username).first()
        if user != instance.user:
            # Switch off access
            context['is_app_editor'] = False
            context['is_app_uploader'] = False
            context['is_app_userplus'] = False

        return context

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
        # First execute the [BriefEdit] default context additions
        context = super(BriefMaster, self).add_to_context(context, instance)

        # Now we may continue here
        oErr = ErrHandle()
        try:
            # Look at the object_id
            context['object_id'] = "{}".format(instance.id)
            context['pname'] = instance.name
            
            ## Make sure we add special group permission(s)
            #add_app_access(self.request, context)

            # Default values
            module = 1      # Start with section #1 "Language"
            section = -1    # No section opened
            # Possibly get alternative values
            if instance.info != "" and instance.info[0] == "{":
                info = json.loads(instance.info)
                module = info.get('module', 1)
                section = info.get('section', -1)

            # We need to have the form object too
            qform = context['queForm']

            lst_module = []
            for mod in BriefModule.objects.all().order_by("order"):
                # Start an object for this module
                oModule = dict(module=mod)
                # Is this the opening section?
                if mod.order == module:
                    oModule['show'] = True
                # Find out what sections there are in this module
                lst_section = []
                for sec in mod.modulesections.all().order_by("order"):
                    # Start section object
                    oSection = dict(section=sec)
                    # Is this the section to be shown?
                    if section >=0 and mod.order == module and sec.order == section:
                        oSection['show'] = True
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
                            if question.rtype == "mline":
                                oQuestion['markdown'] = adapt_markdown(qform[formfieldname].value(), lowercase=False)

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

            # Explicitly say what the mode is
            context['mode'] = "view" if not context['is_app_editor'] else "edit"
            context['title'] = "{} brief".format(instance.name)
            context['downloadurl'] = reverse('brief_report', kwargs={'pk': instance.id})
        except:
            msg = oErr.get_error_message()
            oErr.DoError("BriefMaster/add_to_context")

        # Return the context we have adapted
        return context


class BriefReport(BriefMaster):
    """Show the project brief in a report"""

    template_name = "brief/report.html"
    rtype = "download"
    dtype = "htmldoc"

    def custom_init(self, instance):
        # Calculate the [dname], document name
        self.dname = "Brief-{}-{}.doc".format(instance.name, timezone.now().strftime("%Y%m%d-%H:%M"))
        return None

    def add_to_context(self, context, instance):
        # First execute the [BriefEdit] default context additions
        context = super(BriefReport, self).add_to_context(context, instance)
        files = []
        files.append(os.path.join(STATIC_ROOT, "brief", "content", "bootstrap.min.css"))
        files.append(os.path.join(STATIC_ROOT, "brief", "content", "sil-base.css"))
        contents = []
        for file in files:
            with open(file, "r", encoding="utf8") as fp:
                contents.append(fp.read())

        context['bootstrapcss'] = '<style type="text/css">{}</style>'.format( contents[0])
        context['silbasecss'] = '<style type="text/css">{}</style>'.format(contents[1])
        return context


class BriefProductEdit(BasicDetails):
    """Details view for one Product"""

    model = BriefProduct
    mForm = ProductForm
    prefix = "prd"
    rtype = "json"
    mainitems = []
    project = None
    extend_template = "brief/layout.html"
    prefix_type = "simple"

    def custom_init(self, instance):

        if instance != None:
            # Indicate where to go after deleting
            if instance != None and instance.project != None:
                self.afterdelurl = reverse('project_details', kwargs={'pk': instance.project.id})
        return None

    def add_to_context(self, context, instance):
        """Add to the existing context"""

        # Figure out what the project id is
        project_id = None if instance == None else instance.project.id

        # Define the main items to show and edit
        context['mainitems'] = [
            # -------- HIDDEN field values ---------------
            {'type': 'plain', 'label': "Project id",    'value': project_id,            'field_key': "project", 'empty': 'hide'},
            # --------------------------------------------
            {'type': 'plain', 'label': "Product:",      'value': instance.name,         'field_key': 'name'},
            {'type': 'plain', 'label': "Scripture:",    'value': instance.scripture,    'field_key': 'scripture'},
            {'type': 'plain', 'label': "Format:",       'value': instance.format,       'field_key': 'format'},
            {'type': 'plain', 'label': "Media:",        'value': instance.media,        'field_key': 'media'},
            {'type': 'plain', 'label': "Goal:",         'value': instance.goal,         'field_key': 'goal'  },
            {'type': 'plain', 'label': "Audience:",     'value': instance.audience,     'field_key': 'audience'},
            {'type': 'plain', 'label': "Timing:",       'value': instance.timing,       'field_key': 'timing'},
            {'type': 'plain', 'label': "Saved:",        'value': instance.get_saved()}
            ]

        # Add a button to go back to this project's brief
        topleftlist = []
        if instance.project != None:
            project = instance.project
            buttonspecs = dict(
                label="B", title="Return to this project's brief",
                url=reverse('brief_master', kwargs={'pk': project_id}))
            topleftlist.append(buttonspecs)
        context['topleftbuttons'] = topleftlist

        # Return the context we have made
        return context

    def get_app_access(self, context):
        # Make sure we add special group permission(s)
        add_app_access(self.request, context)
        return True

    def after_new(self, form, instance):
        """Action to be performed after adding a new item"""

        ## Set the 'afternew' URL
        project = instance.project
        if project != None and instance.order < 0:
            # Calculate how many products
            product_count = project.projectquestionproducts.count()
            # Make sure the new project gets changed
            form.instance.order = product_count

        # Return positively
        return True, ""


class BriefProductDetails(BriefProductEdit):
    """Show the details of a [Product]"""
    rtype = "html"


class BriefProductList(BasicList):
    """List of products, allowing filtering for a project"""

    model = BriefProduct
    listform = ProductForm
    new_button = False      # Adding is not from here
    extend_template = "brief/layout.html"
    order_cols = ['product', 'order', 'name']
    order_heads = [
        {'name': 'Project',     'order': 'o=1', 'type': 'str', 'custom': 'project',     'linkdetails': True},
        {'name': 'Name',        'order': 'o=2', 'type': 'str', 'field': 'name',         'linkdetails': True, 'main': True},
        {'name': 'Scripture',   'order': 'o=3', 'type': 'str', 'field': 'scripture',    'linkdetails': True},
        {'name': 'Media',       'order': 'o=4', 'type': 'str', 'field': 'media',        'linkdetails': True},
        {'name': 'Actions',     'order': '',    'type': 'str', 'custom': 'actions'}
        ]

    def initializations(self):
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
            url = reverse("brief_master", kwargs={'pk': instance.project.id})
            html.append('<a href="{}" title="Project brief"><span class="glyphicon glyphicon-th-list"><span></a>'.format(url))
            # COmbineer
            sBack = "\n".join(html)
        elif custom == "project":
            sBack = instance.project.name

        # Retourneer wat kan
        return sBack, sTitle
