"""
Definition of views for the DOC app.
"""

import sys
import json
import re
import requests
import urllib.parse
from django import template
from django.db import models, transaction
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic import ListView, View
from datetime import datetime
import pytz
from django.utils import timezone

# Application-specific
from cesar.settings import APP_PREFIX
from cesar.utils import ErrHandle
from cesar.browser.models import Status
from cesar.browser.views import nlogin, user_is_authenticated, user_is_ingroup
from cesar.seeker.views import csv_to_excel
from cesar.tsg.models import TsgInfo, TsgHandle, get_crpp_date
from cesar.tsg.forms import TsgHandleForm


paginateEntries = 15

# General purpose functions
def get_handle_info(handle_url, handle_user, handle_pw, handle_code=""):
    """Use GET to retrieve one bit of Handle info"""

    # Set the correct URL
    url = handle_url
    if handle_code != "":
        if url[-1] != "/": url = url + "/"
        url = url + handle_code
    # Set up authorisation values
    auth_values = (handle_user, handle_pw)
    # We want to receive JSON
    headers = {'Accept': 'application/json'}
    # Default reply
    oBack = {}
    # Get the data from the CRPP api
    try:
        r = requests.get(url, auth=auth_values, headers=headers)
    except:
        # Getting an exception here probably means that the back-end is not reachable (down)
        oBack['status'] = 'error'
        oBack['code'] = "get_handle_info(): The back-end server (crpp) cannot be reached. Is it running? {}".format(
            get_exc_message())
        return oBack
    # Action depends on what we receive
    if r.status_code == 200:
        # Convert to JSON
        reply = json.loads(r.text.replace("\t", " "))
        # Get the [contents] part
        oBack['contents'] = reply
        oBack['status'] = 'ok'
    else:
        oBack['status'] = 'error'
        oBack['code'] = r.status_code
    # REturn what we have
    return oBack

def get_handle_target(request, handle_code):
    """Try to get the URL belonging to this code"""

    # Default reply
    oBack = {}

    # Check which groups this person belongs to
    if user_is_ingroup(request, "radboud-tsg"):
        # Get Handle credentials
        handle_user = TsgInfo.get_value("handle_user")
        handle_pw = TsgInfo.get_value("handle_pw")
        handle_url = TsgInfo.get_value("handle_url")
        # Set the correct URL
        if handle_code != "":
            url = handle_url
            if url[-1] != "/": url = url + "/"
            url = url + handle_code
            # Set up authorisation values
            auth_values = (handle_user, handle_pw)
            # We want to receive JSON
            headers = {'Accept': 'application/json'}

            # Get the data from the CRPP api
            try:
                r = requests.get(url, auth=auth_values, headers=headers)
            except:
                # Getting an exception here probably means that the back-end is not reachable (down)
                oBack['status'] = 'error'
                oBack['code'] = "get_handle_info(): The back-end server (crpp) cannot be reached. Is it running? {}".format(
                    get_exc_message())
                return oBack
            # Action depends on what we receive
            if r.status_code == 200 or r.status_code == 201:
                # Convert to JSON
                info = json.loads(r.text.replace("\t", " "))

                # Get the information from the handle
                url = ""
                date_obj = None
                for item in info:
                    if item['type'].lower() == "url":
                        url = item['parsed_data'] 
                        timestamp = item['timestamp']   # E.G: 2017-10-25T07:38:26Z
                        date_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
                        date_obj = pytz.timezone("UTC").localize(date_obj)
                        break
                if url == "":
                    # Could not get the stuff
                    oBack['msg'] = "Cannot find URL for code {}".format(handle_code)
                    oBack['status'] = 'error'
                else:
                    # Success: we've got it
                    oBack['contents'] = url
                    oBack['info'] = json.dumps(info)
                    oBack['status'] = 'ok'

            else:
                oBack['status'] = 'error'
                oBack['code'] = r.status_code
        else:
            oBack['status'] = 'error'
            oBack['msg'] = "Obligatory handle PID missing"

    else:
        oBack['status'] = 'error'
        oBack['msg'] = "Unauthorised"

    # REturn what we have
    return oBack


def change_handle_info(request, handle_code, target_url):
    """Use PUT to change an existing handle"""

    # Default reply
    oBack = {}

    # Check which groups this person belongs to
    if user_is_ingroup(request, "radboud-tsg"):
        # Get Handle credentials
        handle_user = TsgInfo.get_value("handle_user")
        handle_pw = TsgInfo.get_value("handle_pw")
        handle_url = TsgInfo.get_value("handle_url")
        # Set the correct URL
        if handle_code != "" and target_url != "":
            url = handle_url
            if url[-1] != "/": url = url + "/"
            url = url + handle_code
            # Set up authorisation values
            auth_values = (handle_user, handle_pw)
            # We must send the data
            oInfo = {}
            oInfo['type'] = "URL"
            oInfo['parsed_data'] = target_url
            data = [ oInfo ]
            # We want to receive JSON
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

            # Get the data from the CRPP api
            try:
                r = requests.put(url, data=json.dumps(data), auth=auth_values, headers=headers)
            except:
                # Getting an exception here probably means that the back-end is not reachable (down)
                oBack['status'] = 'error'
                oBack['code'] = "get_handle_info(): The back-end server (crpp) cannot be reached. Is it running? {}".format(
                    get_exc_message())
                return oBack
            # Action depends on what we receive
            if r.status_code == 200 or r.status_code == 201:
                # Convert to JSON
                reply = json.loads(r.text.replace("\t", " "))
                # Get the [contents] part
                oBack['contents'] = reply
                oBack['status'] = 'ok'
            elif r.status_code == 204:
                # This means: No-Content: The local name already exists , and instead of creating a new one you’ve just updated the values of an existing one.
                oBack['contents'] = "Successfully changed"
                oBack['status'] = 'ok'
            else:
                oBack['status'] = 'error'
                oBack['code'] = r.status_code
        else:
            oBack['status'] = 'error'
            oBack['msg'] = "Obligatory handle PID missing"

    else:
        oBack['status'] = 'error'
        oBack['msg'] = "Unauthorised"

    # REturn what we have
    return oBack

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

def get_exc_message():
    exc_type, exc_value = sys.exc_info()[:2]
    sMsg = "Handling {} exception with message '{}'".format(exc_type.__name__, exc_value)
    return sMsg

# Views belonging to the Cesar TSG handle processing app.
def tsgsync(request):
    """Synchronize TSG handles."""

    oErr = ErrHandle()
    try:
        # Make sure this is a HttpRequest
        assert isinstance(request, HttpRequest)
    
        # Basic authentication
        if not user_is_authenticated(request):
            return nlogin(request)

        # Check which groups this person belongs to
        if user_is_ingroup(request, "radboud-tsg"):
            # Get Handle credentials
            handle_user = TsgInfo.get_value("handle_user")
            handle_pw = TsgInfo.get_value("handle_pw")
            handle_url = TsgInfo.get_value("handle_url")

            msg_lst = []
            # Validate
            if handle_pw == None or handle_pw == "":
                msg_lst.append( "Password is not defined")
            if handle_url == None or handle_url == "":
                msg_lst.append("Handle URL is not defined")
            if handle_user == None or handle_user == "":
                msg_lst.append("Handle User is not defined")
            if len(msg_lst) ==0:
                # Try to get all defined handles
                oHandles = get_handle_info(handle_url, handle_user, handle_pw)
                if oHandles['status'] == "error":
                    msg_lst.append("Request returns code {} for handle-list".format(oHandles['code']))
                else:
                    handle_lst = oHandles['contents']
                    # Compare this list with the handles we already have
                    for handle_code in handle_lst:
                        oBack = get_handle_info(handle_url, handle_user, handle_pw, handle_code)
                        if oBack['status'] == "ok":
                            # Get the information from the handle
                            info = oBack['contents']
                            url = ""
                            date_obj = None
                            for item in info:
                                if item['type'].lower() == "url":
                                    url = item['parsed_data'] 
                                    timestamp = item['timestamp']   # E.G: 2017-10-25T07:38:26Z
                                    date_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
                                    date_obj = pytz.timezone("UTC").localize(date_obj)
                                    break
                            if url == "":
                                msg_lst.append("Cannot find URL for code {}".format(handle_code))
                            else:
                                # Try to get the handle from the database
                                obj = TsgHandle.objects.filter(code=handle_code).first()
                                if obj == None:
                                    # Add the handle
                                    TsgHandle.add_handle(handle_code, url, info=info)
                                else:
                                    bNeedSaving = False
                                    # Check and possibly update the handle
                                    if obj.url != url:
                                        # The URL has changed
                                        obj.url = url
                                        obj.info = json.dumps(info)
                                        bNeedSaving = True
                                    elif obj.info == None or obj.info == "" or obj.info == "[]":
                                        obj.info = json.dumps(info)
                                        bNeedSaving = True
                                    # At any rate: check the date
                                    if obj.created != date_obj:
                                        history = obj.history
                                        if history == None or history == "": history = []
                                        if isinstance(history, str):
                                            history = json.loads(history)
                                        if date_obj == None:
                                            # First creation
                                            history.append("Created at {} by {}".format(get_crpp_date(get_current_datetime()), handle_user))
                                        else:
                                            # Change
                                            history.append("Changed at {} by {}".format(get_crpp_date(get_current_datetime()), handle_user))
                                        obj.history = json.dumps(history)
                                        obj.created = date_obj
                                        bNeedSaving = True
                            
                                    # Save if needed
                                    if bNeedSaving:
                                        obj.save()

                        else:
                            msg_lst.append("Request returns code {} for handle {}".format(oBack['code'], handle_code))
    except:
        msg = oErr.get_error_message()
        oErr.DoError("tsgsync")

    # Return by rendering the listview of TsgHandle
    return redirect('tsg_list')

class BasicPart(View):
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
                    sDbName = "tsg_{}_{}.{}".format(modelname, obj_id, self.dtype)
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
                        response = csv_to_excel(sData, response)
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
        if not request.user.is_authenticated:
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


class TsgDetails(DetailView):
    """Extension of the normal DetailView class for TSG HANDLE"""

    template_name = ""      # Template for GET
    template_post = ""      # Template for POST
    formset_objects = []    # List of formsets to be processed
    afternewurl = ""        # URL to move to after adding a new item
    prefix = ""             # The prefix for the one (!) form we use
    previous = None         # Start with empty previous page
    title = ""              # The title to be passedon with the context
    rtype = "json"          # JSON response (alternative: html)
    prefix_type = ""        # Whether the adapt the prefix or not ('simple')
    mForm = None            # Model form
    add = False             # Are we adding a new record or editing an existing one?

    def get(self, request, pk=None, *args, **kwargs):
        # Initialisation
        data = {'status': 'ok', 'html': '', 'statuscode': ''}
        # always do this initialisation to get the object
        self.initializations(request, pk)
        if not request.user.is_authenticated:
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
        if request.user.is_authenticated:
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
            # response = self.render_to_response(self.template_post, context)
            response = render_to_string(self.template_post, context, request)
            response = response.replace("\ufeff", "")
            data['html'] = response
        else:
            data['html'] = "(No authorization)"
            data['status'] = "error"

        # Return the response
        return JsonResponse(data)

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
        context = super(TsgDetails, self).get_context_data(**kwargs)

        # Check this user: is he allowed to UPLOAD data?
        context['authenticated'] = user_is_authenticated(self.request)

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
        oErr = ErrHandle()

        # prefix = self.prefix
        if self.prefix_type == "":
            id = "n" if instance == None else instance.id
            prefix = "{}-{}".format(self.prefix, id)
        else:
            prefix = self.prefix

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

        # Possibly add to context by the calling function
        context = self.add_to_context(context, instance)

        # Return the calculated context
        return context


class TsgHandleListView(ListView):
    """Paginated view of TsgHandle instances"""

    model = TsgHandle
    template_name = 'tsg/tsghandle_list.html'
    paginate_by = paginateEntries
    entrycount = 0
    qs = None
    order_cols = ['code', 'url', 'created']
    order_heads = [{'name': 'Handle', 'order': 'o=1', 'type': 'str'}, 
                   {'name': 'URL', 'order': 'o=2', 'type': 'str'}, 
                   {'name': 'Date', 'order': 'o=3', 'type': 'str'}]

    def render_to_response(self, context, **response_kwargs):

        if not self.request.user.is_authenticated:
            # Do not allow to get a good response
            return nlogin(self.request)
        # Make sure the correct URL is being displayed
        return super(TsgHandleListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        # Get the initial context
        context = super(TsgHandleListView, self).get_context_data(**kwargs)

        # Who am I?
        currentuser = self.request.user

        # Add some information
        context['is_in_tsg'] = user_is_ingroup(self.request, "radboud-tsg")
        context['authenticated'] = currentuser.is_authenticated

        # Add to the context
        context['order_heads'] = self.order_heads
        # context['msg_lst'] = msg_lst
        context['intro_breadcrumb'] = "TSG Handle list"

        # Determine the count 
        context['entrycount'] = self.entrycount #  self.get_queryset().count()

        # Return the total context
        return context

    def get_queryset(self):
        # We now have all the handles, provide the list of them
        qs = TsgHandle.objects.all()
        # Perform the sorting
        order = [Lower('url')]
        initial = self.request.GET
        bAscending = True
        sType = 'str'
        if 'o' in initial:
            order = []
            iOrderCol = int(initial['o'])
            bAscending = (iOrderCol>0)
            iOrderCol = abs(iOrderCol)
            order.append(Lower( self.order_cols[iOrderCol-1]))
            sType = self.order_heads[iOrderCol-1]['type']
            if bAscending:
                self.order_heads[iOrderCol-1]['order'] = 'o=-{}'.format(iOrderCol)
            else:
                # order = "-" + order
                self.order_heads[iOrderCol-1]['order'] = 'o={}'.format(iOrderCol)
        if sType == 'str':
            qs = qs.order_by(*order)
        else:
            qs = qs.order_by(*order)
        # Possibly reverse the order
        if not bAscending:
            qs = qs.reverse()

        # Set the entry count
        self.entrycount = len(qs)

        # Return what we found
        return qs


class TsgHandleDetails(TsgDetails):
    model = TsgHandle
    mForm = TsgHandleForm
    template_name = 'tsg/tsghandle_details.html'
    prefix = "tsghandle"
    prefix_type = "simple"
    title = "TsgHandleDetails"
    rtype = "html"

    def get_context_data(self, **kwargs):
        # Get the initial context
        context = super(TsgHandleDetails, self).get_context_data(**kwargs)

        # Who am I?
        currentuser = self.request.user

        # Add some information
        context['is_in_tsg'] = user_is_ingroup(self.request, "radboud-tsg")
        
        # The name of this current position
        context['intro_breadcrumb'] = "TSG Handle details"

        # The page to return to
        context['prevpage'] = reverse('tsg_list')

        # Return the total context
        return context


class TsgHandleEdit(BasicPart):
    MainModel = TsgHandle
    template_name = 'tsg/tsghandle_edit.html'
    title = "TsgHandle"
    afternewurl = ""
    prefix = "tsghandle"
    form_objects = [{'form': TsgHandleForm, 'prefix': prefix, 'readonly': False}]

    def add_to_context(self, context):
        # Who am I?
        currentuser = self.request.user

        # Add some information
        context['is_in_tsg'] = user_is_ingroup(self.request, "radboud-tsg")
        context['afterdelurl'] = reverse('tsg_list')

        # Return the total context
        return context

    def before_save(self, prefix, request, instance = None, form = None):
        # Who am I?
        currentuser = self.request.user
        # Adapt the history of the instance
        if instance != None:
            # Get current history
            history = json.loads(instance.history)
            obj = self.MainModel.objects.filter(id=instance.id).first()
            if obj != None and obj.url != instance.url:
                # Actually try make the change to the API
                oBack = change_handle_info(request, instance.code, instance.url)
                if oBack['status'] == "ok":
                    # Try to read back the URL
                    oBack = get_handle_target(request, instance.code)
                    if oBack['status'] == "ok":
                        target_url = oBack['contents']
                        if target_url == instance.url:
                            # Add a new element to the history
                            history.append("Changed URL on {} by {} from {} into {}".format(
                                get_crpp_date(get_current_datetime()), currentuser, obj.url, instance.url))
                            # We may get an update on the information
                            if 'info' in oBack:
                                instance.info = oBack['info']
                        else:
                            # Something went wrong after all
                            history.append("Could not change to url [{}] due to: {}".format(instance.url, oBack['msg']))
                            instance.url = obj.url
                    else:
                        # Something went wrong after all
                        history.append("Could not change to url [{}] due to: {}".format(instance.url, oBack['msg']))
                        instance.url = obj.url
                else:
                    # Something went wrong after all
                    history.append("Could not change to url [{}] due to: {}".format(instance.url, oBack['msg'])) 
                    instance.url = obj.url

            else:
                # Add a new element to the history
                history.append("Changed notes on {} by {}.".format(get_crpp_date(get_current_datetime()), currentuser))
            # Put it back as string
            instance.history = json.dumps(history)
            # Signal that saving is needed
            return True

    def before_delete(self, prefix = None, instance = None):
        bResult = True
        oErr = ErrHandle()
        try:
            # Delete the 
            pass
        except:
            msg = oErr.get_error_message()
            oErr.DoError("TsgHandleEdit/before_delete")
        # Return what is expected 
        return bResult
