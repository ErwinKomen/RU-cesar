import os
import json
import requests
import sys
import base64
import zlib
import urllib

# Specific for Cesar
from cesar.settings import CRPP_HOME

# ------------------------------------------------------------------------
# See also: 2015_CrpStudioAPI_v1-3b.docx
# ------------------------------------------------------------------------

def crpp_send_crp(sUser, sCrp, sName):
    """Send one single CRP to the server
    
    Example: /crpp/crpset?{"userid":"erwin", 
                           "crp":   "eJzVvW2THMdxLv", 
                           "name":  "project_01234.crpx",
                           "overwrit": true}
    Note: this only gets the project into /etc/project/{user}


          CorpusStudioWeb uses a /crpp/load command to copy it 
            to /etc/crpstudio/{user}
          But the existence of the project there is only needed for
            the CorpusStudioWeb program, not for the back-end /crpp
    """

    # Construct the object we pass along
    oToCrpp = { 'userid': sUser,
                'crp':    CompressAndBase64(sCrp),
                'name':   sName,
                'overwrite': True}
    # Send and return the reply
    return crpp_command("crpset", oToCrpp)

def crpp_exe(sUser, sCrpName, sLng, sPart, oOptions):
    """Get the /crpp to start executing the indicated project
    
    The expected reply is:    
        { "status": {
            "code": "started",
            "message": "Searching, please wait...",
            "userid": "erwin",
            "jobid": "1",                           # Use this 'jobid' in /crpp/statusxq 
            "checkAgainMs": 200
          }
        }
    """

    # Construct the object we pass along
    oToCrpp = { 'userid': sUser,
                'lng':    sLng,
                'dir':    sPart,
                'crp':    sCrpName,
                'options':oOptions,
                'cache':  False}
    # Send and return the reply
    return crpp_command("exe", oToCrpp)

def crpp_stop(sUser, sJobId):
    # Construct the object we pass along
    oToCrpp = { 'userid': sUser,
                'jobid':  sJobId}
    # Send and return the reply
    return crpp_command("reset", oToCrpp)

def crpp_dbget(sUser, sCrpName, iQC, sType='csv', sPart=''):
    """Get the /crpp to fetch the database results"""

    # Make sure we get the correct database-name
    sDbName = "{}_QC{}_Dbase.xml".format(sCrpName, iQC)
    # Construct the object to be passed along
    oToCrpp = { 'userid': sUser,
                'name': sDbName,
                'part': sPart,
                'type': sType }
    # Send and return the reply
    oBack = crpp_command("dbget", oToCrpp)
    # Make sure we have the correct name of what is being returned
    sDbName = "{}_{}_QC{}_Dbase.{}.gz".format(sCrpName, sPart, iQC, sType)
    oBack['name'] = sDbName
    return oBack

def crpp_status(sUser, sJobId):
    """Send a status request to /crpp for the job with indicated id
    
    The expected reply may look like this:
        { "indexName": "statusxq",
          "content": {
            "jobid": "165",
            "start": "WR-P-P-K-0000000073.folia",           # Last text started
            "finish": "WR-P-P-K-0000000065.folia.xml",      # Most recent text finished
            "count": 62,                                    # Number of texts started
            "total": 81,                                    # Total number of texts to be done
            "ready": 44                                     # Number of texts done
          },
          "status": {
            "code": "working",                              # Final state is "completed"
            "message": "please wait",
            "userid": "erwin"
          }
        }

    Upon completion the reply also contains a table with a summary of the results:
        { "indexName": "statusxq",
          "content": {
            "jobid": "165",
            "searchParam": { "resultsType": "json","tmpdir": "/var/cache/tomcat/temp","waitfortotal": "no"},
            "searchTime":  7478, 
            "searchDone":  true,
            "query": "{\"crp\":\"ChechenMarkerA.crpx\",\"lng\":\"che_lat\",\"save\":\"2015-12-10 13:13:50\",\"dbase\":\"\",\"dir\":\"NPCMC\",\"userid\":\"guest\"}",
            "taskid": 2,
            "table": [
              { "qc": 1,
                "result": "anyParticleA",
                "subcats": [],
                "counts": [],
                "total": 508,
                "hits": [
                  { "file": "Arsanukaev1-2013.psdx", "message": [], "count": 106,
                    "subs": [] },
                  { "file": "Arsanukaev2-2013.psdx", "message": [], "count": 0,
                    "subs": [] }
                ]
              }
            ],
            "total": 71
          },
          "status": {
            "code": "completed",
            "message": "The search has finished",
            "userid": "erwin"
          }
        }
    """

    # Construct the object we pass along
    oToCrpp = { 'userid': sUser,
                'jobid':  sJobId}
    # Send and return the reply
    return crpp_command("statusxq", oToCrpp)

def crpp_dbinfo(sUser, sCrpName, iQcNum, iStart, iCount, sPart='', filter=None, sort=None):
    """Ask the /crpp/dbinfo service for the count it has for the result combination"""

    # Construct the object we pass along
    oToCrpp = { 'userid': sUser,
                'name':   "{}_QC{}_Dbase".format(sCrpName, iQcNum),
                'part': sPart,
                'start':  iStart,
                'count':  iCount }
    # Possibly add filter
    if filter != None and len(filter)>0:
        oToCrpp['filter'] = filter
    # Possibly add sorting
    if sort != None:
        oToCrpp['sort'] = sort
    # Send and return the reply
    return crpp_command("dbinfo", oToCrpp)

def crpp_hitinfo(sUser, sCrpName, sLng, iQcNum, iStart, iCount, filter=None, sort=None):
    """Ask the /crpp/dbinfo service for the count it has for the result combination"""

    # Construct the object we pass along
    oToCrpp = { 'userid': sUser,
                'crp'   : sCrpName,
                'lng'   : sLng,
                'name':   "{}_QC{}_Dbase".format(sCrpName, iQcNum),
                'start':  iStart,
                'count':  iCount }
    # Possibly add filter
    if filter != None and len(filter)>0:
        oToCrpp['filter'] = filter
    # Possibly add sorting
    if sort != None:
        oToCrpp['sort'] = sort
    # Send and return the reply
    return crpp_command("dbinfo", oToCrpp)

def crpp_command(sCommand, oToCrpp):
    # Set the correct URL
    url = CRPP_HOME + '/'+sCommand
    # Default reply
    oBack = {}
    # Get the data from the CRPP api
    try:
        r = requests.post(url, json=oToCrpp)
    except:
        # Getting an exception here probably means that the back-end is not reachable (down)
        oBack['commandstatus'] = 'error'
        oBack['code'] = "The back-end server (crpp) cannot be reached. Is it running?"
        return oBack
    # Action depends on what we receive
    if r.status_code == 200:
        # Convert to JSON
        reply = json.loads(r.text.replace("\t", " "))
        # Get the most meaningful part from the reply
        if 'content' in reply:
            # Get the [content] part (note: no final 's')
            oContent = reply['content']        
            # Copy all items from [oContent] to oBack
            for item in oContent:
                oBack[item] = oContent[item]
            # Also copy the status
            if 'status' in reply:
                if 'code' in reply['status']:
                    oStatus = reply['status']
                    for item in oStatus:
                        oBack[item] = oStatus[item]
                    oBack['status'] = oStatus['code']
                else:
                    oBack['status'] = reply['status']
        else:
            # Just copy all items
            for item in reply:
                oBack[item] = reply[item]
        oBack['commandstatus'] = 'ok'
    else:
        oBack['commandstatus'] = 'error'
        oBack['code'] = "The server returns error {}: {}".format(r.status_code, r.reason)
    # REturn what we have
    return oBack
     
def CompressAndBase64(sText):
    """Compress the string and then encode it into base64"""
    
    sConverted = base64.b64encode( zlib.compress(bytes(sText, encoding="utf-8")))
    sConverted = sConverted.decode("utf-8").replace("+", "~")
    return sConverted 