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

from cesar.woord.models import WoordUser, Choice, Question, Qset, Result, Stimulus, QuestionSet
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

NUMBER_OF_PARTICIPANTS = 40

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

    #if not user_is_authenticated(request) or not user_is_ingroup(request, app_user): 
    #    # Username is either void, or this user is not a WOORD user
    #    return nlogin(request)

    if user_is_superuser(request):
        # See if initialization is needed
        msg = initialize_woord()

    # Add a form for the user to enter his/her name
    context['userform'] = UserForm()

    # Render and return the page
    return render(request, template_name, context)

def initialize_woord(additional=None, randomize=None):
    """Fill the application if this is needed
    
    Initial: only use stimuli.txt
    Issue #147: read stimuli2021.txt, omitting first line with column headers
    """

    def get_stimulus(row):
        woord = ""
        cat = ""
        note = ""
        oBack = {}
        try:
            if len(row) == 3:
                woord = row[0]
                cat = row[1]
                note = row[2]
                oBack = dict(woord=woord, cat=cat, note=note)
            elif row != "":
                # parts = re.split(r'\s+', row)
                parts = re.split(r'\t', row)
                if len(parts) > 1:
                    woord = parts[0]
                    cat = parts[1] # parts[1].replace("(", "").replace(")", "")
                    note = parts[2]
                    oBack = dict(woord=woord, cat=cat, note=note)
            else:
                # Empty row
                iStop = 1
        except:
            msg = oErr.get_error_message()
            oErr.DoError("get_stimulus")
        return oBack

    oErr = ErrHandle()
    bNeedRandomization = False
    msg = "no changes"
    bOrderStimuli = True                # See issue #151: (valid) choices must be treated one by one for the user
    STIMULI_NAME = "stimuli2021.txt"    # Was: stimuli.txt
    lhtml = []

    try:
        # Figure out directory and file names
        woord_dir = os.path.abspath(os.path.join(WRITABLE_DIR, "../woord"))
        choices_file = os.path.abspath(os.path.join(woord_dir, "choices.txt"))
        stimuli_file = os.path.abspath(os.path.join(woord_dir, STIMULI_NAME))
        if randomize != None and randomize == "reset":
            bNeedRandomization = True

        # Check on number of users
        if WoordUser.objects.count() <= 1:
            # Create 20 random users
            with transaction.atomic():
                for number in range(NUMBER_OF_PARTICIPANTS):
                    username = WoordUser.generate_new()
                    WoordUser.objects.create(name=username)
            lhtml.append("Created {} users".format(NUMBER_OF_PARTICIPANTS))

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
            lhtml.append("Created {} choices".format(len(left_lst)))

        # Check on stimuli
        oErr.Status("initialize_woord #1")
        if additional != None and additional == "stimuli":
            # THis is a POST method, continue
            count = Stimulus.objects.count()
            # Delete
            Stimulus.objects.all().delete()
            # Prepare message
            lhtml.append("Stimuli deleted: {}".format(count))

        if Stimulus.objects.count() == 0:
            bNeedRandomization = True
            oErr.Status("initialize_woord #2")
            # Load the stimuli
            with open(stimuli_file) as f:
                reader = csv.reader(f, dialect='excel-tab')
                lst_stimuli = [get_stimulus(row) for row in reader]
            oErr.Status("initialize_woord #3")
            # Add the stimuli into the objects
            with transaction.atomic():
                # Note: skip the first line containing column headers
                for oStimulus in lst_stimuli[1:]:
                    woord = oStimulus['woord']
                    cat = oStimulus['cat']
                    note = oStimulus['note']
                    Stimulus.objects.create(woord=woord, category=cat, note=note)
            oErr.Status("initialize_woord #4")
            lhtml.append("Read from file {} stimuli".format(len(lst_stimuli)))

        # Otherwise in need of randomization?
        if Question.objects.count() == 0:
            bNeedRandomization = True

        # Do we need to randomize?
        if bNeedRandomization:
            # Remove previous questions
            Question.objects.all().delete()
            # Remove previous questions
            Qset.objects.all().delete()
            lhtml.append("Removed previous questions and qsets")

            # Combine stimuli and choices so that we have the full set
            if bOrderStimuli:
                # See issue #151
                result_sets = []
                with transaction.atomic():
                    # Iterate over the choices in the correct order
                    for choice in Choice.objects.filter(valid=True).order_by("id"):
                        # Stimuli for this result set
                        result = []
                        for stimulus in Stimulus.objects.all():
                            obj = Question.objects.create(stimulus=stimulus, choice=choice)
                            result.append(obj.id)
                        # Add this set to the result_sets
                        result_sets.append(result)
                lhtml.append("Created {} questions".format(Question.objects.count()))

                # Divide the shuffled questions over sets 
                num_sets = NUMBER_OF_PARTICIPANTS + 10
                for i in range(num_sets):
                    # Show where we are
                    oErr.Status("initialize_woord random set #{}".format(i))
                    # Create a Qset
                    qset = Qset.objects.create()
                    # Walk all the result sets
                    order = 0
                    for result in result_sets:
                        # Shuffle the question object id's
                        random.shuffle(result)
                        # Make the links for this shuffle
                        with transaction.atomic():
                            for idx, question_id in enumerate(result):
                                order = order + 1
                                QuestionSet.objects.create(qset=qset, question_id=question_id, order=order)
                lhtml.append("Created {} question sets".format(num_sets))

            else:
                result = []
                # Full randomization
                with transaction.atomic():
                    # Iterate over all stimuli (will be 5000)
                    # 2021: these are now 1823
                    for stimulus in Stimulus.objects.all():
                        # And then over all choices (should be just 1)
                        # 2021: this is now 2
                        for choice in Choice.objects.filter(valid=True):
                            # This yields 10,000 objects
                            obj = Question.objects.create(stimulus=stimulus, choice=choice)
                            result.append(obj.id)
                lhtml.append("Created {} questions".format(Question.objects.count()))

                # Divide the shuffled questions over sets 
                num_sets = NUMBER_OF_PARTICIPANTS + 10
                for i in range(num_sets):
                    # Show where we are
                    oErr.Status("initialize_woord random set #{}".format(i))
                    # Shuffle the question object id's
                    random.shuffle(result)
                    # Create a Qset
                    qset = Qset.objects.create()
                    # Make the links for this shuffle
                    with transaction.atomic():
                        for idx, question_id in enumerate(result):
                            order = idx + 1
                            QuestionSet.objects.create(qset=qset, question_id=question_id, order=order)
                lhtml.append("Created {} question sets".format(num_sets))

        # COmbine the message
        msg = "<br />".join(lhtml)
            
    except:
        msg = oErr.get_error_message()
        oErr.DoError("initialize_woord")

    return msg
        
def tools(request):
    """Renders the tools page."""

    assert isinstance(request, HttpRequest)
    # Specify the template
    template_name = 'woord/tools.html'
    # Define the initial context
    context =  {'title':'Woord tools','year':datetime.now().year,
                'pfx': APP_PREFIX,'site_url': admin.site.site_url}

    # Make sure we add special group permission(s)
    add_app_access(request, context)

    if not user_is_authenticated(request) or not \
       (user_is_ingroup(request, app_user) or user_is_ingroup(request, app_editor) or user_is_superuser(request)): 
        # Username is either void, or this user is not a WOORD user
        return nlogin(request)

    # Add calculations
    working_id = [x['woorduser__id'] for x in Qset.objects.filter(woorduser__isnull=False).values('woorduser__id').distinct()]
    context['count_user'] = WoordUser.objects.count()
    context['users_working'] = ", ".join([x.name for x in WoordUser.objects.filter(id__in=working_id)])
    context['users_available'] = ", ".join([x.name for x in WoordUser.objects.exclude(id__in=working_id)])
    context['count_choice'] = Choice.objects.filter(valid=True).count()
    context['count_stimulus'] = Stimulus.objects.count()
    context['count_question'] = Question.objects.count()
    context['count_qset'] = Qset.objects.count()

    done_count = Question.objects.filter(status="done").count()
    context['progr_done'] = done_count
    context['progr_users'] = len(working_id)

    # Render and return the page
    return render(request, template_name, context)

def reset(request):
    """Reset system."""

    oErr = ErrHandle()
    oData = dict(status="fail")

    try:
        # Only allow POST command
        if request.is_ajax() and request.method == "POST" and user_is_authenticated(request) and \
            (user_is_superuser(request) or user_is_ingroup(request, app_editor)):
            # Get the parameters passed on
            qd = request.POST
            action = qd.get("action", "")

            if action == "questions":
                # THis is a POST method, continue
                count = Question.objects.count()
                # Delete
                Question.objects.all().delete()
                # Prepare message
                oData['msg'] = "Questions deleted: {}".format(count)

            elif action == "stimuli":
                oData['msg'] = initialize_woord("stimuli")

            elif action == "randomize":
                oData['msg'] = initialize_woord(randomize = "reset")

            elif action == "users":
                # THis is a POST method, continue
                count = WoordUser.objects.count()
                user_id = [x['id'] for x in WoordUser.objects.all().values('id')]
                # Delete user results
                count_res = Result.objects.filter(user__id__in=user_id).count()
                Result.objects.filter(user__id__in=user_id).delete()
                # Delete users
                WoordUser.objects.all().delete()
                # Reset done  status
                with transaction.atomic():
                    for obj in Question.objects.filter(status="done"):
                        obj.status = "reset"
                        obj.save()
                # Prepare message
                oData['msg'] = "Woord-Users deleted: {}".format(count)

            elif action == "init":
                oData['msg'] = initialize_woord()

            # REturn positively
            oData['status'] = "ok"
        else:
            oData['msg'] = "Not authenticated"
    except:
        msg = oErr.get_error_message()
        oErr.DoError("question")
        oData['status'] = "error"
        oData['msg'] = msg

    mimetype = "application/json"
    data = json.dumps(oData)
    return HttpResponse(data, mimetype)

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
        bOnlyWoord = True   # Issue #150

        # Transform a question_values object into a stimulus object
        oBack = {}
        woord = obj['question__stimulus__woord']
        if bOnlyWoord:
            oBack['stimulus']  = woord
        else:
            category = obj['question__stimulus__category']
            oBack['stimulus']  = "{}&nbsp;&nbsp;{}".format(woord, category)

        # Issue #150: only woord, not category

        oBack['left'] =obj['question__choice__left']
        oBack['right']=obj['question__choice__right']
        oBack['questionid'] = obj['question_id']
        return oBack

    def get_results(sResult):
        """Convert the string into a proper list of objects"""

        lBack = []
        if not sResult is None:
            lResult = sResult.split("\n")
            for item in lResult:
                if item != "" and item[0] == "{":
                    lBack.append(json.loads(item))
        return lBack

    oErr = ErrHandle()
    bUseSlider = False  # See issue #152
    bDoQuestions = False

    try:
        # First make sure that this is a HTTP request
        assert isinstance(request, HttpRequest)

        # Specify the template
        template_name = 'woord/question.html'
        # Define the initial context
        context =  {'title':'Woordvragen','year':datetime.now().year,
                    'availability': True,
                    'pfx': APP_PREFIX,'site_url': admin.site.site_url}

        # Get the parameters passed on
        qd = request.GET if request.method.lower() == "get" else request.POST
        username = qd.get("username", "")
        lResults = qd.get("results", None)

        # Check for valid user - and if it exists, get a link to that user
        woorduser = WoordUser.get_user(username)
        if username == "" or woorduser == None:
            # Username is either void, or this user is not a WOORD user
            return nlogin(request)

        # Action depends on the status of the user
        if woorduser.status == "created":
            # Need to show the EXPLAIN concreteness page
            woorduser.set_status("explain_conc")
            # Specify the template
            template_name = 'woord/explain_conc.html'
            # Define the initial context
            context =  {'title':'Uitleg 1','year':datetime.now().year,
                        'availability': True,
                        'pfx': APP_PREFIX,'site_url': admin.site.site_url}

        elif woorduser.status == "explain_conc":
            # Need to show the EXPLAIN specificity page
            woorduser.set_status("explain_spec")
            # Specify the template
            template_name = 'woord/explain_spec.html'
            # Define the initial context
            context =  {'title':'Uitleg 2','year':datetime.now().year,
                        'availability': True,
                        'pfx': APP_PREFIX,'site_url': admin.site.site_url}

        elif woorduser.status == "explain_spec":
            woorduser.set_status("questioning")
            bDoQuestions = True
        elif woorduser.status == "questioning":
            bDoQuestions = True
        elif woorduser.status == "lastdone":
            # Need to show the THANKYOU page
            pass

        if bDoQuestions:
            # Specify the template
            template_name = 'woord/question.html'
            # Define the initial context
            context =  {'title':'Woordvragen','year':datetime.now().year,
                        'availability': True,
                        'pfx': APP_PREFIX,'site_url': admin.site.site_url}
            # Get all the questions assigned to this user, but not yet done
            qset = Qset.objects.filter(woorduser=woorduser).first()
            if qset == None:
                # No set has yet been assigned to this user: assign one
                qset = Qset.objects.filter(woorduser__isnull=True).first()
                if qset == None:
                    # No set is available anymore
                    context['availability'] = False
                else:
                    # Assign this set to the user
                    qset.woorduser = woorduser
                    qset.save()
            # Continue if all is well
            if not qset is None:
                # Process any questions handed over to me
                lst_result = get_results(lResults)
                for item in lst_result:
                    # Find out which question this is
                    question = Question.objects.filter(id=item['questionid']).first()
                    if not question is None:
                        # Add the response to this question
                        judgment = item['score']
                        dontknow = item['dontknow']
                        result = Result.objects.create(
                            user=woorduser, question=question, judgment=judgment, dontknown=dontknow)
                        # Change the status of this question
                        question.status = "done"
                        question.save()

                # Find the remaining questions
                questions = QuestionSet.objects.filter(qset__woorduser=woorduser, question__status='created').order_by('order').values(
                    'question_id', 'question__stimulus__woord', 'question__stimulus__category', 
                    'question__choice__left', 'question__choice__right')

                lst_stimulus = [get_stimulus(x) for x in questions[:10]]

                # Calculate the percentage of questions still needing to be answered
                total_num = qset.questions.count()
                done_count = qset.questions.filter(status="done").count()
                percentage = done_count / total_num

                # Additional context information
                context['woordusername'] = woorduser.name
                context['lst_stimulus'] = lst_stimulus
                context['question_url'] = reverse('woord_question')
                context['percentage'] = percentage
                context['progr_done'] = done_count
                context['progr_total'] = total_num
                context['user_slider'] = bUseSlider

        # Make sure we add special group permission(s)
        add_app_access(request, context)
    except:
        msg = oErr.get_error_message()
        oErr.DoError("question")

    # Render and return the page
    return render(request, template_name, context)




