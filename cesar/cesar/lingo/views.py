"""
Definition of views for the LINGO app.
"""

from django.contrib import admin
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import Group
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.db.models.functions import Lower
from django.forms import formset_factory, inlineformset_factory
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import DetailView
from django.views.generic.base import RedirectView
from django.views.generic import ListView, View
from datetime import datetime
import pytz
import random
import itertools
from django.utils import timezone

from cesar.settings import APP_PREFIX
from cesar.utils import ErrHandle
from cesar.lingo.models import *
from cesar.lingo.forms import ExperimentForm, ParticipantForm, AnswerForm, QdataListForm
from cesar.seeker.views import csv_to_excel

# Debugging for certain functions in this views.py
bDebug = True

paginateEntries = 15


def treat_bom(sHtml):
    """REmove the BOM marker except at the beginning of the string"""

    # Check if it is in the beginning
    bStartsWithBom = sHtml.startswith(u'\ufeff')
    # Remove everywhere
    sHtml = sHtml.replace(u'\ufeff', '')
    # Return what we have
    return sHtml

def get_current_datetime():
    return timezone.now()

def unique_permutations(iterable, r=None):
    # permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
    # permutations(range(3)) --> 012 021 102 120 201 210
    pool = tuple(iterable)
    n = len(pool)
    r = n if r is None else r
    if r > n:
        return
    indices = range(n)
    cycles = range(n, n-r, -1)
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i+1:] + indices[i:i+1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                break
        else:
            return

# Create your views here.
def user_is_authenticated(request):
    # Is this user authenticated?
    username = request.user.username
    user = User.objects.filter(username=username).first()
    if user == None:
        return False
    else:
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

def make_ordering(qs, qd, orders, order_cols, order_heads):

    oErr = ErrHandle()

    try:
        bAscending = True
        sType = 'str'
        order = []
        colnum = ""
        # reset 'used' feature for all heads
        for item in order_heads: item['used'] = None
        if 'o' in qd and qd['o'] != "":
            colnum = qd['o']
            if '=' in colnum:
                colnum = colnum.split('=')[1]
            if colnum != "":
                order = []
                iOrderCol = int(colnum)
                bAscending = (iOrderCol>0)
                iOrderCol = abs(iOrderCol)

                # Set the column that it is in use
                order_heads[iOrderCol-1]['used'] = 1
                # Get the type
                sType = order_heads[iOrderCol-1]['type']
                for order_item in order_cols[iOrderCol-1].split(";"):
                    if sType == 'str':
                        order.append(Lower(order_item))
                    else:
                        order.append(order_item)
                if bAscending:
                    order_heads[iOrderCol-1]['order'] = 'o=-{}'.format(iOrderCol)
                else:
                    # order = "-" + order
                    order_heads[iOrderCol-1]['order'] = 'o={}'.format(iOrderCol)

                # Reset the sort order to ascending for all others
                for idx, item in enumerate(order_heads):
                    if idx != iOrderCol - 1:
                        # Reset this sort order
                        order_heads[idx]['order'] = order_heads[idx]['order'].replace("-", "")
        else:
            for order_item in order_cols[0].split(";"):
                order.append(Lower(order_item))
           #  order.append(Lower(order_cols[0]))
        if sType == 'str':
            if len(order) > 0:
                qs = qs.order_by(*order)
            # qs = qs.order_by('editions__first__date_late')
        else:
            qs = qs.order_by(*order)
        # Possibly reverse the order
        if not bAscending:
            qs = qs.reverse()
    except:
        msg = oErr.get_error_message()
        oErr.DoError("make_ordering")
        lstQ = []

    return qs, order_heads, colnum

def home(request):
    """Renders the home page."""

    assert isinstance(request, HttpRequest)
    # Specify the template
    template_name = 'lingo/index.html'
    # Define the initial context
    context =  {'title':'RU-Cesar-Lingo','year':datetime.now().year,
                'is_lingo_user': user_is_ingroup(request, 'lingo-user'),
                'pfx': APP_PREFIX,'site_url': admin.site.site_url}

    # Create the list of experiments
    lstQ = []
    lstQ.append(Q(status='val'))
    newsitem_list = Experiment.objects.filter(*lstQ).order_by('-saved', '-created')
    context['experiment_list'] = newsitem_list

    # Make sure we add special group permission(s)
    context['is_lingo_editor'] = user_is_ingroup(request, "lingo-editor")
    context['is_in_tsg'] = user_is_ingroup(request, "radboud-tsg")
    # Render and return the page
    return render(request, template_name, context)

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'contact.html',
        {   'is_lingo_user': user_is_ingroup(request, 'lingo-user'),
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
        {   'is_lingo_user': user_is_ingroup(request, 'lingo-user'),
            'title':'More',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'lingo/about.html',
        {   'is_lingo_user': user_is_ingroup(request, 'lingo-user'),
            'title':'About',
            'message':'Radboud University CESAR utility.',
            'year':datetime.now().year,
        }
    )

def short(request):
    """Renders the page with the short instructions."""

    assert isinstance(request, HttpRequest)
    template = 'lingo/short.html'
    context = {'title': 'Short overview',
               'is_lingo_user': user_is_ingroup(request, 'lingo-user'),
               'message': 'Radboud University CESAR-LINGO short intro',
               'year': datetime.now().year}
    return render(request, template, context)

def nlogin(request):
    """Renders the not-logged-in page."""
    assert isinstance(request, HttpRequest)
    context =  {    'title':'Not logged in', 
                    'message':'Radboud University CESAR-LINGO utility.',
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
            return redirect('lingo/home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

@csrf_exempt
def crm_contacts(request):
    """Ad-hoc CRM/contacts"""

    contact_list = [
        {'account': 2, 'address': 'Bla', 'createdBy': 2, 'description': 'Test 1', 'email': 'a@b.nl', 'first_name': 'Kaya', 'isActive': True, 'last_name': 'Abbess', 'phone': '0012121212101'},
        {'account': 2, 'address': 'Lievensweg 21', 'createdBy': 2, 'description': 'Test 2', 'email': 'e.komen@ru.nl', 'first_name': 'Erwin', 'isActive': True, 'last_name': 'Komen', 'phone': '0123456789'}
        ]
    data = {}

    if request.method == 'POST':
        pass
    elif request.method == 'GET':
        # List the contacts we have
        data = { 'data':  contact_list }
    # Return the information
    # return JsonResponse(data, safe=False)
    return JsonResponse(data)


class BasicLingo(View):
    """This is my own versatile handling view.

    Note: this version works with <pk> and not with <object_id>
    """

    # Initialisations
    arErr = []              # errors   
    template_name = None    # The template to be used
    template_err_view = None
    form_validated = True   # Used for POST form validation
    savedate = None         # When saving information, the savedate is returned in the context
    add = False             # Are we adding a new record or editing an existing one?
    obj = None              # The instance of the MainModel
    action = ""             # The action to be undertaken
    MainModel = None        # The model that is mainly used for this form
    form_objects = []       # List of forms to be processed
    formset_objects = []    # List of formsets to be processed
    previous = None         # Return to this
    bDebug = False          # Debugging information
    need_authentication = True
    data = {'status': 'ok', 'html': ''}       # Create data to be returned    
    
    def post(self, request, pk=None):
        # A POST request means we are trying to SAVE something
        self.initializations(request, pk)

        # Explicitly set the status to OK
        self.data['status'] = "ok"

        if self.checkAuthentication(request):
            # Build the context
            context = dict(object_id = pk, savedate=None)
            # context['prevpage'] = get_prevpage(request)     #  self.previous
            context['authenticated'] = user_is_authenticated(request)
            # Action depends on 'action' value
            if self.action == "":
                if self.bDebug: self.oErr.Status("ResearchPart: action=(empty)")
                # Walk all the forms for preparation of the formObj contents
                for formObj in self.form_objects:
                    # Are we SAVING a NEW item?
                    if self.add:
                        # We are saving a NEW item
                        formObj['forminstance'] = formObj['form'](request.POST, prefix=formObj['prefix'])
                    else:
                        # We are saving an EXISTING item
                        # Determine the instance to be passed on
                        instance = self.get_instance(formObj['prefix'])
                        # Make the instance available in the form-object
                        formObj['instance'] = instance
                        # Get an instance of the form
                        formObj['forminstance'] = formObj['form'](request.POST, prefix=formObj['prefix'], instance=instance)

                # Initially we are assuming this just is a review
                context['savedate']="reviewed at {}".format(get_current_datetime().strftime("%X"))

                # Iterate again
                for formObj in self.form_objects:
                    prefix = formObj['prefix']
                    # Adapt if it is not readonly
                    if not formObj['readonly']:
                        # Check validity of form
                        if formObj['forminstance'].is_valid() and self.is_custom_valid(prefix, formObj['forminstance']):
                            # Save it preliminarily
                            instance = formObj['forminstance'].save(commit=False)
                            # The instance must be made available (even though it is only 'preliminary')
                            formObj['instance'] = instance
                            # Perform actions to this form BEFORE FINAL saving
                            bNeedSaving = formObj['forminstance'].has_changed()
                            if self.before_save(prefix, request, instance=instance, form=formObj['forminstance']): bNeedSaving = True
                            if formObj['forminstance'].instance.id == None: bNeedSaving = True
                            if bNeedSaving:
                                # Perform the saving
                                instance.save()
                                # Set the context
                                context['savedate']="saved at {}".format(get_current_datetime().strftime("%X"))
                                # Put the instance in the form object
                                formObj['instance'] = instance
                                # Store the instance id in the data
                                self.data[prefix + '_instanceid'] = instance.id
                                # Any action after saving this form
                                self.after_save(prefix, instance)
                            # Also get the cleaned data from the form
                            formObj['cleaned_data'] = formObj['forminstance'].cleaned_data
                        else:
                            self.arErr.append(formObj['forminstance'].errors)
                            self.form_validated = False
                            formObj['cleaned_data'] = None
                    else:
                        # Form is readonly

                        # Check validity of form
                        if formObj['forminstance'].is_valid() and self.is_custom_valid(prefix, formObj['forminstance']):
                            # At least get the cleaned data from the form
                            formObj['cleaned_data'] = formObj['forminstance'].cleaned_data


                    # Add instance to the context object
                    context[prefix + "Form"] = formObj['forminstance']
                # Walk all the formset objects
                for formsetObj in self.formset_objects:
                    prefix  = formsetObj['prefix']
                    if self.can_process_formset(prefix):
                        formsetClass = formsetObj['formsetClass']
                        form_kwargs = self.get_form_kwargs(prefix)
                        if self.add:
                            # Saving a NEW item
                            formset = formsetClass(request.POST, request.FILES, prefix=prefix, form_kwargs = form_kwargs)
                        else:
                            # Saving an EXISTING item
                            instance = self.get_instance(prefix)
                            qs = self.get_queryset(prefix)
                            if qs == None:
                                formset = formsetClass(request.POST, request.FILES, prefix=prefix, instance=instance, form_kwargs = form_kwargs)
                            else:
                                formset = formsetClass(request.POST, request.FILES, prefix=prefix, instance=instance, queryset=qs, form_kwargs = form_kwargs)
                        # Process all the forms in the formset
                        self.process_formset(prefix, request, formset)
                        # Store the instance
                        formsetObj['formsetinstance'] = formset
                        # Adapt the formset contents only, when it is NOT READONLY
                        if not formsetObj['readonly']:
                            # Is the formset valid?
                            if formset.is_valid():
                                has_deletions = False
                                # Make sure all changes are saved in one database-go
                                with transaction.atomic():
                                    # Walk all the forms in the formset
                                    for form in formset:
                                        # At least check for validity
                                        if form.is_valid() and self.is_custom_valid(prefix, form):
                                            # Should we delete?
                                            if 'DELETE' in form.cleaned_data and form.cleaned_data['DELETE']:
                                                # Check if deletion should be done
                                                if self.before_delete(prefix, form.instance):
                                                    # Delete this one
                                                    form.instance.delete()
                                                    # NOTE: the template knows this one is deleted by looking at form.DELETE
                                                    has_deletions = True
                                            else:
                                                # Check if anything has changed so far
                                                has_changed = form.has_changed()
                                                # Save it preliminarily
                                                sub_instance = form.save(commit=False)
                                                # Any actions before saving
                                                if self.before_save(prefix, request, sub_instance, form):
                                                    has_changed = True
                                                # Save this construction
                                                if has_changed: 
                                                    # Save the instance
                                                    sub_instance.save()
                                                    # Adapt the last save time
                                                    context['savedate']="saved at {}".format(get_current_datetime().strftime("%X"))
                                                    # Store the instance id in the data
                                                    self.data[prefix + '_instanceid'] = sub_instance.id
                                                    # Any action after saving this form
                                                    self.after_save(prefix, sub_instance)
                                        else:
                                            if len(form.errors) > 0:
                                                self.arErr.append(form.errors)
                                
                                # Rebuild the formset if it contains deleted forms
                                if has_deletions or not has_deletions:
                                    # Or: ALWAYS
                                    if qs == None:
                                        formset = formsetClass(prefix=prefix, instance=instance, form_kwargs=form_kwargs)
                                    else:
                                        formset = formsetClass(prefix=prefix, instance=instance, queryset=qs, form_kwargs=form_kwargs)
                                    formsetObj['formsetinstance'] = formset
                            else:
                                # Iterate over all errors
                                for idx, err_this in enumerate(formset.errors):
                                    if '__all__' in err_this:
                                        self.arErr.append(err_this['__all__'][0])
                                    elif err_this != {}:
                                        # There is an error in item # [idx+1], field 
                                        problem = err_this 
                                        for k,v in err_this.items():
                                            fieldName = k
                                            errmsg = "Item #{} has an error at field [{}]: {}".format(idx+1, k, v[0])
                                            self.arErr.append(errmsg)

                            # self.arErr.append(formset.errors)
                    else:
                        formset = []
                    # Add the formset to the context
                    context[prefix + "_formset"] = formset
            elif self.action == "download":
                # We are being asked to download something
                if self.dtype != "":
                    # Initialise return status
                    oBack = {'status': 'ok'}
                    sType = "csv" if (self.dtype == "xlsx") else self.dtype

                    # Get the data
                    sData = self.get_data('', self.dtype)
                    # Decode the data and compress it using gzip
                    bUtf8 = (self.dtype != "db")
                    bUsePlain = (self.dtype == "xlsx" or self.dtype == "csv")

                    # Create name for download
                    # sDbName = "{}_{}_{}_QC{}_Dbase.{}{}".format(sCrpName, sLng, sPartDir, self.qcTarget, self.dtype, sGz)
                    modelname = self.MainModel.__name__
                    obj_id = "n" if self.obj == None else self.obj.id
                    sDbName = "lingo_{}_{}.{}".format(modelname, obj_id, self.dtype)
                    sContentType = ""
                    if self.dtype == "csv":
                        sContentType = "text/tab-separated-values"
                    elif self.dtype == "json":
                        sContentType = "application/json"
                    elif self.dtype == "xlsx":
                        sContentType = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                    # Excel needs additional conversion
                    if self.dtype == "xlsx":
                        # Convert 'compressed_content' to an Excel worksheet
                        response = HttpResponse(content_type=sContentType)
                        response['Content-Disposition'] = 'attachment; filename="{}"'.format(sDbName)    
                        response = csv_to_excel(sData, response, delimiter="\t")
                    else:
                        response = HttpResponse(sData, content_type=sContentType)
                        response['Content-Disposition'] = 'attachment; filename="{}"'.format(sDbName)    

                    # Continue for all formats
                        
                    # return gzip_middleware.process_response(request, response)
                    return response
            elif self.action == "delete":
                # The user requests this to be deleted
                if self.before_delete():
                    # We have permission to delete the instance
                    self.obj.delete()
                    context['deleted'] = True

            # Allow user to add to the context
            context = self.add_to_context(context)

            # Check if 'afternewurl' needs adding
            # NOTE: this should only be used after a *NEW* instance has been made -hence the self.add check
            if 'afternewurl' in context and self.add:
                self.data['afternewurl'] = context['afternewurl']
            if 'afterdelurl' in context:
                self.data['afterdelurl'] = context['afterdelurl']

            # Make sure we have a list of any errors
            error_list = [str(item) for item in self.arErr]
            context['error_list'] = error_list
            context['errors'] = json.dumps( self.arErr)
            if len(self.arErr) > 0:
                # Indicate that we have errors
                self.data['has_errors'] = True
                self.data['status'] = "error"
            else:
                self.data['has_errors'] = False
            # Standard: add request user to context
            context['requestuser'] = request.user

            # Get the HTML response
            if len(self.arErr) > 0:
                if self.template_err_view != None:
                     # Create a list of errors
                    self.data['err_view'] = render_to_string(self.template_err_view, context, request)
                else:
                    self.data['error_list'] = error_list
                    self.data['errors'] = self.arErr
                self.data['html'] = ''
            elif self.action == "delete":
                self.data['html'] = "deleted" 
            else:
                # In this case reset the errors - they should be shown within the template
                sHtml = render_to_string(self.template_name, context, request)
                sHtml = treat_bom(sHtml)
                self.data['html'] = sHtml

            # At any rate: empty the error basket
            self.arErr = []
            error_list = []

        else:
            self.data['html'] = "Please log in before continuing"

        # Return the information
        return JsonResponse(self.data)
        
    def get(self, request, pk=None): 
        self.data['status'] = 'ok'
        # Perform the initializations that need to be made anyway
        self.initializations(request, pk)
        if self.checkAuthentication(request):
            context = dict(object_id = pk, savedate=None)
            context['prevpage'] = self.previous
            context['authenticated'] = user_is_authenticated(request)
            # Walk all the form objects
            for formObj in self.form_objects:        
                # Used to populate a NEW research project
                # - CREATE a NEW research form, populating it with any initial data in the request
                initial = dict(request.GET.items())
                if self.add:
                    # Create a new form
                    formObj['forminstance'] = formObj['form'](initial=initial, prefix=formObj['prefix'])
                else:
                    # Used to show EXISTING information
                    instance = self.get_instance(formObj['prefix'])
                    # We should show the data belonging to the current Research [obj]
                    formObj['forminstance'] = formObj['form'](instance=instance, prefix=formObj['prefix'])
                # Add instance to the context object
                context[formObj['prefix'] + "Form"] = formObj['forminstance']
            # Walk all the formset objects
            for formsetObj in self.formset_objects:
                formsetClass = formsetObj['formsetClass']
                prefix  = formsetObj['prefix']
                form_kwargs = self.get_form_kwargs(prefix)
                if self.add:
                    # - CREATE a NEW formset, populating it with any initial data in the request
                    initial = dict(request.GET.items())
                    # Saving a NEW item
                    formset = formsetClass(initial=initial, prefix=prefix, form_kwargs=form_kwargs)
                else:
                    # show the data belonging to the current [obj]
                    instance = self.get_instance(prefix)
                    qs = self.get_queryset(prefix)
                    if qs == None:
                        formset = formsetClass(prefix=prefix, instance=instance, form_kwargs=form_kwargs)
                    else:
                        formset = formsetClass(prefix=prefix, instance=instance, queryset=qs, form_kwargs=form_kwargs)
                # Process all the forms in the formset
                ordered_forms = self.process_formset(prefix, request, formset)
                if ordered_forms:
                    context[prefix + "_ordered"] = ordered_forms
                # Store the instance
                formsetObj['formsetinstance'] = formset
                # Add the formset to the context
                context[prefix + "_formset"] = formset
            # Allow user to add to the context
            context = self.add_to_context(context)
            # Make sure we have a list of any errors
            error_list = [str(item) for item in self.arErr]
            context['error_list'] = error_list
            context['errors'] = self.arErr
            # Standard: add request user to context
            context['requestuser'] = request.user
            
            # Get the HTML response
            sHtml = render_to_string(self.template_name, context, request)
            sHtml = treat_bom(sHtml)
            self.data['html'] = sHtml
        else:
            self.data['html'] = "Please log in before continuing"

        # Return the information
        return JsonResponse(self.data)
      
    def checkAuthentication(self,request):
        # first check for authentication
        if self.need_authentication and not request.user.is_authenticated:
            # Simply redirect to the home page
            self.data['html'] = "Please log in to work on this project"
            return False
        else:
            return True

    def rebuild_formset(self, prefix, formset):
        return formset

    def initializations(self, request, object_id):
        # Store the previous page
        #self.previous = get_previous_page(request)
        # Clear errors
        self.arErr = []
        # COpy the request
        self.request = request
        # Copy any object id
        self.object_id = object_id
        self.add = object_id is None
        # Get the parameters
        if request.POST:
            self.qd = request.POST
        else:
            self.qd = request.GET

        # Check for action
        if 'action' in self.qd:
            self.action = self.qd['action']

        # Find out what the Main Model instance is, if any
        if self.add:
            self.obj = None
        else:
            # Get the instance of the Main Model object
            self.obj =  self.MainModel.objects.filter(pk=object_id).first()
            # NOTE: if the object doesn't exist, we will NOT get an error here
        # ALWAYS: perform some custom initialisations
        self.custom_init()

    def get_instance(self, prefix):
        return self.obj

    def is_custom_valid(self, prefix, form):
        return True

    def get_queryset(self, prefix):
        return None

    def get_form_kwargs(self, prefix):
        return None

    def get_data(self, prefix, dtype):
        return ""

    def before_save(self, prefix, request, instance=None, form=None):
        return False

    def before_delete(self, prefix=None, instance=None):
        return True

    def after_save(self, prefix, instance=None):
        return True

    def add_to_context(self, context):
        return context

    def process_formset(self, prefix, request, formset):
        return None

    def can_process_formset(self, prefix):
        return True

    def custom_init(self):
        pass    


class LingoDetails(DetailView):
    """Extension of the normal DetailView class for Lingo"""

    template_name = ""      # Template for GET
    template_post = ""      # Template for POST
    formset_objects = []    # List of formsets to be processed
    afternewurl = ""        # URL to move to after adding a new item
    prefix = ""             # The prefix for the one (!) form we use
    previous = None         # Start with empty previous page
    title = ""              # The title to be passedon with the context
    rtype = "json"          # JSON response (alternative: html)
    prefix_type = ""        # Whether the adapt the prefix or not ('simple')
    read_only = False
    mForm = None            # Model form
    newRedirect = False     # Redirect the page name to a correct one after creating
    redirectpage = ""       # Where to redirect to
    add = False             # Are we adding a new record or editing an existing one?

    def get(self, request, pk=None, *args, **kwargs):
        # Initialisation
        data = {'status': 'ok', 'html': '', 'statuscode': ''}
        # always do this initialisation to get the object
        self.initializations(request, pk)
        okay = request.user.is_authenticated
        okay = True
        if not okay:
            # Do not allow to get a good response
            if self.rtype == "json":
                data['html'] = "(No authorization)"
                data['status'] = "error"
                response = JsonResponse(data)
            else:
                response = reverse('nlogin')
        else:
            context = self.get_context_data(object=self.object)

            # Possibly indicate form errors
            # NOTE: errors is a dictionary itself...
            if 'errors' in context and len(context['errors']) > 0:
                data['status'] = "error"
                data['msg'] = context['errors']

            if self.rtype == "json":
                # We render to the _name 
                sHtml = render_to_string(self.template_name, context, request)
                sHtml = sHtml.replace("\ufeff", "")
                data['html'] = sHtml
                response = JsonResponse(data)
            else:
                # This takes self.template_name...
                response = self.render_to_response(context)

        # Return the response
        return response

    def post(self, request, pk=None, *args, **kwargs):
        # Initialisation
        data = {'status': 'ok', 'html': '', 'statuscode': ''}
        # always do this initialisation to get the object
        self.initializations(request, pk)
        # Make sure only POSTS get through that are authorized
        if request.user.is_authenticated or self.read_only:
            context = self.get_context_data(object=self.object)
            # Check if 'afternewurl' needs adding
            if 'afternewurl' in context:
                data['afternewurl'] = context['afternewurl']
            # Check if 'afterdelurl' needs adding
            if 'afterdelurl' in context:
                data['afterdelurl'] = context['afterdelurl']
            # Possibly indicate form errors
            # NOTE: errors is a dictionary itself...
            if 'errors' in context and len(context['errors']) > 0:
                data['status'] = "error"
                data['msg'] = context['errors']

            if self.rtype == "json":
                # We render to the _name 
                sHtml = render_to_string(self.template_post, context, request)
                sHtml = sHtml.replace("\ufeff", "")
                data['html'] = sHtml
                response = JsonResponse(data)
            elif self.newRedirect and self.redirectpage != "":
                # Redirect to this page
                return redirect(self.redirectpage)
            else:
                # This takes self.template_name...
                response = self.render_to_response(context)
        else:
            data['html'] = "(No authorization)"
            data['status'] = "error"
            response = JsonResponse(data)

        # Return the response
        # return JsonResponse(data)
        return response

    def initializations(self, request, pk):
        # Store the previous page
        # self.previous = get_previous_page(request)

        # Copy any pk
        self.pk = pk
        self.add = pk is None
        # Get the parameters
        if request.POST:
            self.qd = request.POST
        else:
            self.qd = request.GET

        # Check for action
        if 'action' in self.qd:
            self.action = self.qd['action']

        # Find out what the Main Model instance is, if any
        if self.add:
            self.object = None
        else:
            # Get the instance of the Main Model object
            # NOTE: if the object doesn't exist, we will NOT get an error here
            self.object = self.get_object()

    def before_delete(self, instance):
        """Anything that needs doing before deleting [instance] """
        return True, "" 

    def after_new(self, form, instance):
        """Action to be performed after adding a new item"""
        return True, "" 

    def before_save(self, instance):
        """Action to be performed after saving an item preliminarily, and before saving completely"""
        return True, "" 

    def add_to_context(self, context, instance):
        """Add to the existing context"""
        return context

    def process_formset(self, prefix, request, formset):
        return None

    def get_formset_queryset(self, prefix):
        return None

    def get_form_kwargs(self, prefix):
        return None

    def get_context_data(self, **kwargs):
        # Get the current context
        context = super(LingoDetails, self).get_context_data(**kwargs)

        # Check this user: is he allowed to UPLOAD data?
        context['authenticated'] = user_is_authenticated(self.request)
        context['is_lingo_editor'] = user_is_ingroup(self.request, 'lingo-editor')
        context['is_in_tsg'] = user_is_ingroup(self.request, "radboud-tsg")

        # Get the parameters passed on with the GET or the POST request
        get = self.request.GET if self.request.method == "GET" else self.request.POST
        initial = get.copy()
        self.qd = initial

        self.bHasFormInfo = (len(self.qd) > 0)

        # Set the title of the application
        context['title'] = self.title

        # Get the instance
        instance = self.object
        bNew = False
        mForm = self.mForm
        frm = None
        oErr = ErrHandle()

        # prefix = self.prefix
        if self.prefix_type == "":
            id = "n" if instance == None else instance.id
            prefix = "{}-{}".format(self.prefix, id)
        else:
            prefix = self.prefix

        if mForm != None:
            # Check if this is a POST or a GET request
            if self.request.method == "POST":
                # Determine what the action is (if specified)
                action = ""
                if 'action' in initial: action = initial['action']
                if action == "delete":
                    # The user wants to delete this item
                    try:
                        bResult, msg = self.before_delete(instance)
                        if bResult:
                            # Remove this sermongold instance
                            instance.delete()
                        else:
                            # Removing is not possible
                            context['errors'] = {'delete': msg }
                    except:
                        msg = oErr.get_error_message()
                        # Create an errors object
                        context['errors'] = {'delete':  msg }
                    # And return the complied context
                    return context
            
                # All other actions just mean: edit or new and send back

                # Do we have an existing object or are we creating?
                if instance == None:
                    # Saving a new item
                    frm = mForm(initial, prefix=prefix)
                    bNew = True
                else:
                    # Editing an existing one
                    frm = mForm(initial, prefix=prefix, instance=instance)

                if not self.read_only: 
                    # Both cases: validation and saving
                    if frm.is_valid():
                        # The form is valid - do a preliminary saving
                        instance = frm.save(commit=False)
                        # Any checks go here...
                        bResult, msg = self.before_save(instance)
                        if bResult:
                            # Now save it for real
                            instance.save()
                        else:
                            context['errors'] = {'save': msg }
                    else:
                        # We need to pass on to the user that there are errors
                        context['errors'] = frm.errors
                # Check if this is a new one
                if bNew:
                    # Any code that should be added when creating a new [SermonGold] instance
                    bResult, msg = self.after_new(frm, instance)
                    if not bResult:
                        # Removing is not possible
                        context['errors'] = {'new': msg }
                    # Check if an 'afternewurl' is specified
                    if self.afternewurl != "":
                        context['afternewurl'] = self.afternewurl
                
            else:
                # Check if this is asking for a new form
                if instance == None:
                    # Get the form for the sermon
                    frm = mForm(prefix=prefix)
                else:
                    # Get the form for the sermon
                    frm = mForm(instance=instance, prefix=prefix)
                # Walk all the formset objects
                for formsetObj in self.formset_objects:
                    formsetClass = formsetObj['formsetClass']
                    prefix  = formsetObj['prefix']
                    form_kwargs = self.get_form_kwargs(prefix)
                    if self.add:
                        # - CREATE a NEW formset, populating it with any initial data in the request
                        # Saving a NEW item
                        formset = formsetClass(initial=initial, prefix=prefix, form_kwargs=form_kwargs)
                    else:
                        # show the data belonging to the current [obj]
                        qs = self.get_formset_queryset(prefix)
                        if qs == None:
                            formset = formsetClass(prefix=prefix, instance=instance, form_kwargs=form_kwargs)
                        else:
                            formset = formsetClass(prefix=prefix, instance=instance, queryset=qs, form_kwargs=form_kwargs)
                    # Process all the forms in the formset
                    ordered_forms = self.process_formset(prefix, self.request, formset)
                    if ordered_forms:
                        context[prefix + "_ordered"] = ordered_forms
                    # Store the instance
                    formsetObj['formsetinstance'] = formset
                    # Add the formset to the context
                    context[prefix + "_formset"] = formset

        # Put the form and the formset in the context
        context['{}Form'.format(self.prefix)] = frm
        context['instance'] = instance
        context['options'] = json.dumps({"isnew": (instance == None)})

        # Possibly define where a listview is
        classname = self.model._meta.model_name
        listviewname = "{}_list".format(classname)
        try:
            context['listview'] = reverse(listviewname)
        except:
            context['listview'] = reverse('home')

        # Possibly define the admin detailsview
        if instance:
            admindetails = "admin:lingo_{}_change".format(classname)
            try:
                context['admindetails'] = reverse(admindetails, args=[instance.id])
            except:
                pass
        context['modelname'] = self.model._meta.object_name

        # Possibly add to context by the calling function
        context = self.add_to_context(context, instance)

        # Return the calculated context
        return context


class BasicListView(ListView):
    """Basic listview for Lingo"""

    model = None
    template_name = ""
    paginate_by = paginateEntries
    entrycount = 0
    qs = None
    order_cols = []
    order_default = order_cols
    order_heads = []
    sort_order = ""

    def render_to_response(self, context, **response_kwargs):

        authenticated = self.request.user.is_authenticated
        criterion = True    
        # criterion = authenticated
        if not criterion:
            # Do not allow to get a good response
            return nlogin(self.request)
        # Make sure the correct URL is being displayed
        return super(BasicListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        # Get the initial context
        context = super(BasicListView, self).get_context_data(**kwargs)

        # Who am I?
        currentuser = self.request.user

        # Add some information
        context['is_lingo_user'] = user_is_ingroup(self.request, "lingo-user")
        context['is_lingo_editor'] = user_is_ingroup(self.request, "lingo-editor")
        context['is_in_tsg'] = user_is_ingroup(self.request, "radboud-tsg")
        context['authenticated'] = currentuser.is_authenticated

        # Add to the context
        context['order_heads'] = self.order_heads
        context['intro_breadcrumb'] = "{} list".format(self.model._meta.verbose_name)  # "Experiment list"

        # Determine the count 
        context['entrycount'] = self.entrycount #  self.get_queryset().count()
        context['sortOrder'] = self.sort_order

        # Return the total context
        return context

    def get_queryset(self):
        # We are assuming GET
        initial = self.request.GET if self.request.method == "GET" else self.request.POST
        # We now have all the handles, provide the list of them
        qs = self.model.objects.all()

        if len(self.order_heads) > 0:
            # Perform the sorting
            order = self.order_default
            qs, self.order_heads, colnum = make_ordering(qs, initial, order, self.order_cols, self.order_heads)
            self.sort_order = colnum

        # Set the entry count
        self.entrycount = len(qs)

        # Return what we found
        return qs

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class ExperimentListView(BasicListView):
    """Paginated view of Experiment instances"""

    model = Experiment
    template_name = 'lingo/experiment_list.html'
    order_cols = ['home', 'status', 'title', 'created']
    order_heads = [{'name': 'Home', 'order': 'o=1', 'type': 'str'}, 
                   {'name': 'Status', 'order': 'o=2', 'type': 'str'}, 
                   {'name': 'Title', 'order': 'o=3', 'type': 'str'}, 
                   {'name': 'Date', 'order': 'o=4', 'type': 'str'}]


class ExperimentDo(LingoDetails):
    model = Experiment
    mForm = ExperimentForm
    template_name = 'lingo/experiment_do.html'
    template_post = 'lingo/experiment_done.html'
    prefix = "exp"
    prefix_type = "simple"
    title = "ExperimentDo"
    rtype = "html"
    read_only = True
    correct = ["ja", "j", "yes", "y", "true", "t"]
    random_method = "small_set"     # Options: "choose_subset", "small_set"
    permu_method = "permutations"   # options: "combinations", "permutations"
                                    # combinations('ABCD', 2) >> AB AC AD BC BD CD
                                    # permutations('ABCD', 2) >> AB AC AD BA BC BD CA CB CD DA DB DC
    NUM_RESPONSES = 10
    NUM_PERMU = 10
    NUM_TEXTS = 25
    AnswerFormset = formset_factory(AnswerForm, min_num=NUM_RESPONSES, extra=0, )

    def get_context_data(self, **kwargs):
        # Get the initial context
        context = super(ExperimentDo, self).get_context_data(**kwargs)

        # Set the default response type
        self.rtype = "html"

        # Who am I?
        currentuser = self.request.user

        # Add some information
        context['is_lingo_editor'] = user_is_ingroup(self.request, "lingo-editor")
        context['is_in_tsg'] = user_is_ingroup(self.request, "radboud-tsg")
        
        # The name of this current position
        context['intro_breadcrumb'] = "Experiment do"

        # Make sure to exclude the topnav
        context['exclude_topnav'] = "true" 

        # Details of the experiment
        instance = self.object
        context['consent'] = instance.get_consent_markdown()
        context['agreementq'] = "<p>If you agree to participate, click CONTINUE. You will be asked to enter your Amazon Mechanical Turk worker ID and then complete a short survey.</p>" + \
                                "<p>If you do not agree to participate, please click DECLINE.</p>"

        context['exp_data'] = None
        context['exp_valid'] = (instance.status == "val")

        # Indicate that the experiment is not okay for the moment
        context['exp_okay'] = "no"
        context['exp_msg'] = "-"

        # Provide data based on 'home' field of experiment
        if instance.home == "tcpf":
            pfx = "qans"
            # Check: are we receiving answers or is this a request to start?
            if self.request.method == "POST":
                # Change the response type
                self.rtype = "json"
                # Process the answers
                formset = self.AnswerFormset(self.request.POST, prefix=pfx)

                # Walk the formset and process each form
                for form in formset:
                    # Check if there are errors
                    if len(form.errors) == 0:
                        # Process the answers of this form
                        ptcpid = form.cleaned_data['ptcp_id']
                        text1_ans = (form.cleaned_data['answer2'].lower() in self.correct )
                        text2_ans = (form.cleaned_data['answer3'].lower() in self.correct )
                        best_text = form.cleaned_data['answer4']
                        text1_id = form.cleaned_data['answer5']
                        text2_id = form.cleaned_data['answer6']
                        # Get the correct participant
                        participant = Participant.objects.filter(id=ptcpid).first()
                        if participant != None:
                            # It is the correct participant: Get the text objects
                            text1 = Qdata.objects.filter(id=text1_id).first()
                            text2 = Qdata.objects.filter(id=text2_id).first()
                            if text1 != None and text2 != None:
                                # Check if the answers were given correctly
                                text1_corr = (text1.qcorr.lower()  in self.correct)
                                text2_corr = (text2.qcorr.lower()  in self.correct)
                                identified_1 = (text1_ans == text1_corr)
                                identified_2 = (text2_ans == text2_corr)
                                # Find out what the preference was
                                preference_id = text1.id if best_text.lower() == "text1" else text2.id
                                preference = text1.qmeta if best_text.lower() == "text1" else text2.qmeta
                            
                                # combine answer into JSON
                                answer = {}
                                answer['identified1'] = identified_1
                                answer['identified2'] = identified_2
                                answer['preference'] = preference
                                answer['text1'] = text1.qmeta
                                answer['text2'] = text2.qmeta
                                answer['preference_id'] = preference_id
                                answer['text1_id'] = text1.id
                                answer['text2_id'] = text2_id
                                # Create a response object
                                response = Response(experiment=self.object, participant=participant, answer= json.dumps(answer), created=timezone.now())
                                response.save()
                    else:
                        # Pass on the fact that there are errors
                        context['errors'] = form.errors
                        # Break away
                        break

                # Finished preparing POST data
                post_finished = True
                context['exp_okay'] = "yes"
                
            elif self.request.method == "GET":

                # Make sure the participant id is passed on
                ip = "{}_{}".format(self.request.META.get('REMOTE_ADDR'), self.request.META.get('REMOTE_HOST'))
                participant = Participant.objects.filter(ip=ip).first()
                if participant == None:
                    participant = Participant()
                    participant.ip = ip
                    participant.save()
                context['participant_id'] = participant.id

                # Create a formset for the answer forms
                formset = self.AnswerFormset(prefix=pfx)
                context['answer_formset'] = formset
                if self.random_method == "choose_subset":
                    # Get a list of texts
                    qs_texts = Qdata.objects.filter(experiment=instance).values('id', 'qmeta', 'qtext', 'qtopic' )
                    if len(qs_texts) == self.NUM_TEXTS:
                        combi_list = []

                        # Create data: 20 random texts from the 25
                        text_selection = random.sample(list(qs_texts), 2 * self.NUM_RESPONSES)
                        # NOTE: compare the first ten with the second ten
                        # Create a list of text combinations
                        for idx in range(self.NUM_RESPONSES):
                            left = text_selection[idx]
                            right = text_selection[idx+10]
                            # Create and fill a combi object
                            combi = {}
                            # 1: left part
                            combi['left_id'] = left['id']
                            combi['left'] = left['qtext']
                            combi['left_topic'] = left['qtopic']
                            # 2: right part
                            combi['right_id'] = right['id']
                            combi['right'] = right['qtext']
                            combi['right_topic'] = right['qtopic']
                            # 3: Add the form from the formset
                            form = formset[idx]
                            combi['form'] = form
                            # Add this to the combi=list
                            combi_list.append(combi)
                        # Make the combi list available
                        context['exp_parts'] = combi_list
                elif self.random_method == "small_set":
                    # Create a list of all permutations
                    qs_texts = Qdata.objects.filter(experiment=instance, include='y').values('id', 'qmeta', 'qtext', 'qtopic' )
                    if len(qs_texts) == self.NUM_PERMU:
                        combi_list = []
                        if self.permu_method == "permutations":
                            # Create all permutations of TWO texts
                            pms = [comb for comb in itertools.permutations(qs_texts,2)]
                        elif self.permu_method == "combinations":
                            # Create all non-repeated sorted combinations
                            pms = [comb for comb in itertools.combinations(qs_texts,2)]

                        # Choose NUM_RESPONSES random combinations from  the total
                        text_selection = random.sample(pms, self.NUM_RESPONSES)
                        for idx in range(self.NUM_RESPONSES):
                            left = text_selection[idx][0]
                            right = text_selection[idx][1]
                            # Create and fill a combi object
                            combi = {}
                            # 1: left part
                            combi['left_id'] = left['id']
                            combi['left'] = left['qtext']
                            combi['left_topic'] = left['qtopic']
                            # 2: right part
                            combi['right_id'] = right['id']
                            combi['right'] = right['qtext']
                            combi['right_topic'] = right['qtopic']
                            # 3: Add the form from the formset
                            form = formset[idx]
                            combi['form'] = form
                            # Add this to the combi=list
                            combi_list.append(combi)

                        # Make the combi list available
                        context['exp_parts'] = combi_list
                        # Getting here means that all is in order
                        context['exp_okay'] = "yes"
                    else:
                        context['exp_msg'] = "The number of selected questions is not correct. It should be: {}".format(self.NUM_PERMU)
        else:
            context['exp_msg'] = "Experiment of type '{}' has not been programmed in the code [ExperimentDo] yet".format(instance.home)

        # The page to return to
        context['prevpage'] = reverse("exp_list")

        # Return the total context
        return context


class ExperimentDetails(LingoDetails):
    model = Experiment
    mForm = ExperimentForm
    template_name = 'lingo/experiment_details.html'
    template_post = template_name
    prefix = "exp"
    prefix_type = "simple"
    title = "ExperimentDetails"
    rtype = "html"
    mainitems = []

    def after_new(self, form, instance):
        """Action to be performed after adding a new item"""

        # Set a redirect page
        if instance != None:
            # Make sure we do a page redirect
            self.newRedirect = True
            self.redirectpage = reverse('exp_details', kwargs={'pk': instance.id})
        return True, ""

    def add_to_context(self, context, instance):
        # The name of this current position
        context['intro_breadcrumb'] = "Experiment details"

        # The page to return to
        context['prevpage'] = reverse('exp_list')

        if instance:
            # The related objects are the list of question belonging to this experiment
            related_objects = []

            # This tag in: sermon.notes
            questions = dict(title='Questions that are part of this experiment',
                             addbutton='Add question data',
                             addurl=reverse('qdata_add'),
                             type="qdata")
        
            # Show the list of sermons that contain this tag
            qs = instance.experiment_qdatas.all().order_by('qmeta')
            if qs.count() > 0:
                rel_list =[]
                for item in qs:
                    rel_item = []
                    rel_item.append({'value': item.qmeta, 'title': 'View this question', 'link': reverse('qdata_details', kwargs={'pk': item.id})})
                    rel_item.append({'value': item.qtopic})
                    rel_item.append({'value': item.qtext})
                    rel_item.append({'value': item.get_include_display()})
                    rel_list.append(rel_item)
                questions['rel_list'] = rel_list
                questions['columns'] = ['Meta', 'Topic', 'Text', 'Include']
            # Add the questions - no matter how many there are
            related_objects.append(questions)

            context['related_objects'] = related_objects
        # Return the total context
        return context


class ExperimentEdit(BasicLingo):
    MainModel = Experiment
    template_name = 'lingo/experiment_edit.html'
    title = "Experiment"
    afternewurl = ""
    prefix = "exp"
    need_authentication = False
    form_objects = [{'form': ExperimentForm, 'prefix': prefix, 'readonly': False}]

    def add_to_context(self, context):
        # Who am I?
        currentuser = self.request.user

        # Add some information
        context['is_lingo_editor'] = user_is_ingroup(self.request, "lingo-editor")
        context['is_in_tsg'] = user_is_ingroup(self.request, "radboud-tsg")
        context['afterdelurl'] = reverse("exp_list")

        # Return the total context
        return context

    def before_save(self, prefix, request, instance = None, form = None):
        # Who am I?
        currentuser = self.request.user
        # Adapt the history of the instance
        if instance != None:
            # Any adaptations should happen here

            # Signal that saving is needed
            return False    # Change into "TRUE" if changes are made


class ExperimentDownload(BasicLingo):
    MainModel = Experiment
    template_name = "lingo/download_status.html"
    qcTarget = 1
    dtype = "csv"           # downloadtype
    basket = None
    action = "download"

    def custom_init(self):
        """Calculate stuff"""
        
        dt = self.qd['downloadtype']
        if dt != None and dt != '':
            self.dtype = dt

    def add_to_context(self, context):
        # Provide search URL and search name
        context['exp_edit_url'] = reverse("exp_edit", kwargs={"object_id": self.obj.id})
        context['exp_name'] = self.objname
        context['basket'] = self.basket
        return context

    def get_data(self, prefix, dtype):
        """Get the experiment results as CSV"""

        data = ""
        lCsv = []
        oErr = ErrHandle()
        headers = ['ParticipantId', 'Text1', 'Text2', 'Identified1', 'Identified2', 'Preference', 'Education', 'Age', 'Gender', 'Email', 'Start', 'Finish']
        try:
            # Start with the header
            oLine = "\t".join(headers)
            lCsv.append(oLine)

            # Get a list of all answers given to this experiment
            qs = Response.objects.filter(experiment=self.obj)
            for obj in qs:
                participant = obj.participant
                answer = json.loads( obj.answer)

                identified1 = True
                if 'identified1' in answer:
                    identified1 = answer['identified1']
                elif 'identified' in answer:
                    identified1 = answer['identified']
                identified2 = True
                if 'identified2' in answer:
                    identified2 = answer['identified2']
                elif 'identified' in answer:
                    identified2 = answer['identified']

                education = participant.get_edu()

                sLine = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                    participant.id, answer['text1'], answer['text2'], identified1, identified2, 
                    answer['preference'], education, participant.age, participant.gender, participant.email, 
                    participant.created, obj.created)
                lCsv.append(sLine)

            # REturn the whole
            return "\n".join(lCsv)
        except:
            sMsg = oErr.get_error_message()
            oErr.DoError("ExperimentDownload get_csv")
            data = ""

        return data
    

class ParticipantDetails(BasicLingo):
    MainModel = Participant
    template_name = 'lingo/participant.html'
    title = "Participant"
    need_authentication = False
    ptcpfields = ""
    form_objects = [{'form': ParticipantForm, 'prefix': 'ptcp', 'readonly': False}]

    def is_custom_valid(self, prefix, form):
        """Validate the participant answers to the questions"""

        bValid = True

        # Iterate over the necessary fields
        for item in self.ptcpfields:
            if (form.cleaned_data[item] == None or form.cleaned_data[item] == "") and (item != "email"):
                bValid = False
                self.arErr.append("Hoe zit het met {}?".format(form.fields[item].label))
            elif item == "age":
                sAge = form.cleaned_data[item]
                try:
                    age = int(sAge)
                    if age <= 10:
                        self.arErr.append("Sorry, u bent te jong voor deelname")
                        bValid = False
                    elif age > 110:
                        self.arErr.append("Sorry, u bent te oud voor deelname")
                        bValid = False
                except:
                    self.arErr.append("Wat voor leeftijd?")
                    bValid = False
            elif item == "edu":
                # Double check if an alternative has been provided
                eduother = form.cleaned_data['eduother']
                edu = form.cleaned_data['edu']
                if edu == "g7" and eduother == "":
                    self.arErr.append("Welk schooltype geeft u les?")
                    bValid = False

        return bValid

    def custom_init(self):
        # Find out which participant fields need to be shown
        ptcpfields = []
        if 'experiment_id' in self.qd:
            experiment = Experiment.objects.filter(id=self.qd['experiment_id']).first()
            if experiment != None:
                sFields = experiment.ptcpfields
                if sFields != None and sFields != "":
                    try:
                        ptcpfields = json.loads(sFields)
                    except:
                        pass
        # if it is empty, put all fields in there
        if len(ptcpfields) == 0:
            ptcpfields = ['age','gender', 'engfirst', 'lngfirst', 'lngother', 'edu']
        self.ptcpfields = ptcpfields
        return True

    def add_to_context(self, context):
        # make sure to add the ID for this participant to what we return
        context['participant_id'] = ""
        if 'instance' in self.form_objects[0]:
            instance = self.form_objects[0]['instance']
            if instance != None:
                context['participant_id'] = instance.id
            # TODO: See if we need to add any warning message

        # Find out which participant fields need to be shown
        if self.ptcpfields != "":
            context['ptcpfields'] = self.ptcpfields

        if 'experiment_id' in self.qd:
            context['experiment_id'] = self.qd['experiment_id']

        return context


class QdataListView(BasicListView):
    model = Qdata
    listform = QdataListForm
    prefix = "qdata"
    template_name = 'lingo/qdata_list.html'
    order_cols = ['qmeta', 'qtopic', 'qtext', 'include']
    order_heads = [{'name': 'Meta', 'order': 'o=1', 'type': 'str'}, 
                   {'name': 'Topic', 'order': 'o=2', 'type': 'str'}, 
                   {'name': 'Text', 'order': 'o=3', 'type': 'str'}, 
                   {'name': 'Include', 'order': 'o=4', 'type': 'str'}]


class QdataDetailsView(LingoDetails):
    model = Qdata
    mForm = None
    template_name = 'lingo/generic_details.html'  # 'seeker/sermon_view.html'
    prefix = ""
    title = "QuestionDataDetails"
    rtype = "html"
    mainitems = []

    def add_to_context(self, context, instance):
        context['mainitems'] = [
            {'type': 'plain', 'label': "Question metadata:", 'value': instance.qmeta},
            {'type': 'plain', 'label': "Question data:", 'value': instance.qtext},
            {'type': 'plain', 'label': "Topic:", 'value': instance.qtopic},
            {'type': 'plain', 'label': "Suggested topic:", 'value': instance.qsuggest},
            {'type': 'plain', 'label': "Topic response:", 'value': instance.qcorr},
            {'type': 'plain', 'label': "Include:", 'value': instance.get_include_display()}
            ]

        # Adapt the 'listview' to point to the details view of the associated experiment
        context['listview'] = reverse('exp_details', kwargs={'pk': instance.experiment.id})

        # Provide the correct breadcrumbs
        breadcrumbs = []
        breadcrumbs.append(dict(name="Home", url=reverse('lingo_home')))
        breadcrumbs.append(dict(name="Experiments", url=reverse('exp_list')))
        breadcrumbs.append(dict(name=instance.experiment.title, url=reverse('exp_details', kwargs={'pk': instance.experiment.id})))
        breadcrumbs.append(dict(name=instance.qmeta, url=""))
        context['breadcrumbs'] = breadcrumbs

        # Return the context we have made
        return context

