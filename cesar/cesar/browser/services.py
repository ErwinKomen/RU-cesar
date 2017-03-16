import os
import json
from cesar.settings import CRPP_HOME
import requests


def get_crpp_info():
    """Read information from the /crpp service (if available)"""

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
    # REturn what we have
    return oBack
