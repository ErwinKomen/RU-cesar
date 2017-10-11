import os
import json
from cesar.settings import CRPP_HOME
import requests
import sys
import base64
import zlib

def crpp_send_crp(sUser, sCrp, sName):
    """Send one single CRP to the server
    
    Example: /crpp/crpset?{"userid":"erwin", 
                           "crp":   "eJzVvW2THMdxLv", 
                           "name":  "project_01234.crpx"}
    """

    # Construct the object we pass along
    oToCrpp = { 'userid': sUser,
                'crp':    CompressAndBase64(sCrp),
                'name':   sName,
                'overwrite': True}
    # Send and return the reply
    return crpp_command("crpset", oToCrpp)

def crpp_exe(sUser, sCrpName, sLng, sPart):
    """Get the /crpp to start executing the indicated project"""

    # Construct the object we pass along
    oToCrpp = { 'userid': sUser,
                'lng':    sLng,
                'dir':    sPart,
                'crp':    sCrpName,
                'cache':  False}
    # Send and return the reply
    return crpp_command("exe", oToCrpp)



def crpp_command(sCommand, oToCrpp):
    # Set the correct URL
    url = CRPP_HOME + '/crpp/'+sCommand+'?' + json.dumps(oToCrpp)
    # Default reply
    oBack = {}
    # Get the data from the CRPP api
    try:
        r = requests.get(url)
    except:
        # Getting an exception here probably means that the back-end is not reachable (down)
        oBack['status'] = 'error'
        oBack['code'] = "The back-end server (crpp) cannot be reached. Is it running?"
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
   
  
def CompressAndBase64(sText):
    """Compress the string and then encode it into base64"""
    
    sConverted = base64.b64encode( zlib.compress(bytes(sText, encoding="utf-8")))
    sConverted = str(sConverted).replace("+", "~")
    return sConverted 