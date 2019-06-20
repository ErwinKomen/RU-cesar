import os
import sys
import time
import json
import re
import copy
from io import StringIO 
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from cesar.utils import ErrHandle
from cesar.seeker.models import import_data_file
from cesar.settings import WRITABLE_DIR

# XML processing
from xml.dom import minidom

# FOlia handling: pynlpl
import pynlpl
# from pynlpl.formats import folia
from pynlpl.textprocessors import tokenize, split_sentences
from pynlpl.clients.frogclient import FrogClient

# New folia: FOliaPy
import folia.main as folia


# Attempt to input FROG
try:
    from frog import Frog, FrogOptions
    # See: https://frognlp.readthedocs.io/en/latest/pythonfrog.html
except:
    # It is not there...
    frogurl = "https://webservices-lst.science.ru.nl/frog"
    from clam.common.client import *


MAXPARAMLEN = 100
MAXPATH = 256
FROGPORT = 8020

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
    fdocs = models.ForeignKey(FoliaDocs, related_name="documents")
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

    def read_doc(self, username, data_file, filename, clamuser, clampw, arErr, xmldoc=None, sName = None, oStatus = None):
        """Import a text file, parse it through the frogger, and create a Folia.xml file"""

        oBack = {'status': 'ok', 'count': 0, 'msg': "", 'user': username}
        errHandle = ErrHandle()
        oDoc = None
        iCount = 0
        inputType = "folia"
        frogType = "remote"     # Fix to remote -- or put to None if automatically choosing

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

                # Action depends on the [froglocation]
                if frogLoc == "client" or frogLoc == "local":
                    doc = folProc.doc
                    # Add annotation layers
                    doc.declare(folia.PosAnnotation, 'http://ilk.uvt.nl/folia/sets/frog-mbpos-cgn', 
                                annotator='frog', annotatortype=folia.AnnotatorType.AUTO)
                    doc.declare(folia.LemmaAnnotation, 'http://ilk.uvt.nl/folia/sets/frog-mblem-nl', 
                                annotator='frog', annotatortype=folia.AnnotatorType.AUTO)
                    doc.declare(folia.MorphologyLayer, 'http://ilk.uvt.nl/folia/sets/frog-mbma-nl', 
                                annotator='frog', annotatortype=folia.AnnotatorType.AUTO)
                    # Iterate over paragraphs
                    for paragraph in doc.paragraphs():
                        # Iterate over all the sentences
                        for sentence in paragraph.sentences():
                            # Get the text of this sentence
                            sLine = sentence.text()
                            # Process it
                            bOkay, lSent = folProc.parse_sentence(sLine, frogLoc)
                            if not bOkay:
                                if len(lSent) == 0:
                                    sError = "FrogLink read_doc: unknown error"
                                else:
                                    sError = lSent[0]
                                oBack['status'] = 'error'
                                oBack['msg'] = sError
                                return oBack

                            # Add the annotation to the words in the sentence
                            # Walk the tokens in the sentence and add this information
                            for idx, oWord in enumerate(sentence.words()):
                                # Get the corresponding parse
                                parse = lSent[idx]
                                # Add POS annotation
                                sPosFull = parse['pos']
                                sPosHead = sPosFull.split("(")[0]
                                pos = oWord.add(folia.PosAnnotation, cls=sPosFull, head=sPosHead)
                                # Add lemma
                                lemma = oWord.add(folia.LemmaAnnotation, cls=parse['lemma'])
                                # Add morph
                                mlayer = oWord.add(folia.MorphologyLayer)
                                # The morphemes are enclosed in [...] brackets
                                arMorph = parse['morph'].strip("[]").split("][")
                                for m in arMorph:
                                    mitem = mlayer.add(folia.Morpheme)
                                    mitem.settext(m)
                    # Think of a name to save it
                    folia_out = folProc.basicf.replace(".basis", ".folia")
                    # Write it away
                    doc.save(folia_out)
                    # Note where it is
                    self.fullname = folia_out
                    self.save()
                elif frogLoc == "remote":
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
        dir = os.path.abspath(os.path.join( WRITABLE_DIR, username))
        if not os.path.exists(dir):
            os.mkdir(dir)
        # Set the dir locally
        self.dir = dir
        # Set regex
        self.re_single = re.compile(u"[‘’´]")
        self.re_double = re.compile(u"[“”]")

        # Check if we can create a client
        try:
            self.frogClient = FrogClient('localhost', FROGPORT, returnall=True)
            # Send a word
            tuple = self.frogClient.process("hallo")
        except:
            # There is no connection
            pass

        # Check if [Frog] is local
        try:
            self.frog = Frog(FrogOptions(parser=False))
        except:
            pass

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
            for sLine in lines:
                # Check for empty
                sLine = sLine.strip()
                if sLine != "":
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

    def parse_sentence(self, sSentence, sType):
        """Process one sentence and return appropriate JSON"""

        oErr = ErrHandle()
        parsed_output = []
        try:
            # Action depends on sType
            if sType == "client":
                if not self.frogClient:
                    return False, []
                # This produces one chunk of FoLiA
                tuple_list = self.frogClient.process(sSentence)
                for item in tuple_list:
                    # Take apart the tuple into an object
                    obj = {}
                    if len(item) > 4:
                        # We have almost all information
                        obj['text'] = item[0]
                        obj['lemma'] = item[1]
                        obj['morph'] = item[2]
                        obj['pos'] = item[3]
                        obj['ner'] = item[4]
                        obj['chunker'] = item[5]
                        obj['head'] = item[6]
                        obj['drel'] = item[7]
                    else:
                        # We only have: text, lemma, morph, pos
                        obj['text'] = item[0]
                        obj['lemma'] = item[1]
                        obj['morph'] = item[2]
                        obj['pos'] = item[3]
                    parsed_output.append(obj)
            elif sType == "local":
                token_list = frog.process(sLine)
                # Copy to parsed_output
                parsed_output = json.loads(json.dumps(token_list))
            else:
                return False, []
            # REturn the total parsed output
            return True, parsed_output
        except:
            sMsg = oErr.get_error_message()
            oErr.DoError("parse_sentence")
            return False, [sMsg]
        

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