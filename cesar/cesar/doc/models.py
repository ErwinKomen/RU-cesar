import os
import sys
import time
import json
import re
import copy
import pytz
from io import StringIO 
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from cesar.utils import ErrHandle
from cesar.seeker.models import import_data_file
from cesar.settings import WRITABLE_DIR, TIME_ZONE

# XML processing
from xml.dom import minidom

# FOlia handling: pynlpl
import pynlpl
from pynlpl.textprocessors import tokenize      # , split_sentences

# New folia: FOliaPy
import folia.main as folia


## Attempt to input FROG
#try:
#    from frog import Frog, FrogOptions
#    # See: https://frognlp.readthedocs.io/en/latest/pythonfrog.html
#except:
#    # It is not there...
#    frogurl = "https://webservices-lst.science.ru.nl/frog"
#    from clam.common.client import *

# OLD: frogurl = "https://webservices-lst.science.ru.nl/frog"
# New (2020, december)
frogurl = "https://webservices.cls.ru.nl/frog"
from clam.common.client import *

MAXPARAMLEN = 100
MAXPATH = 256
FROGPORT = 8020

#def get_crpp_date(dtThis):
#    """Convert datetime to string"""

#    # Model: yyyy-MM-dd'T'HH:mm:ss
#    sDate = dtThis.strftime("%Y-%m-%dT%H:%M:%S")
#    return sDate

def get_crpp_date(dtThis, readable=False):
    """Convert datetime to string"""

    if readable:
        # Convert the computer-stored timezone...
        dtThis = dtThis.astimezone(pytz.timezone(TIME_ZONE))
        # Model: yyyy-MM-dd'T'HH:mm:ss
        sDate = dtThis.strftime("%d/%B/%Y (%H:%M)")
    else:
        # Model: yyyy-MM-dd'T'HH:mm:ss
        sDate = dtThis.strftime("%Y-%m-%dT%H:%M:%S")
    return sDate



class FoliaDocs(models.Model):
    """Set of folia-encoded documents"""
    
    # [1] These belong to a particular user
    owner = models.ForeignKey(User, editable=False, on_delete=models.CASCADE, related_name="owner_foliadocs")

    def __str__(self):
        return self.owner.username


class FrogLink(models.Model):
    """This provides the basic link with FROG

    Can be either frog local or frog remote, through the CLAM service
    """

    # [1] Each froglink centers around a file that is uploaded, processed and made available
    name = models.CharField("Name to be used for this file", max_length=MAXPARAMLEN)
    # [1] Each link belongs to a set of docs (that belong to an owner)
    fdocs = models.ForeignKey(FoliaDocs, related_name="documents", on_delete=models.CASCADE)
    # [0-1] Full name is the full path of the folia.xml document on the server
    fullname = models.CharField("Full path of this file", max_length=MAXPATH, null=True, blank=True)
    # [0-1] Concreteness as stringified JSON object
    concr = models.TextField("Concreteness scores", null=True, blank=True)
    # [1] Each Froglink has been created at one point in time
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def create(name, username):
        """Possibly create a new item [name] for user [username]"""

        errHandle = ErrHandle()

        try:
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
                obj = FrogLink(name=name, fdocs=fd)
                obj.save()
            # Return the result 
            return obj, ""
        except:
            errHandle.DoError("FrogLink/create")
            return None, errHandle.get_error_message()

    def get_created(self):
        sBack = self.created.strftime("%d/%B/%Y (%H:%M)")
        return sBack

    def get_owner(self):
        """Return the owner of this concreteness document"""

        sBack = ""
        if self.fdocs != None:
            if self.fdocs.owner != None:
                sBack = self.fdocs.owner.username
        return sBack

    def read_doc(self, username, data_file, filename, clamuser, clampw, arErr, xmldoc=None, sName = None, oStatus = None):
        """Import a text file, parse it through the frogger, and create a Folia.xml file"""

        oBack = {'status': 'ok', 'count': 0, 'msg': "", 'user': username}
        errHandle = ErrHandle()
        oDoc = None
        iCount = 0
        inputType = "folia"
        frogType = "remote"     # Fix to remote -- or put to None if automatically choosing

        def get_error_log(result):
            """Try to get the error.log file contents"""
            for item in result.output:
                name = str(item)
                if "error.log" in name:
                    lText = []
                    for part in item:
                        lText.append(part.decode("utf-8").strip())
                        # lText.append(str(part))
                    sText = "\n".join(lText)
            return sText

        def get_error_view(errorpoint, statusmsg, errormsg, sLog, sText):
            lhtml = []
            lhtml.append("<div>Error in {}: {}</div>".format(errorpoint, statusmsg))
            lhtml.append("<div>Frog error: {}</div>".format(errormsg))
            lhtml.append("<div class='panel panel-default'>")
            lhtml.append("  <div class='panel-heading' data-toggle='collapse' data-target='#error_log'>Log Info</div>")
            lhtml.append("  <div id='error_log' class='collapse'><pre style='font-size: smaller;'>{}</pre></div>".format(sLog))
            lhtml.append("</div>")
            # Get a (numbered) listing of the text file
            lhtml.append("<div class='panel panel-default'>")
            lhtml.append("  <div class='panel-heading' data-toggle='collapse' data-target='#error_text'>Text file</div>")
            lhtml.append("  <div id='error_text' class='collapse'><pre style='font-size: smaller;'>{}</pre></div>".format(sText))
            lhtml.append("</div>")
            return "\n".join(lhtml)


        folProc = FoliaProcessor(username)
        try:
            # Check our location
            frogLoc = frogType if frogType != None else folProc.location()

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
                errHandle.Status("DEBUG: frogLoc={}".format(frogLoc))


                if frogLoc == "remote":
                    # Think of a project name
                    project = folProc.docstr
                    basicauth = True
                    # Get access to the webservice
                    clamclient = CLAMClient(frogurl, clamuser, clampw, basicauth = basicauth)
                    # First delete any previous project, if it exists
                    try:
                        result = clamclient.delete(project)
                        errHandle.Status("Removed previous project {} = {}".format(project, result))
                    except:
                        # No problem: no project has been removed
                        pass
                    # Only now start creating it
                    result = clamclient.create(project)
                    errHandle.Status("Created new project {} = {}".format(project, result))
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
                        oBack['status'] = "error"
                        # Handle errors
                        statusmsg = result.statusmessage
                        errormsg = result.errormsg
                        # Find the error log
                        sText = get_error_log(result)
                        oBack['msg'] = get_error_view("Pre-CLAM", statusmsg, errormsg, sText, sMsg)
                        return oBack
                    # Otherwise loop until ready
                    while result.status != clam.common.status.DONE:
                        time.sleep(1)			            # Wacht 4 seconden
                        result = clamclient.get(project)	# Refresh status
                        statusmsg = result.statusmessage
                        completion = result.completion
                        if oStatus != None:
                            msg = "{}: {}% completed".format(statusmsg, completion)
                            oStatus.set("CLAM", msg=msg)
                    if result.errors:
                        oBack['status'] = "error"
                        # Handle errors
                        statusmsg = result.statusmessage
                        errormsg = result.errormsg
                        # Find the error log
                        sText = get_error_log(result)
                        oBack['msg'] = get_error_view("Post-CLAM", statusmsg, errormsg, sText, sMsg)
                        return oBack
                    # Now we are ready
                    for outputfile in result.output:
                        name = str(outputfile)
                        if ".xml"  in name:
                            # Download the Folia XML file to the user's dir
                            fout = os.path.abspath(os.path.join(dir, os.path.basename(str(outputfile))))
                            fout = fout.replace(".basis", ".folia")
                            outputfile.copy(fout)
                            iCount += 1
                            
                            # Note where it is
                            self.fullname = fout
                            self.save()

                            # Bugfix because of new libfolia version
                            # self.folia_annotation_reduction()

                        else:
                            # Download the other files to a log dir
                            logdir = os.path.abspath(os.path.join(dir, "log"))
                            if not os.path.exists(logdir):
                                os.mkdir(logdir)
                            elif not os.path.isdir(logdir):
                                os.remove(logdir)
                                os.mkdir(logdir)
                            fout = os.path.abspath(os.path.join(logdir, os.path.basename(str(outputfile))))
                            fout = fout.replace(".basis", ".folia")
                            outputfile.copy(fout)
                            iCount += 1
                    # Delete project again
                    clamclient.delete(project)
  
                else:
                    # Don't know this location type
                    pass


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

    def folia_annotation_reduction(self):
        """Remove annotation layers that are not recognized by the current FoLiA"""

        oErr = ErrHandle()
        bOkay = True
        try:
            # (1) Read the file as XML
            fullname = self.fullname
            xmldoc = minidom.parse(fullname)
            # (2) find the <annotations>
            ndAnnot_list = xmldoc.getElementsByTagName("annotations")
            remove_list = []
            if ndAnnot_list.length > 0:
                annotations = ndAnnot_list[0]
                for annotation in annotations.childNodes:
                    if annotation.nodeType == minidom.Node.ELEMENT_NODE:
                        if annotation.tagName == "quote-annotation" or annotation.tagName == "alternative-annotation":
                            # Mark this one as one to be removed
                            remove_list.append(annotation)
            for item in reversed(remove_list):
                annotations.removeChild(item)
            # Save the result
            with open(fullname, "w", encoding="utf-8") as f:
                xmldoc.writexml(f)
        except:
            sError = oErr.get_error_message()
            oErr.DoError("folia_annotation_reduction")
            bOkay = False

        # Return okay
        return bOkay

    def do_concreteness(self):
        rules = [   {'pos': 'ADJ'},
                    {'pos': 'N'},
                    {'pos': 'WW', 'lemma_excl': ['hebben', 'zijn', 'zullen', 'willen', 'worden', 'moeten', 'mogen', 'kunnen', 'laten', 'doen']} ]
        bResult = False
        sMsg = ""
        oErr = ErrHandle()

        def treat_word(posonly, posfull, lemma):
            """Check if this category must be included"""
            bFound = False
            for rule in rules:
                if 'pos' in rule and rule['pos'] == posonly:
                    # Continue
                    if 'lemma_excl' in rule:
                        bFound = lemma not in rule['lemma_excl']
                    else:
                        bFound = True
                    # Whatever the outcome, we have found our result now
                    break
            return bFound

        try:
            # Create a regular expression to detect a content word
            # re_content = re.compile(r'^(VNW|N)$')
            # Read the file into a doc
            doc = folia.Document(file=self.fullname)
            # Read through paragraphs
            para_scores = []
            for para in doc.paragraphs():
                # Read sentences
                sent_scores = []
                for sent in para.sentences():
                    # Read through the words
                    word_scores = []
                    for word in sent.words():
                        # Get to the POS and the lemma of this word
                        pos = word.annotation(folia.PosAnnotation)
                        postag = pos.cls.split("(")[0]
                        lemma = word.annotation(folia.LemmaAnnotation)                     
                        lemmatag = lemma.cls
                        # Check if we need to process this word (if it is a 'content' word)
                        # OLD: if re_content.match(postag):
                        if treat_word(postag, pos, lemmatag):
                            # Get the *FIRST* brysbaert equivalent if existing
                            brys = Brysbaert.objects.filter(stimulus=lemmatag).first()
                            if brys == None:
                                if word.text() == "pensioenregeling":
                                    bStop = True
                                # Check if there are multiple morph parts
                                morph_parts = [m.text() for m in word.morphemes()]
                                score = -1
                                if len(morph_parts)>0:
                                    # There are multiple morphemes
                                    brysb_parts = []
                                    score = 0
                                    for idx, m in enumerate(morph_parts):
                                        brys = Brysbaert.objects.filter(stimulus=m).first()
                                        if brys == None:
                                            score = -1
                                            break
                                        # Add the score to the list
                                        brysb_parts.append(brys.get_concreteness())
                                    if score == 0:
                                        # Determine the average
                                        for m in brysb_parts:
                                            score += m
                                        score = score / len(brysb_parts)
                                    else:
                                        # change the 'lemmatag' to reflect the breaking up of this word into morphemes
                                        lemmatag = "{} (={})".format(lemmatag, "-".join(morph_parts))
                            else:
                                # The concreteness of this word is in brys
                                score = brys.get_concreteness()
                            # Process the score of this content word
                            oScore = {}
                            oScore['word'] = word.text()
                            oScore['pos'] = postag
                            oScore['pos_full'] = pos.cls
                            oScore['lemma'] = lemmatag
                            oScore['concr'] = "NiB" if score < 0 else str(score)
                            # Add it in all lists
                            word_scores.append(oScore)

                    # Process the results of this sentence
                    score = 0
                    n = len(word_scores)
                    for obj in word_scores:
                        if obj['concr'] == "NiB":
                            n -= 1
                        else:
                            score += float(obj['concr'])
                    if n < 1:
                        n = 1
                    avg = score / n
                    sent_scores.append({'score': avg, 'n': n, 'sentence': sent.text(), 'list': word_scores})
                # Process the results of this paragraph
                score = 0
                n = 0
                for obj in sent_scores:
                    score += obj['score']
                    n += obj['n']
                avg = score / len(sent_scores)
                para_scores.append({'score': avg, 'n': n, 'paragraph': para.text(), 'list': sent_scores})

            # Process the results of this text
            score = 0
            n = 0
            for obj in para_scores:
                score += obj['score']
                n += obj['n']
            avg = score / len(para_scores)
            oText = {'text': self.name, 'score': avg, 'n': n, 'list': para_scores}

            # Add the concreteness as string
            self.concr = json.dumps(oText)
            self.save()
            bResult = True
            return bResult, sMsg
        except:
            bResult = False
            sMsg = oErr.get_error_message()
            return bResult, sMsg

    def get_csv(self):
        """Convert [concr] to CSV-string with header row""" 

        lCsv = []
        oErr = ErrHandle()
        try:
            # Start with the header
            oLine = "{}\t{}\t{}\t{}\t{}\t{}\t{}".format("par", "snt", "wrd", "text", "score", "n", "pos")
            lCsv.append(oLine)
            # Get the concr object
            oConcr = json.loads(self.concr)
            # Process measures for the text as a whole
            score = "NiB" if oConcr['score'] == "NiB" else float(oConcr['score'])
            oLine = "{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                "(text)", "(text)", "(text)", "(the whole text)", score, oConcr['n'], "")
            lCsv.append(oLine)
            # Do paragraphs
            for idx_p, para in enumerate(oConcr['list']):
                # Output a line for the paragraph
                score = "NiB" if para['score'] == "NiB" else float(para['score'])
                oLine = "{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                    idx_p+1, "(para)", "(para)", para['paragraph'], score, para['n'], "")
                lCsv.append(oLine)
                # Do sentences
                for idx_s, sent in enumerate(para['list']):
                    # Output a line for the sentence
                    score = "NiB" if sent['score'] == "NiB" else float(sent['score'])
                    oLine = "{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                        idx_p+1, idx_s+1, "(sent)", sent['sentence'], score, sent['n'], "")
                    lCsv.append(oLine)
                    # Do words
                    for idx_w, word in enumerate(sent['list']):
                        # Output a line for the paragraph
                        score = "NiB" if word['concr'] == "NiB" else float(word['concr'])
                        oLine = "{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                            idx_p+1, idx_s+1, idx_w+1, word['lemma'], score, 1, word['pos_full'])
                        lCsv.append(oLine)
            # REturn the whole
            return "\n".join(lCsv)
        except:
            sMsg = oErr.get_error_message()
            oErr.DoError("FrogLink get_csv")
            return ""


class FoliaProcessor():
    """Functions to help create or process a folia document"""

    docstr = ""         # The identifier of this document
    username = ""       # The owner of this document
    dir = ""            # Directory for the output
    basicf = ""         # If any: where the basis folis is
    frogClient = None   
    frog = None
    doc = None
    re_single = None
    re_double = None

    def __init__(self, username):
        # Check and/or create the appropriate directory for the user
        dir = os.path.abspath(os.path.join( WRITABLE_DIR, "../folia", username))
        if not os.path.exists(dir):
            os.mkdir(dir)
        # Set the dir locally
        self.dir = dir
        # Set regex
        self.re_single = re.compile(u"[‘’´]")
        self.re_double = re.compile(u"[“”]")

        ## Check if we can create a client
        #try:
        #    self.frogClient = FrogClient('localhost', FROGPORT, returnall=True)
        #    # Send a word
        #    tuple = self.frogClient.process("hallo")
        #except:
        #    # There is no connection
        #    pass

        ## Check if [Frog] is local
        #try:
        #    self.frog = Frog(FrogOptions(parser=False))
        #except:
        #    pass

    def location(self):
        """Give the location we can work from: local, client or remote"""

        if self.frog != None:
            sBack = "local"
        elif self.frogClient != None:
            sBack = "client"
        else:
            sBack = "remote"
        return sBack

    def basis_folia(self, filename, data_contents):

        errHandle = ErrHandle()
        bReturn = False
        sMsg = ""
        try:
            # Read file into array
            lines = []
            bFirst = True
            for line in data_contents:
                sLine = line.decode("utf-8").strip()
                if bFirst:
                    sLine = sLine.replace(u'\ufeff', '')
                    bFirst = False
                # Change curly quotes
                sLine = self.re_single.sub("'", sLine)
                sLine = self.re_double.sub('"', sLine)
                # Insert a space before ".." or "..."
                sLine = sLine.replace("..", " ..")
                lines.append(sLine)

            # Check and/or create the appropriate directory for the user
            dir = self.dir

            # create a folia document with a numbered id
            docstr = os.path.splitext( os.path.basename(filename))[0].replace(" ", "_").strip()
            # Make sure we remember the docstr
            self.docstr = docstr

            # Start creating a folia document
            doc = folia.Document(id=docstr)
            text = doc.add(folia.Text)

            # Walk through the JSON 
            lFolia = []
            counter = 0
            for sLine in lines:
                # Check for empty
                sLine = sLine.strip()
                if sLine != "":
                    counter += 1
                    lFolia.append("{}: {}".format(counter, sLine))
                    # Append a paragraph
                    para = text.add(folia.Paragraph)

                    # NOTE: do *NOT* Set the <t> of this paragraph -- it will differ from what Folia calculates itself
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
            sMsg = "\n".join(lFolia)

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


class Brysbaert(models.Model):
    """Information from the Brysbaert list of concreteness

    Fields in the Excel:
       stimulus, List, Concrete_m, Concrete_sd, Number_of_ratings, Number_of_N-respones, Number_of_subjects
    """

    # [1] The lemma 
    stimulus = models.CharField("Lemma of word", max_length=MAXPARAMLEN)
    # [1] The list number
    list = models.IntegerField("List number", default=0)
    # [1] Metric 1: concrete_m
    m = models.FloatField("Concrete m", default=0.0)
    # [1] Metric 2: concrete_sd
    sd = models.FloatField("Concrete sd", default=0.0)
    # [1] Metric 3: Number_of_ratings
    ratings = models.FloatField("Number_of_ratings", default=0.0)
    # [1] Metric 4: Number_of_N-responses
    responses = models.FloatField("Number_of_N-responses", default=0.0)
    # [1] Metric 5: Number_of_subjects
    subjects = models.FloatField("Number_of_subjects", default=0.0)

    def __str__(self):
        return self.stimulus

    def get_concreteness(self):
        return self.m

    def find_or_create(stimulus, listnum, m, sd, ratings, responses, subjects):
        """Find existing or create new item"""
        
        obj = None
        sMsg = ""
        oErr = ErrHandle()
        try:
            obj = Brysbaert.objects.filter(stimulus=stimulus).first()
            if obj == None:
                obj = Brysbaert(stimulus=stimulus, list=listnum, m=m, sd=sd, ratings=ratings, responses=responses, subjects=subjects)
                obj.save()
        except:
            sMsg = oErr.get_error_message()
            oErr.DoError("find_or_create")
        # Return the result
        return obj, sMsg

    def clear():
        Brysbaert.objects.all().delete()
        return True


# ======================= NEXIS UNI =======================

class NexisDocs(models.Model):
    """Set of text files for Nexis research"""
    
    # [1] These belong to a particular user
    owner = models.ForeignKey(User, editable=False, on_delete=models.CASCADE, related_name="owner_nexisdocs")

    def __str__(self):
        return self.owner.username

    def get_obj(username):
        nd = None
        owner = User.objects.filter(username=username).first()
        if owner != None:
            nd = NexisDocs.objects.filter(owner=owner).first()
        return nd


class NexisBatch(models.Model):
    """A batch is a set of files that have been uploaded on a certain time"""

    # [1] Each Batch has been created at one point in time
    created = models.DateTimeField(default=timezone.now)
    # [0-1] Eatch batch has a number of files
    count = models.IntegerField("Number of files", default=0)
    # [1] Each batch belongs to a set of docs (that belong to an owner)
    ndocs = models.ForeignKey(NexisDocs, related_name="ndocsbatches", on_delete=models.CASCADE)

    def __str__(self):
        sBack = str(self.created)
        return sBack

    def create(username):
        """Possibly create a new batch for user [username]"""

        errHandle = ErrHandle()

        try:
            # Get the correct user
            owner = User.objects.filter(username=username).first()

            # Find a NexisDocs instance for this user
            fd = NexisDocs.objects.filter(owner=owner).first()
            if fd == None:
                fd = NexisDocs(owner=owner)
                fd.save()

            # Create it
            obj = NexisBatch(ndocs=fd)
            obj.save()
            # Return the result 
            return obj, ""
        except:
            errHandle.DoError("NexisBatch/create")
            return None, errHandle.get_error_message()


class NexisLink(models.Model):
    """Basic information from a Nexis text file: text + metadata"""

    # [1] Each froglink centers around a file that is uploaded, processed and made available
    name = models.CharField("Name to be used for this file", max_length=MAXPARAMLEN)
    # [0-1] Full name is the full path of the txt-file on the server
    fullname = models.CharField("Full path of this file", max_length=MAXPATH, null=True, blank=True)
    # [0-1] Text metadata as stringified JSON object
    nmeta = models.TextField("Nexis metadata", null=True, blank=True)
    # [0-1] Text body
    nbody = models.TextField("Nexis text", null=True, blank=True)
    # [1] Each Froglink has been created at one point in time
    created = models.DateTimeField(default=timezone.now)

    # [1] Each link belongs to a set of docs (that belong to an owner)
    ndocs = models.ForeignKey(NexisDocs, related_name="nexisdocuments", on_delete=models.CASCADE)
    # [1] Each nexislink should belong to a batch
    batch = models.ForeignKey(NexisBatch, null=True, on_delete=models.CASCADE, related_name="batchlinks")

    def __str__(self):
        return self.name

    def create(name, username, batch):
        """Possibly create a new item [name] for user [username]"""

        errHandle = ErrHandle()

        try:
            # Get the correct user
            owner = User.objects.filter(username=username).first()

            # Find a NexisDocs instance for this user
            fd = NexisDocs.objects.filter(owner=owner).first()
            if fd == None:
                fd = NexisDocs(owner=owner)
                fd.save()

            #obj = NexisLink.objects.filter(name=name).first()
            #if obj == None:
            # Just always Create it
            obj = NexisLink(name=name, ndocs=fd, batch=batch)
            obj.save()
            # Return the result 
            return obj, ""
        except:
            errHandle.DoError("NexisLink/create")
            return None, errHandle.get_error_message()

    def read_doc(self, username, data_file, filename, arErr, xmldoc=None, sName = None, oStatus = None):
        """Import a text file, split in text and metadata and store that in the NexisLink instance
        
        The syntax of a file:
            <nexisdoc> := <metadata> <body> <footer>

            <metadata> := <title> <newspaper> <date> <copyright> <meta>*

            <title> := $line NL
            <newspaper> := $line NL
            <date> := $line NL
            <copyright := $line NL

            <meta> := <keyword> ':' <metatext> NL
            <keyword> := 'Section' | 'Length' | 'Byline' | 'Highlight' |'Dateline'
            <metatext> := $line ( NL $line )*

            <body> := 'Body' NL ( $line NL )*

            <footer> := <loaddate> <eod>
            <loaddate> := ‘Load-Date:’ $line NL
            <eod> := ‘End of Document’ NL
        """

        def skip_empty_lines(lst, idx):
            while idx < len(lst) and lst[idx] == "": idx += 1
            return idx

        def get_anywhere(lst, must, start_from = 0, eow=False, year=False):
            bFound = False
            item_found = None
            index_found = -1
            for idx, item in enumerate(lst[start_from:]):
                if bFound:
                    # index_found = idx + start_from
                    break
                item_lower = item.lower()
                for m in must:
                    if m in item_lower: 
                        if eow:
                            pattern = r'.*{}\s*$'.format(m)
                            if re.match(pattern, item_lower):
                                bFound = True
                                item_found = item
                                index_found = idx + start_from
                                break
                        elif year:
                            pattern = r'.*\d\d\d\d\s*.*$'
                            if re.match(pattern, item_lower):
                                bFound = True
                                item_found = item
                                index_found = idx + start_from
                                break
                        else:
                            bFound = True
                            item_found = item
                            index_found = idx + start_from
                            break
            # Found anything?
            index_found += 1
            return bFound, item_found, index_found

        def get_line_item(lst, idx, inside = None, must = None):
            item = lst[idx]
            # Is there a 'must'?
            if must != None:
                bFound = False
                item_lower = item.lower()
                for m in must:
                    if m in item_lower: 
                        bFound = True
                        break
                if not bFound:
                    # Check if we can find it from here
                    idx_local = idx + 1
                    while idx_local < len(lst) and not bFound:
                        item = lst[idx_local]
                        item_lower = item.lower()
                        bFound = False
                        for m in must:
                            if m in item_lower: 
                                bFound = True
                                break
                        if not bFound:
                            idx_local += 1
                    if not bFound:
                        return idx, None
            elif inside != None:
                # Check if we can append to [item] from the next non-empty line
                bReady = False
                bFound = False
                while not bReady:
                    # GO to next non-empty line
                    idy = skip_empty_lines(lst, idx+1)
                    # Check if the contents is inside [inside]
                    if lst[idy] not in inside:
                        bReady = True
                    else:
                        idx = idy
                        bFound = True
                # Has something been found?
                if not bFound:
                    return idx, None

            # Skip any following empty lines
            idx = skip_empty_lines(lst, idx+1)
            # Return the index of the first non-empty line + the item we found
            return idx, item

        def get_line_meta(lst, idx):
            key = ""
            value = ""
            try:
                item = lst[idx]
                if ":" in item:
                    colon = item.index(":")
                    key = item[:colon]
                    value = item[colon+1:].strip()
                    # Go to the next line
                    idx += 1
                    # Check if the next line is not empty
                    while idx < len(lst) and lst[idx] != "" and ":" not in lst[idx]:
                        value = "{} {}".format(value, lst[idx])
                        idx += 1
                    while idx < len(lst) and lst[idx] == "": idx += 1

                return idx, key, value
            except:
                sError = errHandle.get_error_message()
                return -1, "", ""

        oBack = {'status': 'ok', 'count': 0, 'msg': "", 'user': username}
        errHandle = ErrHandle()
        oDoc = None
        iCount = 0
        inputType = "nexistext"
        nexisProc = NexisProcessor(username)
        day = ['maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag',
               'monday', 'tuesday', 'wednesday', 'thursday','friday', 'saturday', 'sunday']
        paper = ['telegraaf', 'dagblad', 'handelsblad', 'trouw', 'volkskrant', 'nrc.next', 'nrc']
        copyright = ['copyright']
        highlight = ['highlight:']
        byline = ['byline:']
        section = ['section:']

        nexis_filename = ""

        try:
            # Provide the right nexis filename
            nexis_filename = "nexislink_{}.txt".format(str(self.id).zfill(6))

            # Read and create basis-folia
            # Note: changed from [filename] to [nexis_filename]
            oResult = nexisProc.basis_text(nexis_filename, data_file)
            if not oResult['okay']:
                # There was some kind of error
                oBack['status'] = 'error'
                oBack['msg'] = "basis_text load error: {}".format( oResult['msg'])
            else:
                # DEBUG: show the frog location
                errHandle.Status("DEBUG: basis_text has been read")

                # Get the metadata and the body
                lst_meta = oResult['metadata']
                lst_body = oResult['body']

                # Process the metadata
                oMeta = {}
                bTitle = False
                # Add all the metadata 
                oMeta['raw'] = "\n".join(lst_meta)
                # Skip empty lines
                iLine = skip_empty_lines(lst_meta, 0)
                # Get the title, newspaper, date and copyright
                iLine, oMeta['title'] = get_line_item(lst_meta, iLine, inside=filename)
                if oMeta['title'] == None: 
                    oMeta['title'] = filename.replace(".txt", "")
                else:
                    bTitle = True
                
                bFound, oMeta['newspaper'], iLine = get_anywhere(lst_meta, must=paper, eow=True) # , start_from=iLine+1)
                if oMeta['newspaper'] == None:
                    oMeta['newspaper'] = "(Unknown newspaper)"
                elif not bTitle:
                    # See if he previous position has the title
                    if lst_meta[iLine-2] != "":
                        oMeta['title'] = lst_meta[iLine-2]

                bFound, oMeta['newsdate'], iLine = get_anywhere(lst_meta, must=day, year=True)
                # iLine, oMeta['newsdate'] = get_line_item(lst_meta, iLine, must=day)
                if oMeta['newsdate'] == None:
                    oMeta['newsdate'] = "(Cannot find the news date)"
                elif "Unknown" in oMeta['newspaper']:
                    # Take the newspaper as the line immediately preceding the newsdate
                    oMeta['newspaper'] = lst_meta[iLine-2]
                    if not bTitle and lst_meta[iLine-3] != "":
                        oMeta['title'] = lst_meta[iLine-3]

                bFound, oMeta['copyright'], iLine = get_anywhere(lst_meta, must=copyright)
                # iLine, oMeta['copyright'] = get_line_item(lst_meta, iLine, must=copyright)
                if oMeta['copyright'] == None:
                    oMeta['copyright'] = "(no copyright line)"

                # Get any more metadata, starting from the first line with colon
                iLine = 1
                while iLine < len(lst_meta) and not ":" in lst_meta[iLine]:
                    iLine += 1
                while iLine < len(lst_meta) and ":" in lst_meta[iLine]:
                    # Extract one meta element
                    iLine, key, value = get_line_meta(lst_meta, iLine)
                    # NOTE: the key must not contain a space
                    if key != "" and value != "" and not " " in key:
                        oMeta[key.lower()] = value
                # Any last line left?
                if iLine == len(lst_meta)-1 and ":" not in lst_meta[iLine]:
                    # There is still one final line -- not sure what that is though
                    oMeta['last'] = lst_meta[iLine]

                self.nmeta = json.dumps( oMeta)
                self.nbody = "\n".join(lst_body)
                self.save()
                iCount += 1
                oBack['name'] = self.name
                oBack['title'] = oMeta['title']

            # Make sure the requester knows how many have been added
            oBack['count'] = iCount   # The number of files added

        except:
            sError = errHandle.get_error_message()
            oBack['status'] = 'error'
            oBack['msg'] = sError

        # Return the object that has been created
        return oBack
    

class NexisProcessor():
    """Functions to help create or process a nexis uni document"""

    docstr = ""         # The identifier of this document
    username = ""       # The owner of this document
    dir = ""            # Directory for the output
    basicf = ""         # If any: where the basis folia is
    frogClient = None   
    frog = None
    doc = None
    re_single = None
    re_double = None
    bDebug = True

    def __init__(self, username):
        # Check and/or create the appropriate directory for the user
        dir = os.path.abspath(os.path.join( WRITABLE_DIR,  "../nexis", username))
        if not os.path.exists(dir):
            os.mkdir(dir)
        # Set the dir locally
        self.dir = dir
        # Set regex
        self.re_single = re.compile(u"[‘’´]")
        self.re_double = re.compile(u"[“”]")

    def basis_text(self, filename, data_contents):

        errHandle = ErrHandle()
        oBack = dict(okay=True)
        try:
            errHandle.Status("NexisProcessor: {}".format(filename))
            # Read file into array
            lines = []
            bFirst = True
            idx = 0
            for line in data_contents:
                idx += 1
                # ===================================================
                if self.bDebug:
                    errHandle.Status("[{}]: [{}]".format(idx, line))
                # ===================================================
                sLine = line.decode("utf-8").strip()
                if bFirst:
                    sLine = sLine.replace(u'\ufeff', '')
                    bFirst = False
                # Change curly quotes
                sLine = self.re_single.sub("'", sLine)
                sLine = self.re_double.sub('"', sLine)
                # Insert a space before ".." or "..."
                sLine = sLine.replace("..", " ..")
                lines.append(sLine)

            # Check and/or create the appropriate directory for the user
            dir = self.dir

            # ===================================================
            if self.bDebug:
                # Save the file just to be sure
                save_name = os.path.abspath(os.path.join(dir, filename))
                with open(save_name, "w", encoding = "utf-8") as fd:
                    fd.write("\n".join(lines))
            # ===================================================

            ## create a folia document with a numbered id
            #docstr = os.path.splitext( os.path.basename(filename))[0].replace(" ", "_").strip()
            ## Make sure we remember the docstr
            #self.docstr = docstr

            # Split into metadata and body
            iBodyStart = -1
            iBodyEnd = -1
            iLoadDate = -1
            iMetaEnd = -1
            loaddate = None
            end_of_text = []    # Array of possible end-of-text indexes
                                # (idea of Joost Grunwald)
            for idx, line in enumerate(lines):
                if line.startswith( "Body"):
                    iBodyStart = idx + 1
                    while lines[iBodyStart] == "":
                        iBodyStart += 1
                    iMetaEnd = idx - 1
                elif line.startswith("End of Document"):
                    # iBodyEnd = idx - 1
                    end_of_text.append(idx - 1)
                elif line.startswith("Bekijk de oorspronkelijke pagina"):
                    end_of_text.append(idx - 1)
                elif line.startswith("* Vervangende titel"):
                    # Issue #137: check for replacement title
                    end_of_text.append(idx - 1)
                elif line.startswith("Load-Date:"):
                    iLoadDate = idx - 1
                    colon = line.index(":") + 1
                    loaddate = line[colon:].strip()
                    end_of_text.append(idx - 1)
            # If there is a loaddate, then that is the end of the body
            # Determine the best candidate for the end-of-text
            if len(end_of_text) == 0:
                iBodyEnd = iBodyStart
            else:
                # Take the highest index in the list
                end_of_text.sort()
                iBodyEnd = end_of_text[0]
            # if iLoadDate >= 0: iBodyEnd = iLoadDate

            # Get the Meta and the body
            oBack['metadata'] = lines[:iMetaEnd]
            oBack['body'] = lines[iBodyStart:iBodyEnd]
            oBack['loaddate'] = loaddate

            # Issue #137: check for replacement title
            for idx, line in enumerate(oBack['body']):
                if "* vervangende titel" in line.lower():
                    # Get the previous line
                    alt_title = oBack['body'][idx-1]
                    oBack['body'].pop(idx)
                    oBack['body'].pop(idx-1)
                    oBack['metadata'].append('alt_title: {}'.format(alt_title))
                    break
            # Issuee #139: Look for Graphic
            if iBodyEnd < len(lines):
                for idx, line in enumerate(lines[iBodyEnd+1:]):
                    if line.startswith("Graphic"):
                        # Skip empty lines
                        bFound = False
                        start = iBodyEnd + 1 + idx 
                        for line_next in lines[start+1:]:
                            if line_next != "":
                                oBack['metadata'].append('graphic: {}'.format(line_next))
                                bFound = True
                                break
                        if bFound:
                            break
        except:
            oBack['msg'] = errHandle.get_error_message()
            errHandle.DoError("basis_text")
            oBack['okay'] = False
        # Return what has happened
        return oBack
