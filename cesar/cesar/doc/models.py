import os
import sys
import time
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from cesar.utils import ErrHandle
from cesar.seeker.models import import_data_file
from cesar.settings import WRITABLE_DIR

# FOlia handling: pynlpl
import pynlpl

# Attempt to input FROG
try:
    from frog import Frog, FrogOptions
    froglocation = "local"
    # See: https://frognlp.readthedocs.io/en/latest/pythonfrog.html
except:
    # It is not there...
    froglocation = "remote"
    frogurl = "https://webservices-lst.science.ru.nl/frog"
    from clam.common.client import *

MAXPARAMLEN = 100


class FoliaDocs(models.Model):
    """Set of folia-encoded documents"""
    
    # [1] These belong to a particular user
    owner = models.ForeignKey(User, editable=False)

    def __str__(self):
        return self.owner.username


class FrogLink(models.Model):
    """This provides the basic link with FROG

    Can be either frog local or frog remote, through the CLAM service
    """

    # [1] Each froglink centers around a file that is uploaded, processed and made available
    name = models.CharField("Name to be used for this file", max_length=MAXPARAMLEN)
    # [1] Each link belongs to a set of docs (that belong to an owner)
    docs = models.ForeignKey(FoliaDocs)
    # [1] Each Froglink has been created at one point in time
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def create(name, username):
        """Possibly create a new item"""

        # Get the correct user
        owner = User.objects.filter(username=username).first()

        # Find a FoliaDocs instance for this user
        fd = FoliaDocs.objects.filter(owner=owner).first()
        if fd == None:
            fd = FoliaDocs(owner=owner)
            fd.save()

        obj = FrogLink.objects.filter(name=name).first()
        if obj == None:
            # Create it
            obj = FrogLink(name=name, docs=fd)
            obj.save()
        # Return the result 
        return obj

    def read_doc(self, username, data_file, filename, clamuser, clampw, arErr, xmldoc=None, sName = None, oStatus = None):
        """Import a text file, parse it through the frogger, and create a Folia.xml file"""

        oBack = {'status': 'ok', 'count': 0, 'msg': "", 'user': username}
        errHandle = ErrHandle()
        oDoc = None
        iCount = 0
        try:
            # Directory: one directory for each user
            dir = os.path.abspath(os.path.join( WRITABLE_DIR, username))
            if not os.path.exists(dir):
                os.mkdir(dir)
            # Action depends on the [froglocation]
            if froglocation == "local":
                # We can make use of the local frog
                frog = Frog(FrogOptions(parser=False, xmlout=TRue))

                # FIrst try: do it all at once
                if True:
                    oDoc = frog.process(data_file)
                    # The output is an instance of [folia.Document]
                else:
                    # Read the data into a JSON object -- then each 'line' is one 'paragraph'
                    oJson = import_data_file(data_file, errHandle)
                    # Walk through the JSON 
                    lFolia = []
                    for sLine in oJson:
                        # This produces one chunk of FoLiA
                        output = frog.process(sLine)
                        # The output is an instance of [folia.Document]
                        lFolia.append(output)
                    # TODO: combine lFolia into one oDoc
                    # oDoc = None
            else:
                # Think of a project name
                project = self.name
                basicauth = True
                # Get access to the webservice
                clamclient = CLAMClient(frogurl, clamuser, clampw, basicauth = basicauth)
                result = clamclient.create(project)
                data = clamclient.get(project)
                it = data.inputtemplate('maininput')
                for param in it.parameters:
                    if param.id == 'docid':
                        param.value = self.name
                        param.hasvalue = True
                    elif param.id == 'author':
                        param.value = "cesar"
                        param.hasvalue = True
                it.filename = self.name
                
                # Add the file as input to the project
                f = os.path.abspath(os.path.join(dir, filename))
                with open(f, "wb") as destination:
                    destination.write(data_file.read())
                # f = "./probeersel.txt"
                result = clamclient.addinputfile(project, it, f, language='nl')
                # Opstarten
                result = clamclient.start(project)
                if result.errors:
                    # Handle errors
                    sys.exit(1)
                # Otherwise loop until ready
                while result.status != clam.common.status.DONE:
                    time.sleep(1)			            # Wacht 4 seconden
                    result = clamclient.get(project)	# Refresh status
                    statusmsg = result.statusmessage
                    completion = result.completion
                    if oStatus != None:
                        msg = "{}: {}% completed".format(statusmsg, completion)
                        oStatus.set("CLAM", msg=msg)
                # Now we are ready
                for outputfile in result.output:
                    name = str(outputfile)
                    if ".xml"  in name or ".frog.out" in name:
                        # Download the Folia XML file to (current dir)
                        fout = os.path.abspath(os.path.join(dir, os.path.basename(str(outputfile))))
                        outputfile.copy(fout)
                        iCount += 1
                # Delete project again
                clamclient.delete(project)
  


            # Make sure the requester knows how many have been added
            oBack['count'] = iCount   # The number of sermans added
            oBack['filename'] = filename
            oBack['concreteness'] = 0

        except:
            sError = errHandle.get_error_message()
            oBack['status'] = 'error'
            oBack['msg'] = sError

        # Return the object that has been created
        return oBack

    