"""Models for the BROWSER app.

The browser allows browsing through XML files that are part of a corpus.
A corpus is in a particular language and according to a particular tagset.
The information here mirrors (and extends) the information in the crp-info.json file.
"""
from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.functions import Lower
from datetime import datetime
from cesar.utils import *
from cesar.browser.services import *
from cesar.settings import APP_PREFIX
import sys
import copy
import json

MAX_IDENTIFIER_LEN = 10
MAX_TEXT_LEN = 200

CORPUS_LANGUAGE = "corpus.language"
CORPUS_ETHNO = "corpus.ethnologue"
CORPUS_STATUS = "corpus.status"
CORPUS_FORMAT = "corpus.format"
VARIABLE_TYPE = "variable.type"
VARIABLE_LOC = "variable.loc"
LANGUAGE = "language"

# ============================= LOCAL CLASSES ======================================
errHandle = ErrHandle()

class FieldChoice(models.Model):

    field = models.CharField(max_length=50)
    english_name = models.CharField(max_length=100)
    dutch_name = models.CharField(max_length=100)
    abbr = models.CharField(max_length=20, default='-')
    machine_value = models.IntegerField(help_text="The actual numeric value stored in the database. Created automatically.")

    def __str__(self):
        return "{}: {}, {} ({})".format(
            self.field, self.english_name, self.dutch_name, str(self.machine_value))

    class Meta:
        ordering = ['field','machine_value']

def build_choice_list(field, position=None, subcat=None, maybe_empty=False):
    """Create a list of choice-tuples"""

    choice_list = [];
    unique_list = [];   # Check for uniqueness

    try:
        # check if there are any options at all
        if FieldChoice.objects == None:
            # Take a default list
            choice_list = [('0','-'),('1','N/A')]
            unique_list = [('0','-'),('1','N/A')]
        else:
            if maybe_empty:
                choice_list = [('0','-')]
            for choice in FieldChoice.objects.filter(field__iexact=field):
                # Default
                sEngName = ""
                # Any special position??
                if position==None:
                    sEngName = choice.english_name
                elif position=='before':
                    # We only need to take into account anything before a ":" sign
                    sEngName = choice.english_name.split(':',1)[0]
                elif position=='after':
                    if subcat!=None:
                        arName = choice.english_name.partition(':')
                        if len(arName)>1 and arName[0]==subcat:
                            sEngName = arName[2]

                # Sanity check
                if sEngName != "" and not sEngName in unique_list:
                    # Add it to the REAL list
                    choice_list.append((str(choice.machine_value),sEngName));
                    # Add it to the list that checks for uniqueness
                    unique_list.append(sEngName)

            choice_list = sorted(choice_list,key=lambda x: x[1]);
    except:
        print("Unexpected error:", sys.exc_info()[0])
        choice_list = [('0','-'),('1','N/A')];

    # Signbank returns: [('0','-'),('1','N/A')] + choice_list
    # We do not use defaults
    return choice_list;

def build_abbr_list(field, position=None, subcat=None, maybe_empty=False):
    """Create a list of choice-tuples"""

    choice_list = [];
    unique_list = [];   # Check for uniqueness

    try:
        # check if there are any options at all
        if FieldChoice.objects == None:
            # Take a default list
            choice_list = [('0','-'),('1','N/A')]
            unique_list = [('0','-'),('1','N/A')]
        else:
            if maybe_empty:
                choice_list = [('0','-')]
            for choice in FieldChoice.objects.filter(field__iexact=field):
                # Default
                sEngName = ""
                # Any special position??
                if position==None:
                    sEngName = choice.english_name
                elif position=='before':
                    # We only need to take into account anything before a ":" sign
                    sEngName = choice.english_name.split(':',1)[0]
                elif position=='after':
                    if subcat!=None:
                        arName = choice.english_name.partition(':')
                        if len(arName)>1 and arName[0]==subcat:
                            sEngName = arName[2]

                # Sanity check
                if sEngName != "" and not sEngName in unique_list:
                    # Add it to the REAL list
                    choice_list.append((str(choice.abbr),sEngName));
                    # Add it to the list that checks for uniqueness
                    unique_list.append(sEngName)

            choice_list = sorted(choice_list,key=lambda x: x[1]);
    except:
        print("Unexpected error:", sys.exc_info()[0])
        choice_list = [('0','-'),('1','N/A')];

    # Signbank returns: [('0','-'),('1','N/A')] + choice_list
    # We do not use defaults
    return choice_list;

def choice_english(field, num):
    """Get the english name of the field with the indicated machine_number"""

    try:
        result_list = FieldChoice.objects.filter(field__iexact=field).filter(machine_value=num)
        if (result_list == None):
            return "(No results for "+field+" with number="+num
        return result_list[0].english_name
    except:
        return "(empty)"

def choice_value(field, term):
    """Get the numerical value of the field with the indicated English name"""

    try:
        result_list = FieldChoice.objects.filter(field__iexact=field).filter(english_name__iexact=term)
        if result_list == None or result_list.count() == 0:
            # Try looking at abbreviation
            result_list = FieldChoice.objects.filter(field__iexact=field).filter(abbr__iexact=term)
        if result_list == None:
            return -1
        else:
            return result_list[0].machine_value
    except:
        return -1

def choice_abbreviation(field, num):
    """Get the abbreviation of the field with the indicated machine_number"""

    try:
        result_list = FieldChoice.objects.filter(field__iexact=field).filter(machine_value=num)
        if (result_list == None):
            return "{}_{}".format(field, num)
        return result_list[0].abbr
    except:
        return "-"

def m2m_combi(items):
    if items == None:
        sBack = ''
    else:
        qs = items.all()
        sBack = '-'.join([str(thing) for thing in qs])
    return sBack

def m2m_namelist(items):
    if items == None:
        sBack = ''
    else:
        qs = items.all()
        sBack = ' || '.join([thing.name for thing in qs])
    return sBack

def m2m_identifier(items):
    if items == None:
        sBack = ''
    else:
        qs = items.all()
        sBack = "-".join([thing.identifier for thing in qs])
    return sBack

def get_instance_copy(item, commit=True):
    new_copy = copy.copy(item)
    new_copy.id = None          # Reset the id
    if commit:
        try:
            new_copy.save()             # Save it preliminarily
        except:
            e = sys.exc_info()[0]
            iStop = 1
    return new_copy

def copy_m2m(inst_src, inst_dst, field, **kwargs):
    # Copy M2M or one-to-many relationship  
    item_list = getattr(inst_src, field).all()  
    back_list = []
    for item in item_list:
        newItem = item.get_copy(**kwargs)
        # x = inst_src.definitionvariables.all()
        # Possibly copy more m2m
        if kwargs is not None and 'lst_m2m' in kwargs:
            # Get the list of stuff
            lst_m2m = kwargs['lst_m2m']
            # Remove the field from kwargs
            del kwargs['lst_m2m']
            # Walk the list
            for deeper in lst_m2m:
                copy_m2m(item, newItem, deeper, **kwargs)
        getattr(inst_dst, field).add(newItem)
        back_list.append({'src': item, 'dst': newItem})
    return back_list

def copy_fk(inst_src, inst_dst, field):
    # Copy foreign-key relationship
    instSource = getattr(inst_src, field)
    if instSource != None:
        # instCopy = get_instance_copy(instSource)
        instCopy = instSource.get_copy()
        setattr(inst_dst, field, instCopy)

def get_ident(qs):
    if qs == None:
        idt = ""
    else:
        lst = qs.all()
        if len(lst) == 0:
            idt = "(empty)"
        else:
            qs = lst[0].collection_set
            idt = m2m_identifier(qs)
    return idt

def get_tuple_value(lstTuples, iId):
    if lstTuples == None:
        sBack = ""
    else:
        lstFound = [item for item in lstTuples if item[0] == iId]
        if len(lstFound) == 0:
            sBack = ""
        else:
            sBack = lstFound[0][1]
    return sBack

def get_tuple_index(lstTuples, sValue):
    if lstTuples == None:
        iBack = -1
    else:
        lstFound = [item for item in lstTuples if item[1] == sValue]
        if len(lstFound) == 0:
            iBack = -1
        else:
            iBack = lstFound[0][0]
    return iBack

def get_format_name(iFormat):
    return choice_english(CORPUS_FORMAT, iFormat)

class Status(models.Model):
    """Intermediate loading of /crpp information and status of processing it"""

    # [1] Status of the process
    status = models.CharField("Status of synchronization", max_length=50)
    # [1] Counts (as stringified JSON object)
    count = models.TextField("Count details", default="{}")
    # [0-1] Synchronisation type
    type = models.CharField("Type", max_length=255, default="")
    # [0-1] User
    user = models.CharField("User", max_length=255, default="")
    # [0-1] Error message (if any)
    msg = models.TextField("Error message", blank=True, null=True)

    def __str__(self):
        # Refresh the DB connection
        self.refresh_from_db()
        # Only now provide the status
        return self.status

    def set(self, sStatus, oCount = None, msg = None):
        self.status = sStatus
        if oCount != None:
            self.count = json.dumps(oCount)
        if msg != None:
            self.msg = msg
        self.save()

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def get_text_from_txtlist(arList, sFileName, idx):
    """Retrieve text [sFileName] from arList"""
    oBack = None
    oErr = ErrHandle()
    try:
        if idx < len(arList):
            # Start searching frim [idx] onwards
            oText = arList[idx]
            while oText['name'] != sFileName:
                idx += 1
                oText = arList[idx]
            if oText['name'] == sFileName:
                return oText, idx
    except:
        sMsg = oErr.get_error_message()
        oErr.DoError("get_text_from_txtlist: " + sMsg)
        oBack = None
    return oBack, idx

def sort_texts_from_txtlist(oTxtList):
    """Retrieve texts from oTxtList and sort them"""
    arList = []
    oErr = ErrHandle()
    try:
        for oPath in oTxtList['txtlist']:
            # Process this patth
            sPath = oPath['path']
            iPathCount = oPath['count']
            for item in oPath['list']:
                item['path'] = sPath
                item['count'] = iPathCount
                # Add to arlist
                arList.append(item)
        # Now sort
        arList.sort(key=lambda item: item['name'].lower())
    except:
        sMsg = oErr.get_error_message()
        oErr.DoError("sort_texts_from_txtlist: " + sMsg)
        arList = []
    return arList


def process_textlist(oTxtlist, part, sFormat, oStatus, options):
    """Update our own models with the information in [oCorpusInfo]"""

    oBack = {}      # What we return
    lOblig = ['name', 'size', 'words', 'title', 'date', 'author', 'genre', 'subtype']
    bNoDeleting = False
    bUpdating = False
    sUpdateField = ""

    # Get the value for format
    format_choice = choice_value(CORPUS_FORMAT, sFormat)

    if 'nodeleting' in options:
        bNoDeleting = options['nodeleting']
    if 'updating' in options:
        bUpdating = options['updating']
    if 'update_field' in options:
        sUpdateField = options['update_field']

    def has_oblig_fields(oItem):
        for sField in lOblig:
            if not sField in oItem:
                return False
        return True

    try:
        # Debugging
        errHandle.Status("Process_textlist nodeleting={} updating={} update_field={}".format(bNoDeleting, bUpdating, sUpdateField))

        # Update the synchronisation object that contains all relevant information
        oBack['lng'] = part.corpus.get_lng_display()
        oBack['part'] = part.name
        oBack['format'] = sFormat
        oStatus.set("copying", oBack)

        # Validate the [oTxtList] object
        if oTxtlist == None or not 'paths' in oTxtlist or not 'count' in oTxtlist:
            # We miss information
            oStatus.set("error", msg="information is missing (paths, count)")
            return oBack

        # Take the genre and the subtype lists
        lGenre = oTxtlist['genre']
        lSubtype = oTxtlist['subtype']

        # Initialise what we return
        oBack = {'result': False, 'parts': 0, 
                 'paths': oTxtlist['paths'],
                 'total': oTxtlist['count']}

        # Prepare 
        qs_texts = Text.objects.filter(format=format_choice,part=part).order_by(Lower('fileName'))
        if qs_texts.count() == 0:
            bUpdating = False

        if bUpdating :
            # ================= ONLY UPDATE EXISTING ================
            oBack['language'] =  part.corpus.get_lng_display()
            oBack['format']   = sFormat
            oStatus.set("bulk update", oBack)

            # Look for the texts that need to be visited
            qs_iter = qs_texts.iterator()

            # Sort the texts in oTxtList in an array
            arList = sort_texts_from_txtlist(oTxtlist)
            idx_list = 0

            # Establish the chunk parameters
            iChunk = 0
            iChunkSize = 100
            iChunkLen = qs_texts.count() // iChunkSize + 1
            iNum = 0

            # Iterate through the Text instances
            text = next(qs_iter)
            for chunk_this in range(iChunkLen):
                iChunk += 1
                # Walk this chunk
                sChunkMsg = "process_textlist u {} (of {})".format(iChunk, iChunkLen)
                oBack['chunk'] = sChunkMsg

                # ====== DEBUG ========
                # Log what we are doing in the output
                errHandle.Status(sChunkMsg)
                # =====================

                # Show what is going on
                oStatus.set("updating", oBack)
                with transaction.atomic():
                    for idx in range(iChunkSize):
                        if text != None:
                            # Find this text in [oTxtlist]
                            oText, idx_list = get_text_from_txtlist(arList, text.fileName, idx_list)
                            if oText == None:
                                oStatus.set("error")
                                errHandle.DoError("Cannot find text ["+text.fileName+"]")
                                return oBack
                            else:
                                if sUpdateField == "":
                                    # No idea what to do now
                                    pass
                                elif sUpdateField == "words" and text.words == 0:
                                    text.words = oText['words']
                                    text.save()
                                    oBack['file'] = text.fileName
                                    iNum += 1
                                    oBack['updated'] = iNum

                            # Get to the next text
                            try:
                                text = next(qs_iter)
                            except StopIteration as e:
                                break
                # Show what is going on
                oStatus.set("updating", oBack)

            sChunkMsg = "process_textlist updated the wordcounts of {} texts".format(iNum)
            errHandle.Status(sChunkMsg)
        else:
            
            # Walk all the different paths
            for oPath in oTxtlist['txtlist']:
                # Process this patth
                sPath = oPath['path']
                iPathCount = oPath['count']
                arList = oPath['list']

                # Debugging
                errHandle.Status("Process_textlist path={} ".format(sPath))

                # Remove all texts adhering to the specifications
                lstText = []
                oBack['part'] = part.name
                oBack['format'] = sFormat
                oStatus.set("deleting", oBack)
                # Do the deleting in chunks of 100
                lenArList = len(arList)
                # chunk_arList = chunks(arList, 100)

                # ================ DELETE OLD STUFF =========================
                if not bNoDeleting:
                    for chunk_this in chunks(arList, 100):

                        with transaction.atomic():
                            for oText in chunk_this:

                                # Debugging
                                errHandle.Status("Process_textlist deleting step #1 {}".format(oText['name']))

                                # Validate
                                if has_oblig_fields(oText):
                                    # check if it is in [Text] already
                                    lMatches = Text.objects.filter(fileName=oText['name'], format=format_choice,
                                                    part=part, title=oText['title'], lines=oText['size'],
                                                    words=oText['words'], date=oText['date'], author=oText['author'],
                                                    genre=lGenre[oText['genre']], subtype=lSubtype[oText['subtype']])
                                    oBack['file'] = oText['name']
                                    # Walk through all results
                                    for oMatch in lMatches:
                                        # Debugging
                                        errHandle.Status("Process_textlist deleting step #2 {} Text.id={}".format(oText['name'], oMatch.id))

                                        # Delete this result (this also includes deleting the related [Sentence] entry)
                                        oMatch.delete()
                        # Show what is happening
                        oStatus.set("deleting", oBack)

                if bUpdating:
                    # ================= ONLY UPDATE EXISTING ================
                    oBack['language'] =  part.corpus.get_lng_display()
                    oBack['part'] =  "{}: {}".format(part.dir, sPath)
                    oBack['format'] = sFormat
                    oStatus.set("bulk update", oBack)
                    iChunk = 0
                    iChunkLen = len(arList) // 100 + 1
                    for chunk_this in chunks(arList, 100):
                        iChunk += 1
                        oBack['chunk'] = "{} (of {})".format(iChunk, iChunkLen)
                        with transaction.atomic():
                            for oText in chunk_this:
                                # Validate
                                if has_oblig_fields(oText):
                                    # Find the instance to be updated
                                    instance = Text.objects.filter(fileName=oText['name'], format=format_choice,part=part).first()
                                    if instance == None:
                                        oStatus.set("error")
                                        errHandle.DoError("Cannot find text ["+oText['name']+"]")
                                        return oBack
                                    else:
                                        if sUpdateField == "":
                                            # No idea what to do now
                                            pass
                                        elif sUpdateField == "words":
                                            instance.words = oText['words']
                                            instance.save()
                                            oBack['file'] = oText['name']
                                else:
                                    # Not all fields were there in the [oText] we encountered
                                    oBack['note'] = "Did not find all obl fields in {} [{}]".format(oText['name'], sFormat)
                                    oStatus.set("error", oBack)
                        # Show what is going on
                        oStatus.set("updating", oBack)
                    # We are ready with this part
                    oBack['parts'] += 1
                    oBack['paths'] += 1

                else:
                    # ================= BULK CREATE NEW =====================
                    # Keep the transactions together in a bulk edit
                    lstText = []
                    oBack['language'] =  part.corpus.get_lng_display()
                    oBack['part'] =  "{}: {}".format(part.dir, sPath)
                    oBack['format'] = sFormat
                    oStatus.set("bulk add", oBack)
                    iChunk = 0
                    iChunkLen = len(arList) // 100
                    for chunk_this in chunks(arList, 100):
                        iChunk += 1
                        oBack['chunk'] = "{} (of {})".format(iChunk, iChunkLen)
                        with transaction.atomic():
                            for oText in chunk_this:
                                # Validate
                                if has_oblig_fields(oText):
                                    # if 'name' in oText and 'size' in oText and 'title' in oText and 'date' in oText and 'author' in oText and 'genre' in oText and 'subtype' in oText:
                                    try:
                                        oNew = Text(fileName=oText['name'], format=format_choice,
                                                    part=part, title=oText['title'], lines=oText['size'],
                                                    words=oText['words'], date=oText['date'], author=oText['author'],
                                                    genre=lGenre[oText['genre']], subtype=lSubtype[oText['subtype']])
                                    except:
                                        oStatus.set("error")
                                        errHandle.DoError("process_textlist [new]", True)
                                        return oBack
                                    oBack['file'] = oText['name']
                                    # Now add the object to the list of objects
                                    lstText.append(oNew)
                                else:
                                    # Not all fields were there in the [oText] we encountered
                                    oBack['note'] = "Did not find all obl fields in {} [{}]".format(oText['name'], sFormat)
                                    oStatus.set("error", oBack)

                        # Show what is going on
                        oStatus.set("adding", oBack)

                    # We are ready with this part
                    oBack['parts'] += 1
                    # Save what we have so far
                    Text.objects.bulk_create(lstText)
                    oBack['paths'] += 1

        # We are done!
        oStatus.set("part", oBack)

        # return positively
        oBack['result'] = True
        return oBack
    except:
        # oCsvImport['status'] = 'error'
        oStatus.set("error")
        errHandle.DoError("process_textlist", True)
        return oBack


def process_corpusinfo(oStatus, oCorpusInfo):
    """Update our own models with the information in [oCorpusInfo]"""

    oBack = {}      # What we return

    try:
        # Retrieve the correct instance of the status object
        # oStatus = Status.objects.last()

        # oStatus = Status.objects.filter(user=username, type=synctype).first()
        oStatus.set("preparing")

        # Initialise what we return
        oBack = {'result': False, 'constituents': 0, 
                 'metavar': 0, 'corpora': 0, 'variable': 0, 
                 'tagset': 0, 'grouping': 0, 'part': 0}

        # Validate
        if not 'indices' in oCorpusInfo or not 'corpora' in oCorpusInfo \
            or not 'metavar' in oCorpusInfo or not 'constituents' in oCorpusInfo:
            mis_list = []
            element_list = ['indices', 'corpora', 'metavar', 'constituents']
            for el in element_list:
                if not el in oCorpusInfo:
                    mis_list.append(el)
            missing = " ".join(mis_list)

            # We miss information
            msg = "process_corpusinfo: information is missing ({})".format(missing)
            oStatus.set('error', msg=msg)
            # Just to be sure, indicate that we have no result
            oBack['result'] = False
            return oBack

        # Process the 'constituents' part - most basic and not dependant of other things
        oStatus.set("constituents", oBack)
        lConstituents = oCorpusInfo['constituents']
        for oCns in lConstituents:
            # Check if this item is defined
            instCns = Constituent.get_item(oCns['title'])
            if instCns == None:
                # This constituent is not yet there: create it
                oNew = Constituent(title=oCns['title'], 
                                   eng=oCns['eng'])
                oNew.save()
                # Create a constituent name in Dutch linked to me
                oName = ConstituentNameTrans(lng=choice_value(LANGUAGE, 'nld'), 
                                             descr=oCns['nld'], 
                                             constituent=oNew)
                oName.save()
                # Bookkeeping
                oBack['constituents'] += 1
                oStatus.set("constituents: "+str(oBack['constituents']), oBack)

        # Process the METAVAR information -- only depends on the constituent names
        oStatus.set("metavar ...", oBack)
        lMetavar = oCorpusInfo['metavar']
        for oMvar in lMetavar:
            # Get the name of the metavar
            sMvarName = oMvar['name']
            # Sanity check
            if sMvarName == "":
                # THis is no good -- continue with the next item in [metavar]
                continue

            # If we don't yet have this metavar, create it
            instMvar = Metavar.get_item(sMvarName)
            if instMvar == None :
                # Create it
                instMvar = Metavar(name=sMvarName, hidden=oMvar['hidden'])
                instMvar.save()
                # Bookkeeping
                oBack['metavar'] += 1
                oStatus.set("metavar: "+str(oBack['metavar']), oBack)

            # Check out variable definitions--for this particular Metavar-Name
            lVariable = oMvar['variables']
            for oVariable in lVariable:
                # Sanity check
                if oVariable['name'] != "":
                    # Check if the VariableName exists (this is Metavar-name independant)
                    oVname = VariableName.get_item(oVariable['name'])
                    if oVname == None:
                        # Create a variable name
                        oVname = VariableName(name=oVariable['name'],
                                              descr=oVariable['descr'],
                                              type=choice_value(VARIABLE_TYPE, oVariable['type'] ))
                        oVname.save()
                    # Check if this variable/Metavar-name combination is in there
                    oNew = Variable.get_item(oVariable['name'], instMvar)
                    if oNew == None:
                        # First create a variable name item
                        # Create it and save it
                        oNew = Variable(name=oVname,
                                        metavar=instMvar,
                                        loc=choice_value(VARIABLE_LOC, oVariable['loc']),
                                        value=oVariable['value'])
                        oNew.save()
                        # Bookkeeping
                        oBack['variable'] += 1
                        oStatus.set("metavar variable: "+str(oBack['variable']), oBack)

            # Check out tagset definitions
            lTagset = oMvar['tagset']
            for oTagset in lTagset:
                # Sanity check
                if oTagset['title'] == "": continue
                # Try to find a Constituent for this tagset
                instCns = Constituent.get_item(oTagset['title'])
                if instCns != None:
                    # Try get the tagset, dependant upon [metavar]
                    instTagset = Tagset.get_item(instCns, instMvar)
                    if instTagset == None:
                        # Create a new tagset item
                        instTagSet = Tagset(metavar=instMvar, 
                                            constituent=instCns,
                                            definition=oTagset['def'])
                        instTagSet.save()
                        # Bookkeeping
                        oBack['tagset'] += 1
                        oStatus.set("metavar tagset: "+str(oBack['tagset']), oBack)

            # Check out grouping definitions
            lGrouping = oMvar['groupings']
            for oGroup in lGrouping:
                # Sanity check
                if oGroup['name'] =="": continue
                # First check for the grouping-name
                instGrpName = GroupingName.get_item(oGroup['name'])
                if instGrpName == None:
                    # Add the grouping name
                    instGrpName = GroupingName(name=oGroup['name'],
                                               descr=oGroup['descr'])
                    instGrpName.save()
                # Check if this grouping is in there
                instGrp = Grouping.get_item(instGrpName, instMvar)
                if instGrp == None:
                    # grouping is not yet defined: define it
                    instGrp = Grouping(name=instGrpName, 
                                       value=oGroup['value'],
                                       metavar=instMvar)
                    instGrp.save()
                    # Bookkeeping
                    oBack['grouping'] += 1
                    oStatus.set("metavar grouping: "+str(oBack['grouping']), oBack)

        # Process the 'corpora' part
        oStatus.set("corpora information", oBack)
        lCorpora = oCorpusInfo['corpora']
        for oCrp in lCorpora:
            # Check if this corpus exists already
            instCrp = Corpus.get_item(oCrp['name'])
            if instCrp == None:
                # Create this corpus
                if oCrp['hidden']:
                    sStatus = 'hidden'
                else:
                    sStatus = 'public'
                sMvar = oCrp['metavar']
                if sMvar == "":
                    # NOte: it is not obligatory for one corpus to have one instance of a metavar
                    instMvar = None
                else:
                    instMvar = Metavar.get_item(sMvar)
                # Only now can we create a corpus instance
                instCrp = Corpus(name=oCrp['name'],
                                 lng=choice_value(CORPUS_LANGUAGE, oCrp['lng']),
                                 eth=choice_value(CORPUS_ETHNO, oCrp['eth']),
                                 metavar=instMvar,
                                 status=sStatus)
                instCrp.save()
                oBack['corpora'] += 1
                oStatus.set("corpora: "+str(oBack['corpora']), oBack)
            # Now check for all the [part] elements in this corpus
            for oPart in oCrp['parts']:
                # Sanity check
                if oPart['name'] == "": continue
                # Check if this corpus/part item already exists
                instPart = Part.get_item(oPart['name'], instCrp)
                if instPart == None:
                    # This part does not yet exist: add it
                    sMvar = oPart['metavar']
                    if sMvar != "":
                        # Metavar is obligatory for a [Part]
                        instMvar = Metavar.get_item(sMvar)
                        # Now create a [Part]
                        instPart = Part(name=oPart['name'],
                                        dir=oPart['dir'],
                                        descr=oPart['descr'],
                                        url=oPart['url'],
                                        metavar=instMvar,
                                        corpus=instCrp)
                        instPart.save()
                        oBack['part'] += 1
                        oStatus.set("part: "+str(oBack['part']), oBack)
                        # Sanity check
                        if not 'psdx' in oPart:
                            # Stop right here
                            iStop = 1
                        else:
                            # Look for download information
                            if oPart['psdx'] != "":
                                # Add psdx download information
                                instDown = Download(url=oPart['psdx'],
                                                    format=choice_value(CORPUS_FORMAT, 'psdx'),
                                                    part=instPart)
                                instDown.save()
                        # Sanity check
                        if not 'folia' in oPart:
                            # Stop right here
                            iStop = 1
                        else:
                            if oPart['folia'] != "":
                                # Add psdx download information
                                instDown = Download(url=oPart['folia'],
                                                    format=choice_value(CORPUS_FORMAT, 'folia'),
                                                    part=instPart)
                                instDown.save()
                    

        # We are done!
        oStatus.set("done", oBack)

        # return positively
        oBack['result'] = True
        return oBack
    except:
        # oCsvImport['status'] = 'error'
        oStatus.set("error")
        errHandle.DoError("process_corpusinfo", True)
        return oBack


class HelpChoice(models.Model):
    """Define the URL to link to for the help-text"""
    
    field = models.CharField(max_length=200)        # The 'path' to and including the actual field
    searchable = models.BooleanField(default=False) # Whether this field is searchable or not
    display_name = models.CharField(max_length=50)  # Name between the <a></a> tags
    help_url = models.URLField(default='')          # THe actual help url (if any)

    def __str__(self):
        return "[{}]: {}".format(
            self.field, self.display_name)

    def Text(self):
        help_text = ''
        # is anything available??
        if (self.help_url != ''):
            if self.help_url[:4] == 'http':
                help_text = "See: <a href='{}'>{}</a>".format(
                    self.help_url, self.display_name)
            else:
                help_text = "{} ({})".format(
                    self.display_name, self.help_url)
        return help_text


def get_help(field):
    """Create the 'help_text' for this element"""

    # find the correct instance in the database
    help_text = ""
    try:
        entry_list = HelpChoice.objects.filter(field__iexact=field)
        entry = entry_list[0]
        # Note: only take the first actual instance!!
        help_text = entry.Text()
    except:
        help_text = "Sorry, no help available for " + field

    return help_text


class Metavar(models.Model):
    """Meta variable definitions for a particular corpus"""

    # [1]
    name = models.CharField("Name of this meta variable", max_length=MAX_TEXT_LEN, blank=False, null=False)
    # [1]
    hidden = models.BooleanField("This metavar is hidden (?)", default = False)

    def __str__(self):
        return self.name

    def get_item(sName):
        qs = Metavar.objects.filter(name=sName)
        if qs == None or len(qs) == 0:
            return None
        else:
            return qs[0]


class VariableName(models.Model):
    """One variable name that can be used by Variable specification"""

    # [1; o] Each variable has a name (e.g: 'author', 'date', 'dateEarly')
    #        But the name comes from a closed set of possibilities defined in FieldChoice
    name = models.CharField("Name of this variable", max_length=MAX_TEXT_LEN, blank=False, null=False)
    # [1; o] Description in plain text of this variable
    descr = models.TextField("Description of this variable", blank=False, null=False)
    # [1; f] Type of variable as available from a fixed set of possibilities
    type = models.CharField("Type of this variable", choices=build_choice_list(VARIABLE_TYPE), 
                            max_length=5, help_text=get_help(VARIABLE_TYPE))

    def __str__(self):
        return self.name

    def get_item(sName):
        qs = VariableName.objects.filter(name=sName)
        if qs == None or len(qs) == 0:
            return None
        else:
            return qs[0]


class Variable(models.Model):
    """A (named) variable contains the link to the actual Xquery code"""

    # [1; c] Link to the variable name and description definition
    name = models.ForeignKey(VariableName, blank=False, null=False, on_delete=models.CASCADE, related_name="name_variables")
    # [1] Where should this variable be found in XML: header of cmdi file?
    loc = models.CharField("Location", choices=build_choice_list(VARIABLE_LOC), max_length=5, help_text=get_help(VARIABLE_LOC), blank=False, null=False)
    # [1; o] Xquery text to get to the value of this variable
    value = models.TextField("Xquery definition", blank=False, null=False)
    # [1] Each variable belongs to exactly one [Metavar]
    metavar = models.ForeignKey(Metavar, blank=False, null=False, on_delete=models.CASCADE, related_name="metavar_variables")

    def __str__(self):
        return "{}_{}".format(self.name.name, self.metavar.name)

    def get_item(sName, instMvar):
        qs = Variable.objects.filter(name__name__iexact=sName).filter(metavar=instMvar)
        if qs == None or len(qs) == 0:
            return None
        else:
            return qs[0]


class GroupingName(models.Model):
    """One variable name that can be used by Grouping specification"""

    # [1; o] Each grouping has a name (e.g: 'subtype', 'authorAlphabet')
    #        But the name comes from a closed set of possibilities defined in FieldChoice
    name = models.CharField("Name of this grouping", max_length=MAX_TEXT_LEN, blank=False, null=False)
    # [1; o] Description in plain text of this grouping
    descr = models.TextField("Description of this grouping", blank=False, null=False)

    def __str__(self):
        return self.name

    def get_item(sName):
        qs = GroupingName.objects.filter(name=sName)
        if qs == None or len(qs) == 0:
            return None
        else:
            return qs[0]


class Grouping(models.Model):
    """A (named) variable contains the link to the actual Xquery code"""

    # [1; c] Link to the variable name and description definition
    name = models.ForeignKey(GroupingName, blank=False, null=False, on_delete=models.CASCADE, related_name="name_groupings")
    # [1; o] Xquery text to get to the value of this variable
    value = models.TextField("Definition of this grouping in Xquery", blank=False, null=False)
    # [1] Each variable belongs to exactly one [Metavar]
    metavar = models.ForeignKey(Metavar, blank=False, null=False, on_delete=models.CASCADE, related_name="metavar_groupings")

    def __str__(self):
        return "{}_{}".format(self.name.name, self.metavar.name)

    def get_item(instGrpName, instMvar):
        qs = Grouping.objects.filter(name=instGrpName).filter(metavar=instMvar)
        if qs == None or len(qs) == 0:
            return None
        else:
            return qs[0]


class Constituent(models.Model):
    """One constituent that can be used by tagsets and other stuff"""

    # [1; o] Each variable has a name (e.g: 'author', 'date', 'dateEarly')
    #        But the name comes from a closed set of possibilities defined in FieldChoice
    title = models.CharField("Name of the constituent", max_length=MAX_TEXT_LEN, blank=False, null=False, default="TITLE")
    # [1]    Plain text description of what constituent(s) this tagset variable targets
    eng = models.TextField("Constituent description (English)", blank=False, null=False, default="SPECIFY")

    def __str__(self):
        return self.title

    def get_item(sName):
        qs = Constituent.objects.filter(title=sName)
        if qs == None or len(qs) == 0:
            return None
        else:
            return qs[0]


class ConstituentNameTrans(models.Model):
    """Translation of a tagset name description into another language"""

    # [1] Language
    lng = models.CharField("Language", choices=build_choice_list(LANGUAGE), max_length=5, help_text=get_help(LANGUAGE))
    # [1] Description
    descr = models.TextField("Constituent description (in this language)", blank=False, null=False, default="SPECIFY")
    # [1] Link to a [TagsetName]
    constituent = models.ForeignKey(Constituent, blank=False, null=False, on_delete=models.CASCADE, related_name="constituent_translations")

    def __str__(self):
        return "{}_{}".format(self.constituent.title, self.lng)


class Tagset(models.Model):
    """Links the name of a constituent with the POS names used in one corpus"""

    # [1; c]
    constituent = models.ForeignKey(Constituent, blank=False, null=False, default=0, on_delete=models.CASCADE, related_name="constituent_tagsets")
    # [1; o]
    definition = models.CharField("Xquery for the constituent", max_length=MAX_TEXT_LEN, blank=False, null=False)
    # [1] Each tagset specification belongs to exactly one [Metavar]
    metavar = models.ForeignKey(Metavar, blank=False, null=False, on_delete=models.CASCADE, related_name="metavar_tagsets")

    def __str__(self):
        return "{}_{}".format(self.constituent.title, self.metavar.name)

    def get_item(instConst, instMvar):
        qs = Tagset.objects.filter(constituent=instConst).filter(metavar=instMvar)
        if qs == None or len(qs) == 0:
            return None
        else:
            return qs[0]


class Corpus(models.Model):
    """Description of one XML text corpus"""

    # [1]
    name = models.CharField("Name of this corpus", max_length=MAX_TEXT_LEN)
    # [1]
    lng = models.CharField("Language of the texts", choices=build_choice_list(CORPUS_LANGUAGE), max_length=5, help_text=get_help(CORPUS_LANGUAGE))
    # [1]
    eth = models.CharField("Ethnologue 3-letter code of the text langauge", choices=build_choice_list(CORPUS_ETHNO), max_length=5, help_text=get_help(CORPUS_ETHNO))
    # [0-1]
    metavar = models.ForeignKey(Metavar, blank=True, null=True, on_delete=models.CASCADE, related_name="metavar_corpora")
    # [1]
    status = models.CharField("The status (e.g. 'hidden')", choices=build_choice_list(CORPUS_STATUS), max_length=5, help_text=get_help(CORPUS_STATUS))

    def __str__(self):
        return self.name

    def get_item(sName):
        qs = Corpus.objects.filter(name=sName)
        if qs == None or len(qs) == 0:
            return None
        else:
            return qs[0]


class Part(models.Model):
    """Makeup of one part of a corpus"""

    # [1]
    name = models.CharField("Name of this part", max_length=MAX_TEXT_LEN)
    # [1]
    dir = models.CharField("Sub directory of this part", max_length=MAX_TEXT_LEN, blank=True, default="")
    # [1]
    descr = models.TextField("Full name of this part", default="(Put your description here)")
    # [1]
    url = models.URLField("Link to the (original) release of this corpus (part)")
    # [1]
    metavar = models.ForeignKey(Metavar, blank=False, null=False, on_delete=models.CASCADE, related_name="metavar_parts")
    # [1] Each 'Part' can only belong to one 'Corpus'
    corpus = models.ForeignKey(Corpus, blank=False, null=False, on_delete=models.CASCADE, related_name="corpus_parts")

    def __str__(self):
        return self.name

    def get_item(sName, instCrp):
        qs = Part.objects.filter(name=sName).filter(corpus=instCrp)
        if qs == None or len(qs) == 0:
            return None
        else:
            return qs[0]

    def language(self):
        return self.corpus.get_lng_display()

    def get_parts():
        qs = Part.objects.all().order_by('corpus__lng', 'corpus__name', 'name')
        return qs

    def get_text_count(self):
        lst_format = [{"format": 0, "name": "psdx", "count": 0},
                      {"format": 1, "name": "folia", "count": 0}]
        html = []
        for oFormat in lst_format:
            oFormat['count'] += self.part_texts.filter(format=oFormat['format']).count()
            html.append("{}: {}".format( oFormat['name'], oFormat['count']))
        sBack = " ".join(html)
        return sBack

    def get_line_count(self):
        lst_format = [{"format": 0, "name": "psdx", "count": 0},
                      {"format": 1, "name": "folia", "count": 0}]
        html = []
        for oFormat in lst_format:
            for oItem in self.part_texts.filter(format=oFormat['format']).values("lines"):
                oFormat['count'] += oItem['lines']
            html.append("{}: {}".format( oFormat['name'], oFormat['count']))
        sBack = " ".join(html)
        return sBack

    def get_word_count(self):
        lst_format = [{"format": 0, "name": "psdx", "count": 0},
                      {"format": 1, "name": "folia", "count": 0}]
        html = []
        for oFormat in lst_format:
            for oItem in self.part_texts.filter(format=oFormat['format']).values("words"):
                oFormat['count'] += oItem['words']
            html.append("{}: {}".format( oFormat['name'], oFormat['count']))
        sBack = " ".join(html)
        return sBack


class Download(models.Model):
    """Download information for one corpus part in one format"""

    # [1]
    format = models.CharField("Format for this corpus (part)", choices=build_choice_list(CORPUS_FORMAT), 
                              max_length=5, help_text=get_help(CORPUS_FORMAT))
    # [0-1; f] Actual URL to place on the internet
    url = models.URLField("Link to download this corpus (part)", blank=True, null=True)
    # [1] Number of texts available in this format
    count = models.CharField("Number of texts", max_length=10, default="unknown")
    # [1]    Link to the [Part] this download belongs to
    part = models.ForeignKey(Part, blank=False, null=False, related_name="downloads", on_delete=models.CASCADE)

    def __str__(self):
        return "{}_{}".format(self.part.name, choice_english(CORPUS_FORMAT, self.format))


class Text(models.Model):
    """One text that belongs to a Part of a Corpus"""

    # [1] - this is only the *last* part of the file name
    fileName = models.CharField("Name of the text file", max_length=MAX_TEXT_LEN)
    # [1] - every text must be [psdx] or [folia] or something
    format = models.CharField("Format for this corpus (part)", choices=build_choice_list(CORPUS_FORMAT), max_length=5, help_text=get_help(CORPUS_FORMAT))
    # [1] - Every text must be part of a Part
    part = models.ForeignKey(Part, blank=False, null=False, on_delete=models.CASCADE, related_name="part_texts")
    # [1] - EVery text must have a length in number of lines
    lines = models.IntegerField("Number of lines", default=0)
    # [1] - EVery text must have a length in number of words
    words = models.IntegerField("Number of words", default=0)
    # [0-1] - Every text may have a metadata file associated with it
    metaFile = models.CharField("Name of the metadata file", max_length=MAX_TEXT_LEN, blank=True, null=True)
    # [0-1] - Every text *MAY* have a title
    title = models.CharField("Title of this text", max_length=MAX_TEXT_LEN, blank=True, null=True)
    # [0-1] - Every text *MAY* have a date
    date = models.CharField("Publication year of this text", max_length=MAX_TEXT_LEN, blank=True, null=True)
    # [0-1] - Every text *MAY* have an author
    author = models.CharField("Author(s) of this text", max_length=MAX_TEXT_LEN, blank=True, null=True)
    # [0-1] - Every text *MAY* have a genre
    genre = models.CharField("Genre of this text", max_length=MAX_TEXT_LEN, blank=True, null=True)
    # [0-1] - Every text *MAY* have a subtype
    subtype = models.CharField("Subtype of this text", max_length=MAX_TEXT_LEN, blank=True, null=True)

    def __str__(self):
        return self.fileName

    def formatname(self):
        return self.get_format_display()
    formatname.short_description = "format"
    def datename(self):
        return self.date
    datename.short_description = "date"
    def genrename(self):
        return self.genre
    genrename.short_description = "genre"
    def subtypename(self):
        return self.subtype
    subtypename.short_description = "subtype"

    def get_absolute_url(self):
        return "/"+APP_PREFIX+"text/view/%i/" % self.id

    def admin_form_column_names(self):
        # 'part','format', 'fileName','title', 'date', 'author', 'genre', 'subtype'
        return ("%s %s %s %s %s %s %s %s" %
            (self.part.name, self.get_format_display(),
            self.fileName, self.title, self.date, self.author, self.genre, self.subtype)
            )

    def get_item(sName):
        qs = Text.objects.filter(fileName=sName)
        if qs == None or len(qs) == 0:
            return None
        else:
            return qs[0]

    def strip_ext(sName):
        lExt = ['.folia.xml.gz','.folia.xml', '.psdx.gz', '.psdx' ]
        # Possibly adapt filename: strip the extension
        for ext in lExt:
            if ext in sName:
                sName = sName.replace(ext, "")
                break
        #sName = sName.replace(".folia.xml.gz", "")
        #sName = sName.replace(".folia.xml", "")
        #sName = sName.replace(".psdx.gz", "")
        #sName = sName.replace(".psdx", "")
        return sName

    def find_text(part, format, sName):
        """Find the text [sName] within the part/format combination"""
        sName = Text.strip_ext(sName)
        return Text.objects.filter(fileName=sName, part=part, format=format).first()

    def sorted_texts(part, format):
        # Provide a list of sorted texts starting from [sName]
        qs = Text.objects.filter(part=part, format=format).order_by('fileName')
        return qs

    def get_sentences(self):
        """Get the sentences belonging to this text"""

        # Initialize return object
        oBack = {'status': 'ok'}
        # Check if they have been fetched
        if self.sentences.count() == 0:
            # Need to fetch them
            oBack = get_crpp_text(self.part.corpus.get_lng_display(), 
                                  self.part.dir, 
                                  self.get_format_display(), 
                                  self.fileName)
            # Validate what we receive
            if oBack == None or oBack['status'] == 'error':
                return oBack
            # Process what we received into [Sentence] objects
            lstSent = []
            iOrder = 1
            with transaction.atomic():
                for oSent in oBack['line']:
                    # Create a new Sentence object
                    oNew = Sentence(identifier=oSent['id'],
                                    order=iOrder,
                                    sent=oSent['text'],
                                    text=self)
                    lstSent.append(oNew)
                    iOrder += 1
            # Save what we have so far
            Sentence.objects.bulk_create(lstSent)
        # At this point we HAVE all the sentences, so we only need to return the lot together
        # But this needs to be in a QUERYSET
        qs = Sentence.objects.filter(text__id=self.id).distinct().select_related().order_by('order')
        oBack['qs'] = qs
        return oBack

    def delete(self, using = None, keep_parents = False):
        # Remove all related QsubInfo
        # Qsubinfo.objects.filter(text=self).delete()
        # Remove all the sentences pointing to me
        Sentence.objects.filter(text=self).delete()
        # Now remove myself
        return super(Text, self).delete(using, keep_parents)


class Sentence(models.Model):
    """One sentence from the surface form of a text"""

    # [1] Order - number that dictates the order within a text
    order = models.IntegerField("Order")
    # [1] Identifier
    identifier = models.CharField("Identifier", max_length=MAX_TEXT_LEN)
    # [1] Text content itself
    # sent = models.CharField("Sentence", max_length=MAX_TEXT_LEN)
    sent = models.TextField("Sentence")
    # [1] Link to the [Text] this line belongs to
    text = models.ForeignKey(Text, blank=False, null=False, related_name="sentences", on_delete=models.CASCADE)

    def __str__(self):
        return self.identifier

    def get_part(self):
        return self.text.part.name

    def get_fileName(self):
        return self.text.fileName
