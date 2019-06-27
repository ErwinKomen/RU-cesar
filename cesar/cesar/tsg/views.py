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

from cesar.settings import APP_PREFIX
from cesar.utils import ErrHandle
from cesar.browser.models import Status
from cesar.browser.views import nlogin, user_is_authenticated, user_is_ingroup
from cesar.seeker.views import csv_to_excel
from cesar.tsg.models import TsgInfo, TsgHandle


paginateEntries = 15

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


# Views belonging to the Cesar TSG handle processing app.
def tsgsync(request):
    """Synchronize TSG handles."""

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
                                    obj.info = info
                                    bNeedSaving = True
                                # At any rate: check the date
                                if obj.created != date_obj:
                                    obj.created = date_obj
                                    bNeedSaving = True
                            
                                # Save if needed
                                if bNeedSaving:
                                    obj.save()

                    else:
                        msg_lst.append("Request returns code {} for handle {}".format(oBack['code'], handle_code))

    # Return by rendering the listview of TsgHandle
    return redirect('tsg_list')


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
        context['authenticated'] = currentuser.is_authenticated()

        # Add to the context
        context['order_heads'] = self.order_heads
        # context['msg_lst'] = msg_lst
        context['intro_breadcrumb'] = "TSG-Radboud"

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


class TsgHandleDetails(DetailView):
    model = TsgHandle
    template_name = 'tsg/tsghandle_details.html'
