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
from cesar.basic.views import BasicDetails, BasicList, BasicPart
from cesar.browser.models import Status
from cesar.browser.views import nlogin, user_is_authenticated, user_is_ingroup
from cesar.seeker.views import csv_to_excel
from cesar.tsg.models import TsgInfo, TsgHandle, TsgStatus, get_crpp_date
from cesar.tsg.forms import TsgHandleForm


paginateEntries = 15

# ====================== General purpose functions ===========================
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

# =============== Handle creation and consulting =============================


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

def get_handle_code(request, targeturl):
    """Check if there is a handle for the targeturl"""

    # Default reply
    oBack = {}
    oErr = ErrHandle()
    try:

        # Check which groups this person belongs to
        if user_is_ingroup(request, "radboud-tsg"):
            # Get Handle credentials
            handle_user = TsgInfo.get_value("handle_user")
            handle_pw = TsgInfo.get_value("handle_pw")
            handle_url = TsgInfo.get_value("handle_url")
            # Set the correct URL
            if targeturl != "":
                url = handle_url
                if url[-1] != "/": url = url + "/"
                url = "{}?URL={}".format(url, targeturl)
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
                    oBack['code'] = "get_handle_code(): The back-end server (crpp) cannot be reached. Is it running? {}".format(
                        get_exc_message())
                    return oBack
                # Action depends on what we receive
                if r.status_code == 200 or r.status_code == 201:
                    # Convert to JSON
                    info = json.loads(r.text.replace("\t", " "))

                    # Get the information from the handle
                    code = ""
                    url = ""
                    if len(info) == 1:
                        # We have the exact code
                        code = info[0]
                    elif len(info) > 1:
                        # Hmmm. Take the last code?
                        code = info[-1]

                    if code == "":
                        oBack['status'] = "error"
                        oBack['msg'] = "Cannot find the code for URL {}".format(targeturl)
                    else:
                        # Okay, we have the code, now get the info
                        oBack = get_handle_target(request, code)
                        # Note: this yields contents, info and status

                        # Success: we've got it
                        oBack['code'] = code

                else:
                    oBack['status'] = 'error'
                    oBack['code'] = r.status_code
            else:
                oBack['status'] = 'error'
                oBack['msg'] = "Obligatory handle PID missing"

        else:
            oBack['status'] = 'error'
            oBack['msg'] = "Unauthorised"
    except:
        msg = oErr.get_error_message()
        oErr.DoError("get_handle_code")

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

def create_handle_info(request, target_url):
    """Use POST to create a new handle within prefix TSG"""

    # Default reply
    oBack = dict(status="ok", msg = "")

    # Check which groups this person belongs to
    if user_is_ingroup(request, "radboud-tsg"):
        # Get Handle credentials
        handle_user = TsgInfo.get_value("handle_user")
        handle_pw = TsgInfo.get_value("handle_pw")
        handle_url = TsgInfo.get_value("handle_url")
        handle_code = ""
        # Set the correct URL
        if target_url != "":
            # This is the URL we need to use for the request
            url = "{}?prefix=TSG".format( handle_url)
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
                r = requests.post(url, data=json.dumps(data), auth=auth_values, headers=headers)
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
                oBack['info'] = reply
                oBack['code'] = reply['epic-pid']
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

def handle_delete(request, handle_code):
    """Delete the handle indicated"""

    oBack = dict(status="error", msg="")
    oErr = ErrHandle()
    try:
        # Check which groups this person belongs to
        if user_is_ingroup(request, "radboud-tsg"):
            # double check
            if not handle_code is None and handle_code != "":
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
                    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

                    # Get the data from the CRPP api
                    try:
                        r = requests.delete(url, auth=auth_values, headers=headers)
                    except:
                        # Getting an exception here probably means that the back-end is not reachable (down)
                        oBack['status'] = 'error'
                        oBack['code'] = "handle_delete(): The back-end server (crpp) cannot be reached. Is it running? {}".format(
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

                # Fill in the values
                oBack['status'] = "ok"
        else:
            oBack['status'] = 'error'
            oBack['msg'] = "Unauthorised"
    except:
        msg = oErr.get_error_message()
        oBack['msg'] = msg
        oBack['status'] = "error"
        oErr.DoError("handle_delete")

    return oBack


# ============== Views belonging to the Cesar TSG handle processing app ======


def tsgsync(request):
    """Synchronize TSG handles."""

    oErr = ErrHandle()
    handle_lst = []
    response = None
    infoval = None
    data = None
    try:
        # Make sure this is a HttpRequest
        assert isinstance(request, HttpRequest)
    
        # Basic authentication
        if not user_is_authenticated(request) or request.method.lower() != "post":
            return nlogin(request)

        # Check which groups this person belongs to
        if user_is_ingroup(request, "radboud-tsg"):

            # Get the mode
            qd = request.POST
            mode = qd.get("mode")

            # Get the infoval
            infoval = TsgInfo.get_value("tsgsync")
            if not infoval is None:
                if infoval == "busy" and mode == "start":
                    # Provide message that we are busy
                    data = dict(status="error", msg="Synchronization is busy")
                    response = JsonResponse(data)

                    # FOR NOW: just reset the status to 'ok'
                    infoval = "ok"
                elif infoval == "reset":
                    TsgInfo.set_value("tsgsync", "ok")
                    # Provide message that we are busy
                    data = dict(status="error", msg="Reset done")
                    response = JsonResponse(data)

            # We can only continue if the infovalue is okay
            if infoval is None or infoval in ["ok", "busy", "reset", "ready"]:

                # Get Handle credentials
                handle_user = TsgInfo.get_value("handle_user")
                handle_pw = TsgInfo.get_value("handle_pw")
                handle_url = TsgInfo.get_value("handle_url")

                del_status = TsgStatus.objects.filter(abbr="del").first()

                # Mode: can be 'start', 'update', 'finish'
                if mode == "start":

                    msg_lst = []
                    bReset = False
                    # Validate
                    if handle_pw is None or handle_pw == "":
                        msg_lst.append( "Password is not defined")
                    if handle_url is None or handle_url == "":
                        msg_lst.append("Handle URL is not defined")
                    if handle_user is None or handle_user == "":
                        msg_lst.append("Handle User is not defined")
                    if len(msg_lst) == 0:
                        # Try to get all defined handles
                        oHandles = get_handle_info(handle_url, handle_user, handle_pw)
                        if oHandles['status'] == "error":
                            msg_lst.append("Request returns code {} for handle-list".format(oHandles['code']))
                        else:
                            handle_lst = oHandles['contents']

                            # Set the infoval to 'busy'
                            obj_status = TsgInfo.set_value("tsgsync", "busy")
                            obj_status.history_clear()

                            # Compare this list with the handles we already have
                            for handle_code in handle_lst:
                                # Always first check for a possible reset
                                infoval = TsgInfo.get_value("tsgsync")
                                if infoval == "reset":
                                    TsgInfo.set_value("tsgsync", "ok")
                                    # Provide message that we are busy
                                    data = dict(status="error", msg="Reset done")
                                    response = JsonResponse(data)
                                    bReset = True
                                    obj_status.history_add("Reset by user")
                                    # Get out of the loop
                                    break

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
                                        msg = "Cannot find URL for code {}".format(handle_code)
                                        oErr.Status("tsgsync cannot find URL for handle: {}".format(handle_code))
                                        msg_lst.append(msg)
                                        obj_status.history_add(msg)
                                    else:
                                        # Try to get the handle from the database
                                        obj = TsgHandle.objects.filter(code=handle_code).first()
                                        if obj == None:
                                            msg = "tsgsync add handle: {}, {}".format(handle_code, url)
                                            oErr.Status(msg)
                                            # Add the handle
                                            TsgHandle.add_handle(handle_code, url, info=info)
                                            # Keep track of where we are
                                            obj_status.history_add(msg)
                                        else:
                                            msg = "tsgsync existing handle: {}, {}".format(handle_code, url)
                                            oErr.Status(msg)
                                            obj_status.history_add(msg)

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
                                                    msg = "Created at {} by {}".format(get_crpp_date(get_current_datetime()), handle_user)
                                                else:
                                                    # Change
                                                    msg = "Changed at {} by {}".format(get_crpp_date(get_current_datetime()), handle_user)
                                                history.append(msg)
                                                obj.history = json.dumps(history)
                                                obj.created = date_obj
                                                bNeedSaving = True

                                                obj_status.history_add(msg)
                            
                                            # Save if needed
                                            if bNeedSaving:
                                                obj.save()

                                else:
                                    oErr.Status("tsgsync error handle: {}, {}".format(handle_code, oBack['code']))
                                    msg_lst.append("Request returns code {} for handle {}".format(oBack['code'], handle_code))
                                    obj_status.history_set(msg_lst)

                    # Is there a list of handles?
                    if not bReset and len(handle_lst) > 0:
                        # Then we walk all the TsgHandle object to see if there are handles not in this list
                        #  (unless they already have the status "del")
                        for obj in TsgHandle.objects.exclude(tsgstatus__abbr="del"):
                            code = obj.code
                            if not code in handle_lst:
                                oErr.Status("Removing code, since there is no PID for it anymore: [{}] tsghandle={}".format(code, obj.id))
                                # There is a code that should be deleted from the TsgHandle
                                lst_history = json.loads(obj.history)
                                msg = "Removed code, since there is no PID for it anymore: [{}]".format(code)
                                lst_history.append(msg)
                                obj.history = json.dumps(lst_history)
                                obj.code = ""
                                obj.tsgstatus = del_status
                                # obj.status = "del"
                                obj.save()

                                # Add to history
                                obj_status.history_add(msg)

                    # Once we are ready, we should give the message that we are
                    TsgInfo.set_value("tsgsync", "ready")
                    # Get the total history
                    obj_status = TsgInfo.get_item("tsgsync")
                    sHistory = obj_status.get_history_html("Successfully finished synchronization")
                    data = dict(status="ready", msg=sHistory)

                    # Response JSON with the data
                    response = JsonResponse(data)

                elif mode == "update":
                    # This is a status update request
                    data = dict(status="ok", msg="")

                    # Get the status object
                    obj_status = TsgInfo.get_item("tsgsync")
                    infoval = obj_status.infoval
                    if infoval != "busy":
                        data['status'] = infoval

                    # Get the total history
                    sHistory = obj_status.get_history_html()

                    data['msg'] = sHistory

                    # Response JSON with the data
                    response = JsonResponse(data)

        else:
            data = dict(status="error", msg="User not in radboud-tsg group")
            response = JsonResponse(data)
    except:
        msg = oErr.get_error_message()
        oErr.DoError("tsgsync")

    # Return by rendering the listview of TsgHandle
    return response


class TsgHandleList(BasicList):
    """Paginated view of TsgHandle instances"""

    model = TsgHandle
    listform = TsgHandleForm
    has_select2 = True
    prefix = "tsg"
    basic_name = "tsg"
    new_button = True       # It is possible to add a new TsgHandle
    order_cols = ['code', 'url', 'tsgstatus', 'created']
    # order_default = order_cols
    order_default = ['-tsgstatus__name', 'url', 'code']
    order_heads = [
        {'name': 'Handle',  'order': 'o=1', 'type': 'str',  'custom': 'code'}, 
        {'name': 'URL',     'order': 'o=2', 'type': 'str',  'custom': 'url'}, 
        {'name': 'Status',  'order': 'o=3', 'type': 'str',  'custom': 'status', 'linkdetails': True}, 
        {'name': 'Date',    'order': 'o=4', 'type': 'str',  'custom': 'date',   'linkdetails': True}]
    filters = [ 
        {"name": "Handle",  "id": "filter_handle",  "enabled": False},
        {"name": "URL",     "id": "filter_url",     "enabled": False},
        {"name": "Status",  "id": "filter_status",  "enabled": False},
        ]
    searches = [
        {'section': '', 'filterlist': [
            {'filter': 'handle',    'dbfield': 'code',      'keyS': 'handle_ta',    'keyList': 'handlelist', 'infield': 'id' },
            {'filter': 'url',       'dbfield': 'url',       'keyS': 'url_ta'                            },
            {'filter': 'status',    'fkfield': 'tsgstatus', 'keyList': 'statuslist','infield': 'id' },
            ]
         }
        ]

    def add_to_context(self, context, initial):
        oErr = ErrHandle()
        try:
            # Add some information
            context['is_in_tsg'] = user_is_ingroup(self.request, "radboud-tsg")
            if not context['is_app_editor']:
                context['is_app_editor'] = context['is_in_tsg']

            # Add a basic introduction
            context['basic_intro'] = render_to_string("tsg/tsglist_intro.html", context, self.request)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("TsgHandleList/add_to_context")
        return context

    def get_field_value(self, instance, custom):
        sBack = ""
        sTitle = ""
        oErr = ErrHandle()
        try:
            if custom == "code":
                sTitle = instance.full_handle()
                url = instance.full_handle()
                sBack = '<span class="badge signature ot"><a href="{}" target="_blank">{}</a></span>'.format(url, instance.code)
            elif custom == "url":
                url = instance.url
                sBack = '<span class="badge signature gr"><a href="{}" target="_blank">{}</a></span>'.format(url, instance.url)
            elif custom == "status":
                sBack = instance.get_status()
            elif custom == "date":
                sBack = instance.get_created()
        except:
            msg = oErr.get_error_message()
            oErr.DoError("TsgHandleList/get_field_value")
        return sBack, sTitle


class TsgHandleEdit(BasicDetails):
    model = TsgHandle
    mForm = TsgHandleForm
    basic_name = "tsg"
    prefix = "tsghandle"
    prefix_type = "simple"
    title = "TsgHandle"
    listviewtitle = "TSG Handle list"

    def add_to_context(self, context, instance):
        """Add to the existing context"""

        # Who am I?
        currentuser = self.request.user

        # Add some information
        context['is_in_tsg'] = user_is_ingroup(self.request, "radboud-tsg")
        
        # The name of this current position
        context['intro_breadcrumb'] = "TSG Handle details"

        # The page to return to
        context['prevpage'] = reverse('tsg_list')

        # Set the main items
        if context['is_in_tsg']:
            # This user may also be editor
            context['is_app_editor'] = True
            # Fill in the details to be edited and viewable
            context['mainitems'] = [
                {'type': 'plain',   'label': "URL:",             'value': instance.get_url(False),  'field_key': 'url'      },
                {'type': 'plain',   'label': "Notes:",           'value': instance.notes,           'field_key': 'notes'    },
                {'type': 'plain',   'label': "Handle code:",     'value': instance.code                 },
                {'type': 'plain',   'label': "Handle base url:", 'value': instance.domain               },
                {'type': 'plain',   'label': "Full handle url:", 'value': instance.full_handle(False)   },
                {'type': 'plain',   'label': "Information:",     'value': instance.get_info_html()      },
                {'type': 'plain',   'label': "Status:",          'value': instance.get_status()         },
                {'type': 'plain',   'label': "History:",         'value': instance.get_history(False)   },
                {'type': 'plain',   'label': "Created:",         'value': instance.get_created()        },
            ]
            ## The CREATE handle button is shown if the status is 'ini'
            #if instance.status == "ini":
            #    # Add a button to create a HANDLE
            #    context['tsg_status'] = instance.status
            #    sHandle = render_to_string("tsg/tsghandle_button.html", context, self.request)
            #    oItem = dict(type="safe", label="", value=sHandle)
            #    context['mainitems'].append(oItem)

            # The DELETE button can be shown, if that is appropriate
            if instance.get_statusabbr() != "ini" and instance.code != "":
                # Add the delete button
                context['permission'] = "write"
                sHtml = render_to_string("tsg/tsghandle_buttons.html", context, self.request)
                context['mainitems'].append(dict(type="safe", value=sHtml))


        # Return the total context
        return context

    def before_save(self, form, instance):
        """Check if anything changed and then what needs to be done
        
        Depends on instance.tsgstatus (abbr)
        - ini   If there is a valid URL, then create a link
        - chg   Change the existing link
        """
        bResult = True
        msg = ""
        oErr = ErrHandle()
        try:
            # Who am I?
            currentuser = self.request.user

            # Can we continue to assess the situation?
            if not instance is None and not instance.url is None and instance.url != "":
                # Get current history as an object
                history = json.loads(instance.history)

                # Get the pre-saved version of this item
                obj = self.model.objects.filter(id=instance.id).first()

                # Is this the creation of a link or the changing?
                status_abbr = instance.get_statusabbr()
                if status_abbr == "ini":
                    # First check if the link is not there yet
                    oBack = get_handle_code(self.request, instance.url)
                    status = oBack.get("status")
                    if status == "ok":
                        # There already is a code - Do we already have a TsgHandle with it?
                        handle = TsgHandle.objects.filter(url=instance.url).first()
                        if handle is None or handle.id == obj.id:
                            # Now adapt the form's values
                            form.instance.code = oBack['code']       # Code of the handle
                            form.instance.info = oBack['info']       # This already is a string
                            # Add a note to history
                            history.append("Fetched handle for url [{}]".format(instance.url))
                        else:
                            # There already is a handle pointing to this URL
                            bResult = False
                            msg = "There already is a TSG handle for this url: {}".format(handle.id)
                            history.append(msg)
                    else:
                        # It has not been created yet, so create it
                        oBack = create_handle_info(self.request, instance.url)
                        # Does it make sense?
                        status = oBack.get("status")
                        if status == "ok":
                            # Get the regular information
                            oBack = get_handle_code(self.request, instance.url)
                            if oBack.get("status") == "ok":
                                # Now adapt the form's values
                                form.instance.code = oBack['code']      # Code of the handle
                                form.instance.info = oBack['info']      # This already is a string
                                # Add a note to history
                                history.append("Created handle for url [{}]".format(instance.url))
                            else:
                                # Created handle for URL, but cannot find it anymore
                                history.append("Cannot find handle for URL: {}".format(instance.url))
                        else:
                            # There is some error
                            history.append("Error creating handle: {}".format(oBack.get("msg")))
                            bResult = False
                    # Do we need to change the status?
                    if bResult:
                        # Yes, change the status to 'set'
                        form.instance.status = "set"
                        # instance.save()
                elif obj != None and obj.url != instance.url:
                    # Actually try make the change to the API
                    oBack = change_handle_info(self.request, instance.code, instance.url)
                    if oBack['status'] == "ok":
                        # Try to read back the URL
                        oBack = get_handle_target(self.request, instance.code)
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

                elif not obj is None:
                    # Double check the info component
                    info = obj.info
                    if not info is None:
                        oInfo = json.loads(info)
                        if len(info) < 2:
                            # This just contains the regular information
                            oBack = get_handle_code(self.request, instance.url)
                            if oBack.get("status") == "ok":
                                form.instance.info = oBack['info']       # This already is a string
                else:
                    # Add a new element to the history
                    history.append("Changed notes on {} by {}.".format(get_crpp_date(get_current_datetime()), currentuser))
                # Put it back as string
                form.instance.history = json.dumps(history)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("TsgHandleEdit/before_save")
            bResult = False
        # Signal that saving is needed
        return bResult, msg


class TsgHandleDetails(TsgHandleEdit):
    rtype = "html"

    def add_to_context(self, context, instance):
        """Add to the existing context"""

        # First do the regular contact addition
        context = super(TsgHandleDetails, self).add_to_context(context, instance)

        if context['is_in_tsg']:
            context['permission'] = "write"

        # Now optionally add the delete handle button
        context['after_details'] = render_to_string("tsg/tsghandle_del.html", context, self.request)

        # Return the total context
        return context


class TsgHandleDelete(BasicPart):
    """Delete the PID Handle (not the TsgHandle) of the object"""

    MainModel = TsgHandle

    def add_to_context(self, context):
        """Perform the actual deletion"""

        oErr = ErrHandle()
        try:
            if not self.obj is None:
                # Make sure the redirectpage is set
                self.redirectpage = reverse("tsg_details", kwargs={'pk': self.obj.id})

                # Get the parameter: the CODE = handle
                handle_code = self.obj.code
                if not handle_code is None and handle_code != "":
                    # Try to delete the handle
                    oResult = handle_delete(self.request, handle_code)

                    # Are we successful?
                    if oResult.get("status") == "ok":
                        history = json.loads(self.obj.history)
                        history.append("Deleted the Handle CODE on {}".format(get_crpp_date(timezone.now())))
                        # Then adapt the object
                        self.obj.code = ""
                        self.obj.status = "del"
                        self.obj.history = json.dumps(history)
                        self.obj.save()

        except:
            msg = oErr.get_error_message()
            oErr.DoError("TsgHandleDelete/add_to_context")

        # Return the adapted context
        return context



