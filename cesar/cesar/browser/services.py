import os
import json
import requests
import sys
import time
import threading
from cesar.settings import CRPP_HOME
from cesar.utils import ErrHandle

def get_exc_message():
    exc_type, exc_value = sys.exc_info()[:2]
    sMsg = "Handling {} exception with message '{}'".format(exc_type.__name__, exc_value)
    return sMsg

def get_crpp_info():
    """Read the list of available corpora from the /crpp service (if available)"""

    # Set the correct URL
    url = CRPP_HOME + "/serverinfo"
    # Default reply
    oBack = {}
    # Get the data from the CRPP api
    try:
        r = requests.get(url)
    except:
        # Getting an exception here probably means that the back-end is not reachable (down)
        oBack['status'] = 'error'
        oBack['code'] = "get_crpp_info(): The back-end server (crpp) cannot be reached. Is it running? {}".format(
            get_exc_message())
        return oBack
    # Action depends on what we receive
    if r.status_code == 200:
        # Convert to JSON
        reply = json.loads(r.text.replace("\t", " "))
        # Get the [contents] part
        oContent = reply['contents']
        # Start my own reply: take over the 'corpora' contents
        oBack = json.loads(oContent['corpora'])
        # Add the 'indices' separately
        oBack['indices'] = oContent['indices']
        oBack['status'] = 'ok'
    else:
        oBack['status'] = 'error'
        oBack['code'] = r.status_code
    # REturn what we have
    return oBack

def get_crpp_texts(sLng, sPart, sFormat, status):
    """Read the list of texts from the /crpp service (if available)"""

    oErr = ErrHandle()
    try:
        # Construct the object we pass along
        oTxtList = {'userid': "erwin",
                    'lng': sLng,
                    'ext': sFormat}
        # Possibly add 'dir'
        if sPart != None and sPart != "":
            oTxtList['dir'] = sPart
        # Set the correct URL
        url = CRPP_HOME + '/txtlist?' + json.dumps(oTxtList)
        # Default reply
        oBack = {}
        # Get the data from the CRPP api
        try:
            r = requests.get(url)
        except:
            # Getting an exception here probably means that the back-end is not reachable (down)
            oBack['status'] = 'error'
            oBack['code'] = "get_crpp_texts(): The back-end server (crpp) cannot be reached. Is it running? \n{} \nURL={}".format(
                get_exc_message(), url)
            return oBack
        # Action depends on what we receive
        if r.status_code == 200:
            # Convert to JSON
            reply = json.loads(r.text.replace("\t", " "))
            # Get the [content] part (note: no final 's')
            oContent = reply['content']
            # If all is well, then we receive just a jobid
            if "jobid" in oContent:
                sJobId = oContent['jobid']
                # Now continue to ask for the status
                oTxtListStatus = {'userid': "erwin", 'jobid': sJobId}
                url = CRPP_HOME + '/statusxl?' + json.dumps(oTxtListStatus)
                bDone = False
                while not bDone:
                    # Get the data from the CRPP api
                    try:
                        r = requests.get(url)
                    except:
                        error_info = sys.exc_info()
                        iStop = True
                    # Action depends on what we receive
                    if r.status_code == 200:
                        # Convert the reply to JSON
                        reply = json.loads(r.text.replace("\t", " "))
                        # Get the [content] part (note: no final 's')
                        oContent = reply['content']
                        # Get the status part
                        oStatus = reply['status']
                        if oStatus['code'] == "error":
                            # There is an error
                            oBack['status'] = 'error'
                            oBack['code'] = oContent['code'] + oContent['msg']
                            bDone = True
                            # Need to store this status!!!
                            status.set("crpp", oBack)
                        elif oStatus['code'] == "finished":
                            # The process is ready
                            bDone = True
                            # Get the textlist
                            oTextList = oContent['textlist']
                            # Define the lists
                            oBack['count'] = oTextList['texts']
                            oBack['subtype'] = oTextList['subtype']
                            oBack['genre'] = oTextList['genre']
                            oBack['paths'] = oTextList['paths']
                            oBack['txtlist'] = oTextList['list']
                            oBack['status'] = 'ok'

                            # What we show in the end is not what needs to be returned
                            oShow = dict(count=oTextList['texts'],
                                         subtype=oTextList['subtype'],
                                         paths=oTextList['paths'])
                            oShow['status'] = 'ok'
                            oShow['status.code'] = oStatus['code']
                            # Need to store this status!!!
                            status.set("crpp", oShow)
                        else:
                            # Update the synchronisation object that contains all relevant information
                            oBack['lng'] = sLng
                            oBack['part'] = sPart
                            oBack['format'] = sFormat
                            oBack['count'] = oContent['total']
                            oBack['status.code'] = oStatus['code']
                            oBack['last.url'] = url
                            status.set("crpp", oBack)

                            # DEBUGGING
                            sMsg = oStatus['code'] 
                            if 'msg' in oContent:
                                sMsg += " " + oContent['msg']
                            if 'msg' in oStatus:
                                sMsg += " " + oStatus['msg']
                            oErr.Status(sMsg)

                            # Make sure we wait some time before making the next request
                            period = 0.400
                            nexttime = time.time() + period
                            bReady = False
                            while not bReady:
                                now = time.time()
                                bReady = (now > nexttime)
                            
                    else:
                        # There is an error
                        oBack['status'] = 'error'
                        oBack['code'] = r.status_code
                        bDone = True
            else:
                oBack['status'] = 'error'
                oBack['code'] = ""

        else:
            oBack['status'] = 'error'
            oBack['code'] = r.status_code
    except:
        oBack['status'] = 'error'
        oBack['code'] = sys.exc_info()[1]

    # REturn what we have
    return oBack

def get_crpp_text(sLng, sPart, sFormat, sName):
    """Get the one single text
    
    Example: /crpp/txt?{"userid":"erwin", "lng":"", "dir": "OE", "ext": "psdx", "name": "coadrian.o34"}
    """

    # Construct the object we pass along
    oTxtReq = {'userid': "erwin",
                'lng': sLng,
                'ext': sFormat,
                'name': sName}
    # Possibly add 'dir'
    if sPart != None and sPart != "":
        oTxtReq['dir'] = sPart
    # Set the correct URL
    url = CRPP_HOME + '/txt?' + json.dumps(oTxtReq)
    # Default reply
    oBack = {}
    # Get the data from the CRPP api
    try:
        r = requests.get(url)
    except:
        # Getting an exception here probably means that the back-end is not reachable (down)
        oBack['status'] = 'error'
        oBack['code'] = "get_crpp_text(): The back-end server (crpp) cannot be reached. Is it running? {}".format(
            get_exc_message())
        return oBack
    # Action depends on what we receive
    if r.status_code == 200:
        # Convert to JSON
        reply = json.loads(r.text.replace("\t", " "))
        # Get the [content] part (note: no final 's')
        oContent = reply['content']
        # Define the lists
        oBack['count'] = oContent['count']
        oBack['line'] = oContent['line']
        oBack['status'] = 'ok'
    else:
        oBack['status'] = 'error'
        oBack['code'] = "The server returns error {}: {}".format(r.status_code, r.reason)
    # REturn what we have
    return oBack

def get_crpp_sent_info(options):
    """Retrieve the information belonging to the sentence defined in [options]"""
    oBack = {}

    try:
        # Set the correct URL
        url = CRPP_HOME + "/txt?" + json.dumps(options)
        # Get the data from the CRPP api
        r = requests.get(url)
        # Action depends on what we receive
        if r.status_code == 200:
            # Convert to JSON (and replace any tabs to a space)
            reply = json.loads(r.text.replace("\t", " "))
            # Get the [content] part (note: no final 's')
            oContent = reply['content']
            # Define the lists
            oBack['info'] = oContent
            oBack['status'] = 'ok'
        else:
            oBack['status'] = 'error'
            oBack['code'] = "The server returns error {}: {}".format(r.status_code, r.reason)
    except:
        oBack = None
    
    return oBack