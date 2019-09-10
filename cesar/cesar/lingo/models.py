"""Models for the LINGO app.

The lingo app is the main page for linguistic experiments.
"""
from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils.html import mark_safe
from django.utils import timezone
from datetime import datetime
from markdown import markdown
from cesar.utils import *
from cesar.settings import APP_PREFIX
import sys
import copy
import json

MAX_IDENTIFIER_LEN = 10
MAX_TEXT_LEN = 200

EXPERIMENT_STATUS = "experiment.status"
EXPERIMENT_GENDER = "experiment.gender"
EXPERIMENT_YESNO = "experiment.yesno"
EXPERIMENT_EDU = "experiment.edu"

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

def build_abbr_list(field, position=None, subcat=None, maybe_empty=False, language="eng", sortcol=1):
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
                choice_list = [('','-')]
            for choice in FieldChoice.objects.filter(field__iexact=field):
                # Default
                sEngName = ""
                # Any special position??
                if position==None:
                    sEngName = choice.english_name if language=="eng" else choice.dutch_name
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

            choice_list = sorted(choice_list,key=lambda x: x[sortcol]);
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

def get_crpp_date(dtThis):
    """Convert datetime to string"""

    # Model: yyyy-MM-dd'T'HH:mm:ss
    sDate = dtThis.strftime("%Y-%m-%dT%H:%M:%S")
    return sDate

def adapt_markdown(val, lowercase=True, nopara=True):
    sBack = ""
    if val != None:
        val = val.replace("***", "\*\*\*")
        sBack = mark_safe(markdown(val, safe_mode='escape'))
        if nopara:
            sBack = sBack.replace("<p>", "")
            sBack = sBack.replace("</p>", "")
        if lowercase:
            sBack = sBack.lower()
    return sBack



class Experiment(models.Model):
    """An experiment that can be joined in for a limited time"""

    # [1] title of this news-item
    title = models.CharField("Title",  max_length=MAX_TEXT_LEN)
    # [1] the date when this item was created
    created = models.DateTimeField(default=datetime.now)
    saved = models.DateTimeField(null=True, blank=True)
    # [1] The URL to this experiment
    home = models.CharField("Home page part",  max_length=MAX_TEXT_LEN)

    # [0-1] optional time after which this should not be shown anymore
    until = models.DateTimeField("Remove at", null=True, blank=True)
    # [1] the explanatory message that needs to be shown (in html)
    msg = models.TextField("Message")
    # [0-1] Informed consent page (markdown)
    consent = models.TextField("Informed consent", blank=True, null=True)
    # [0-1] the fields in the Participant model that need to be asked
    ptcpfields = models.TextField("Participant fields", default="[]", blank=True)
    # [1] the status of this message (can e.g. be 'archived')
    status = models.CharField("Status", choices=build_abbr_list(EXPERIMENT_STATUS), 
                              max_length=5)

    def __str__(self):
        # An experiment is the title and the created
        sItem = "{}-{}".format(self.title, self.id)
        return sItem

    def get_msg_markdown(self):
        """Get a markdown representation of the msg"""
        return adapt_markdown(self.msg, lowercase=False)

    def get_consent_markdown(self):
        """Get a markdown representation of the consent"""
        return adapt_markdown(self.consent, lowercase=False, nopara=False)

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
        # Adapt the save date
        self.saved = datetime.now()
        response = super(Experiment, self).save(force_insert, force_update, using, update_fields)
        return response

    def resultcount(self):
        """Determine how many results there are"""

        # Get all participants from responses
        ptcp_list = Response.objects.filter(experiment=self).values('participant').distinct()
        
        return len(ptcp_list)


class Qdata(models.Model):
    """Question data for a particular experiment"""

    # [0-1] Metadata (e.g. text name or question number)
    qmeta = models.TextField("Question metadata", blank=True, default = "")
    # [0-1] The question data
    qtext = models.TextField("Question data", blank=True, default = "")
    # [0-1] Topic of the text
    qtopic = models.CharField("Topic", max_length=255, blank=True, default = "")
    # [0-1] Suggested topic of the text
    qsuggest = models.CharField("Suggested topic", max_length=255, blank=True, default = "")
    # [0-1] Correct response for this topic
    qcorr = models.CharField("Topic response", choices=build_abbr_list(EXPERIMENT_YESNO), max_length=5, blank=True, default = "")
    # [1] The experiment
    experiment = models.ForeignKey(Experiment)
    # [1] Include this one or not
    include = models.CharField("Include text", choices=build_abbr_list(EXPERIMENT_YESNO), max_length=5, blank=True, default = "n")

    def __str__(self):
        return self.qmeta


class Participant(models.Model):
    """A participant to the survey"""

    # [1] A unique ID that has been given to the participant
    ptcpid = models.CharField("Survey participant ID", max_length=MAX_TEXT_LEN, blank=True, default = "")
    # [0-1] IP address and computer name of participant
    ip = models.CharField("IP address", max_length=MAX_TEXT_LEN, blank=True, default = "unknown")
    # [1] Age (as a number)
    age = models.IntegerField("Age (number)", blank=True, null=True)
    # [1] Gender
    gender = models.CharField("Gender", choices=build_abbr_list(EXPERIMENT_GENDER), max_length=5, blank=True, default = "")
    # [1] English first language
    engfirst = models.CharField("English L1", choices=build_abbr_list(EXPERIMENT_YESNO), max_length=5, blank=True, default = "")
    # [0-1] First language
    lngfirst = models.CharField("First language", blank=True, null=True, max_length=MAX_TEXT_LEN, default = "")
    # [0-1] Additional languages
    lngother = models.CharField("Other languages", blank=True, null=True, max_length=MAX_TEXT_LEN, default = "")
    # [1] Highest education degree
    edu = models.CharField("Education", choices=build_abbr_list(EXPERIMENT_EDU), max_length=5, blank=True, default = "")
    # [0-1] Specification of education 
    eduother = models.TextField("Other education", blank=True, default="")
    # [0-1] Email (optional)
    email = models.CharField("E-mailadres", max_length=MAX_TEXT_LEN, blank=True, default="")
    # [1] Record when it was created
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        response = "ptcp{}: {}-{}".format(self.id, self.age, self.gender)
        return response

    def get_edu(self):
        abbr = self.edu
        dutch = FieldChoice.objects.filter(field__iexact=EXPERIMENT_EDU, abbr=abbr).first().dutch_name
        if abbr == "g7" and self.eduother != None:
            education = "{}_{}".format(dutch, self.eduother)
        else:
            education = dutch
        return education



class Response(models.Model):
    """Answers of one participant to one experiment"""

    # [1] The experiment
    experiment = models.ForeignKey(Experiment)
    # [1] The Participant
    participant = models.ForeignKey(Participant)
    # [0-1] The answers as a json object (stringified)
    answer = models.TextField("Answers", blank=True, null=True)
    # [1] Record when this response was created
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "{}_{}".format(self.experiment.home, self.participant.ptcpid)


