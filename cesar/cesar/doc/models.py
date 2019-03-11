import os
import sys
import time
import json
from io import StringIO 
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from cesar.utils import ErrHandle
from cesar.seeker.models import import_data_file
from cesar.settings import WRITABLE_DIR

# FOlia handling: pynlpl
import pynlpl
from pynlpl.formats import folia
from pynlpl.textprocessors import tokenize, split_sentences

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
        inputType = "folia"

        folProc = FoliaProcessor(username)
        try:
            # Directory: one directory for each user
            dir = folProc.dir

            # Read and create basis-folia
            bResult, sMsg = folProc.basis_folia(filename, data_file)
            if not bResult:
                # There was some kind of error
                oBack['status'] = 'error'
                oBack['msg'] = "basis_folia load error: {}".format(sMsg)
            else:
                # DEBUG: show the frog location
                errHandle.Status("DEBUG: froglocation={}".format(froglocation))

                # Action depends on the [froglocation]
                if froglocation == "local":
                    # We can make use of the locally available frog
                    frog = Frog(FrogOptions(parser=False))

                    doc = folProc.doc
                    # Iterate over all the sentences
                    for sentence in doc.sentences():
                        # Get the text of this sentence
                        sLine = sentence.text()
                        # This produces one chunk of FoLiA
                        parsed_output = frog.process(sLine)
                        ## The output is an instance of [folia.Document]
                        #lFolia.append(output)
                        # The output is a list of dictionary objects
                        errHandle.Status(json.dumps(parsed_output))
                    # TODO: combine lFolia into one oDoc
                    # oDoc = None
                else:
                    # Think of a project name
                    project = folProc.docstr
                    basicauth = True
                    # Get access to the webservice
                    clamclient = CLAMClient(frogurl, clamuser, clampw, basicauth = basicauth)
                    result = clamclient.create(project)
                    data = clamclient.get(project)
                    # If we have textinput, then it is 'maininput' (see /frog/info)
                    if inputType == "text":
                        it = data.inputtemplate('maininput')
                        for param in it.parameters:
                            if param.id == 'author':
                                param.value = "cesar"
                                param.hasvalue = True
                        it.filename = self.name
                    else:
                        it = data.inputtemplate("foliainput")
                
                    # Add the Basis-Folia XML file as input to the project
                    basicf = folProc.basicf
                    result = clamclient.addinputfile(project, it, basicf, language='nl')
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
                            fout = fout.replace(".basis", ".folia")
                            outputfile.copy(fout)
                            iCount += 1
                        else:
                            # Download the Folia XML file to (current dir)
                            fout = os.path.abspath(os.path.join(dir, os.path.basename(str(outputfile))))
                            fout = fout.replace(".basis", ".folia")
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

class FoliaProcessor():
    """Functions to help create or process a folia document"""

    docstr = ""         # The identifier of this document
    username = ""       # The owner of this document
    dir = ""            # Directory for the output
    basicf = ""         # If any: where the basis folis is
    doc = None

    def __init__(self, username):
        # Check and/or create the appropriate directory for the user
        dir = os.path.abspath(os.path.join( WRITABLE_DIR, username))
        if not os.path.exists(dir):
            os.mkdir(dir)
        # Set the dir locally
        self.dir = dir

    def basis_folia(self, filename, data_contents):

        errHandle = ErrHandle()
        bReturn = False
        sMsg = ""
        try:
            # Read file into array
            lines = []
            for line in data_contents:
                lines.append(line.decode("utf-8").strip())

            # Check and/or create the appropriate directory for the user
            dir = self.dir

            # create a folia document with a numbered id
            docstr = os.path.splitext( os.path.basename(filename))[0]
            # Make sure we remember the docstr
            self.docstr = docstr

            # Start creating a folia document
            doc = folia.Document(id=docstr)
            text = doc.add(folia.Text)

            # Walk through the JSON 
            lFolia = []
            for sLine in lines:
                # Check for empty
                sLine = sLine.strip()
                if sLine != "":
                    # Append a paragraph
                    para = text.add(folia.Paragraph)
                    # Set the <t> of this paragraph
                    # para.settext(sLine)
                    # Split text into sentences
                    sf = StringIO(sLine)
                    for s_list in pynlpl.textprocessors.Tokenizer(sf, splitsentences=True):
                        for s in s_list:
                            sentence = para.add(folia.Sentence)
                            for token in s:
                                sentence.add(folia.Word, token)
                            # Add text to sentence
                            sentence.settext(sentence.text())
                    # Add text to paragraph
                    para.settext(para.text())

            # THink of a correct name for Basic folia
            f =  os.path.abspath(os.path.join(dir, docstr) + ".basis.xml")
            self.basicf = f
            # Save the doc
            doc.save(f)
            # Make sure the doc is in this class instance
            self.doc = doc
            # Set positive return
            bReturn = True
        except:
            sMsg = errHandle.get_error_message()
            errHandle.DoError("basis_folia")
            bReturn = False
        # Return what has happened
        return bReturn, sMsg