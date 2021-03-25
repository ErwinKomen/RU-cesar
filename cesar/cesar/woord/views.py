"""
Definition of views for the WOORD app.
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
import os.path, io, csv
import random

from cesar.settings import APP_PREFIX, WRITABLE_DIR, STATIC_ROOT
from cesar.basic.views import BasicList, BasicDetails, BasicPart
from cesar.browser.views import nlogin
from cesar.utils import ErrHandle

from cesar.woord.models import WoordUser, Choice, Question, Result, Stimulus
from cesar.woord.forms import UserForm

# Global debugging 
bDebug = False

# Provide application-specific information
PROJECT_NAME = "woord"
app_user = "{}_user".format(PROJECT_NAME.lower())
app_uploader = "{}_uploader".format(PROJECT_NAME.lower())
app_editor = "{}_editor".format(PROJECT_NAME.lower())
app_userplus = "{}_userplus".format(PROJECT_NAME.lower())
app_moderator = "{}_moderator".format(PROJECT_NAME.lower())

def initialize_woord():
    """Fill the application if this is needed"""

    def get_stimulus(row):
        woord = ""
        cat = ""
        if row != "":
            parts = re.split(r'\s+', row)
            if len(parts) > 1:
                woord = parts[0]
                cat = parts[1].replace("(", "").replace(")", "")
        oBack = dict(woord=woord, cat=cat)
        return oBack

    oErr = ErrHandle()
    bNeedRandomization = False

    try:
        # Figure out directory and file names
        woord_dir = os.path.abspath(os.path.join(WRITABLE_DIR, "../woord"))
        choices_file = os.path.abspath(os.path.join(woord_dir, "choices.txt"))
        stimuli_file = os.path.abspath(os.path.join(woord_dir, "stimuli.txt"))

        # Check on number of users
        if WoordUser.objects.count() <= 1:
            # Create 20 random users
            with transaction.atomic():
                for number in range(20):
                    username = WoordUser.generate_new()
                    WoordUser.objects.create(name=username)

        # Check on choices
        if Choice.objects.count() == 0:
            # Load choices
            with open(choices_file) as f:
                reader = csv.reader(f, dialect='excel', delimiter='\t')
                left, right = zip(*reader)
            # Make lists
            left_lst = list(left)
            right_lst = list(right)
            # Copy and create from these lists
            break_points = ['heel', 'niet']
            with transaction.atomic():
                for idx, left in enumerate(left_lst):
                    right = right_lst[idx]
                    name = left
                    for bp in break_points:
                        if bp in left:
                            name = left.split(bp)[1].strip()
                            break
                    # Create object
                    Choice.objects.create(name=name, left=left, right=right)

        # Check on stimuli
        if Stimulus.objects.count() == 0:
            bNeedRandomization = True
            # Load the stimuli
            with open(stimuli_file, encoding="utf-8") as f:
                reader = csv.reader(f, dialect='excel')
                lst_stimuli = [get_stimulus(row) for row in reader]
            # Add the stimuli into the objects
            with transaction.atomic():
                for oStimulus in lst_stimuli:
                    woord = oStimulus['woord']
                    cat = oStimulus['cat']
                    Stimulus.objects.create(woord=woord, category=cat)

        # Do we need to randomize?
        if bNeedRandomization:
            # Remove previous questions
            Question.objects.all().delete()

            # Combine stimuli and choices so that we have the full set
            result = []
            with transaction.atomic():
                for stimulus in Stimulus.objects.all():
                    for choice in Choice.objects.all():
                        obj = Question.objects.create(stimulus=stimulus, choice=choice)
                        result.append(obj)

            # Shuffle the question objects
            random.shuffle(result)

            # Divide the shuffled questions over sets 
            
    except:
        msg = oErr.get_error_message()
        oErr.DoError("initialize_woord")


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
    template_name = 'woord/index.html'
    # Define the initial context
    context =  {'title':'Woordbeoordelingen','year':datetime.now().year,
                'pfx': APP_PREFIX,'site_url': admin.site.site_url}

    # Make sure we add special group permission(s)
    add_app_access(request, context)

    if not user_is_authenticated(request) or not user_is_ingroup(request, app_user): 
        # Username is either void, or this user is not a WOORD user
        return nlogin(request)

    if user_is_superuser(request):
        # See if initialization is needed
        initialize_woord()

    # Add a form for the user to enter his/her name
    context['userform'] = UserForm()

    # Render and return the page
    return render(request, template_name, context)

def nlogin(request):
    """Renders the not logged-in page."""

    assert isinstance(request, HttpRequest)
    # Specify the template
    template_name = 'woord/nlogin.html'
    # Define the initial context
    context =  {'title':'NoPermission','year':datetime.now().year,
                'pfx': APP_PREFIX,'site_url': admin.site.site_url}

    # Render and return the page
    return render(request, template_name, context)

def question(request):
    """Check this user's existence and start with the questions"""

    def get_stimulus(obj):
        # Transform a question_values object into a stimulus object
        oBack = {}
        woord = obj['woord']
        category = obj['category']
        oBack['stimulus']  = "{}&nbsp;&nbsp;{}".format(woord, category)
        oBack['left'] =obj['choice__left']
        oBack['right']=obj['choice__right']
        return oBack


    # First make sure that this is a HTTP request
    assert isinstance(request, HttpRequest)

    # Get the parameters passed on
    qd = request.GET if request.method.lower() == "get" else request.POST
    username = qd.get("username", "")

    # Check for valid user - and if it exists, get a link to that user
    woorduser = WoordUser.get_user(username)
    if username == "" or woorduser == None:
        # Username is either void, or this user is not a WOORD user
        return nlogin(request)

    # Get all the questions assigned to this user, but not yet done
    stimuli = Stimuli.objects.filter(woorduser=woorduser)
    questions = Question.objects.filter(stimuli=stimuli, status='created').values(
        'woord', 'category', 'choice__left', 'choice__right')
    lst_stimulus = [get_stimulus(x) for x in questions]

    total_num = Question.objects.filter(stimuli=stimuli).count()
    percentage = len(lst_stimulus) / total_num

    # Specify the template
    template_name = 'woord/question.html'
    # Define the initial context
    context =  {'title':'Woordvragen','year':datetime.now().year,
                'pfx': APP_PREFIX,'site_url': admin.site.site_url}
    # Additional context information
    context['woordusername'] = woorduser.name
    context['lst_stimulus'] = lst_stimulus
    context['question_url'] = reverse('woord_question')
    context['percentage'] = percentage

    # Make sure we add special group permission(s)
    add_app_access(request, context)

    # Render and return the page
    return render(request, template_name, context)




