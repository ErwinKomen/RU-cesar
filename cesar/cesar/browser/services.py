import os
import json
from cesar.settings import CRPP_HOME
import requests


def get_crpp_info():
    """Read the list of available corpora from the /crpp service (if available)"""

    # Set the correct URL
    url = CRPP_HOME + "/crpp/serverinfo"
    # Default reply
    oBack = {}
    # Get the data from the CRPP api
    r = requests.get(url)
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


def get_crpp_texts(sLng, sPart, sFormat):
    """Read the list of texts from the /crpp service (if available)"""

    # Construct the object we pass along
    oTxtList = {'userid': "erwin",
                'lng': sLng,
                'ext': sFormat}
    # Possibly add 'dir'
    if sPart != None and sPart != "":
        oTxtList['dir'] = sPart
    # Set the correct URL
    url = CRPP_HOME + '/crpp/txtlist?' + json.dumps(oTxtList)
    # Default reply
    oBack = {}
    # Get the data from the CRPP api
    r = requests.get(url)
    # Action depends on what we receive
    if r.status_code == 200:
        # Convert to JSON
        reply = json.loads(r.text.replace("\t", " "))
        # Get the [content] part (note: no final 's')
        oContent = reply['content']
        # Define the lists
        oBack['count'] = oContent['texts']
        oBack['paths'] = oContent['paths']
        oBack['txtlist'] = oContent['list']
        oBack['status'] = 'ok'
    else:
        oBack['status'] = 'error'
        oBack['code'] = r.status_code
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
    url = CRPP_HOME + '/crpp/txt?' + json.dumps(oTxtReq)
    # Default reply
    oBack = {}
    # Get the data from the CRPP api
    r = requests.get(url)
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
        oBack['code'] = r.status_code
    # REturn what we have
    return oBack

def get_crpp_sent_info(options):
    """Retrieve the information belonging to the sentence defined in [options]"""
    oBack = {}

    try:
        # Set the correct URL
        url = CRPP_HOME + "/crpp/txt?" + json.dumps(options)
        # Get the data from the CRPP api
        r = requests.get(url)
        # Action depends on what we receive
        if r.status_code == 200:
            # Convert to JSON
            reply = json.loads(r.text.replace("\t", " "))
            # Get the [content] part (note: no final 's')
            oContent = reply['content']
            # Define the lists
            oBack['info'] = oContent
            oBack['status'] = 'ok'
        else:
            oBack['status'] = 'error'
            oBack['code'] = r.status_code
    except:
        oBack = None
    
    return oBack