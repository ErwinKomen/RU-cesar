"""Models for the browser ap.

The browser allows browsing through XML files that are part of a corpus.
A corpus is in a particular language and according to a particular tagset.
The information here mirrors (and extends) the information in the crp-info.json file.
"""
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import sys
import copy

MAX_IDENTIFIER_LEN = 10
MAX_TEXT_LEN = 200

CORPUS_LANGUAGE = "corpus.language"
CORPUS_ETHNO = "corpus.ethnologue"
CORPUS_STATUS = "corpus.status"
CORPUS_FORMAT = "corpus.format"
VARIABLE_TYPE = "variable.type"
VARIABLE_LOC = "variable.loc"
LANGUAGE = "language"

class FieldChoice(models.Model):

    field = models.CharField(max_length=50)
    english_name = models.CharField(max_length=100)
    dutch_name = models.CharField(max_length=100)
    machine_value = models.IntegerField(help_text="The actual numeric value stored in the database. Created automatically.")

    def __str__(self):
        return "{}: {}, {} ({})".format(
            self.field, self.english_name, self.dutch_name, str(self.machine_value))

    class Meta:
        ordering = ['field','machine_value']

def build_choice_list(field, position=None, subcat=None):
    """Create a list of choice-tuples"""

    choice_list = [];
    unique_list = [];   # Check for uniqueness

    try:
        # check if there are any options at all
        if FieldChoice.objects == None:
            # Take a default list
            choice_list = [('0','-'),('1','N/A')]
        else:
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
        print("Unexpected error [build_choice_list]:", sys.exc_info()[0])
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

def get_instance_copy(item):
    new_copy = copy.copy(item)
    new_copy.id = None          # Reset the id
    new_copy.save()             # Save it preliminarily
    return new_copy

def copy_m2m(inst_src, inst_dst, field, lst_m2m = None):
    # Copy M2M relationship: conversationalType    
    for item in getattr(inst_src, field).all():
        newItem = get_instance_copy(item)
        # Possibly copy more m2m
        if lst_m2m != None:
            for deeper in lst_m2m:
                copy_m2m(item, newItem, deeper)
        getattr(inst_dst, field).add(newItem)

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


class VariableName(models.Model):
    """One variable name that can be used by Variable specification"""

    # [1; o] Each variable has a name (e.g: 'author', 'date', 'dateEarly')
    #        But the name comes from a closed set of possibilities defined in FieldChoice
    name = models.CharField("Name of this variable", max_length=MAX_TEXT_LEN, blank=False, null=False)
    # [1; o] Description in plain text of this variable
    descr = models.TextField("Description of this variable", blank=False, null=False)
    # [1; f] Type of variable as available from a fixed set of possibilities
    type = models.CharField("Type of this variable", choices=build_choice_list(VARIABLE_TYPE), max_length=5, help_text=get_help(VARIABLE_TYPE))

    def __str__(self):
        return self.name


class Variable(models.Model):
    """A (named) variable contains the link to the actual Xquery code"""

    # [1; c] Link to the variable name and description definition
    name = models.ForeignKey(VariableName, blank=False, null=False)
    # [1] Where should this variable be found in XML: header of cmdi file?
    loc = models.CharField("Location", choices=build_choice_list(VARIABLE_LOC), max_length=5, help_text=get_help(VARIABLE_LOC), blank=False, null=False)
    # [1; o] Xquery text to get to the value of this variable
    value = models.TextField("Xquery definition", blank=False, null=False)
    # [1] Each variable belongs to exactly one [Metavar]
    metavar = models.ForeignKey(Metavar, blank=False, null=False)

    def __str__(self):
        return "{}_{}".format(self.name.name, self.metavar.name)


class GroupingName(models.Model):
    """One variable name that can be used by Grouping specification"""

    # [1; o] Each grouping has a name (e.g: 'subtype', 'authorAlphabet')
    #        But the name comes from a closed set of possibilities defined in FieldChoice
    name = models.CharField("Name of this grouping", max_length=MAX_TEXT_LEN, blank=False, null=False)
    # [1; o] Description in plain text of this grouping
    descr = models.TextField("Description of this grouping", blank=False, null=False)

    def __str__(self):
        return self.name


class Grouping(models.Model):
    """A (named) variable contains the link to the actual Xquery code"""

    # [1; c] Link to the variable name and description definition
    name = models.ForeignKey(GroupingName, blank=False, null=False)
    # [1; o] Xquery text to get to the value of this variable
    value = models.TextField("Definition of this grouping in Xquery", blank=False, null=False)
    # [1] Each variable belongs to exactly one [Metavar]
    metavar = models.ForeignKey(Metavar, blank=False, null=False)

    def __str__(self):
        return "{}_{}".format(self.name.name, self.metavar.name)


class Constituent(models.Model):
    """One constituent that can be used by tagsets and other stuff"""

    # [1; o] Each variable has a name (e.g: 'author', 'date', 'dateEarly')
    #        But the name comes from a closed set of possibilities defined in FieldChoice
    title = models.CharField("Name of the constituent", max_length=MAX_TEXT_LEN, blank=False, null=False, default="TITLE")
    # [1]    Plain text description of what constituent(s) this tagset variable targets
    eng = models.TextField("Constituent description (English)", blank=False, null=False, default="SPECIFY")

    def __str__(self):
        return self.title


class ConstituentNameTrans(models.Model):
    """Translation of a tagset name description into another language"""

    # [1] Language
    lng = models.CharField("Language", choices=build_choice_list(LANGUAGE), max_length=5, help_text=get_help(LANGUAGE))
    # [1] Description
    descr = models.TextField("Constituent description (in this language)", blank=False, null=False, default="SPECIFY")
    # [1] Link to a [TagsetName]
    constituent = models.ForeignKey(Constituent, blank=False, null=False)

    def __str__(self):
        return "{}_{}".format(self.constituent.title, self.lng)


class Tagset(models.Model):
    """Links the name of a constituent with the POS names used in one corpus"""

    # [1; c]
    constituent = models.ForeignKey(Constituent, blank=False, null=False, default=0)
    # [1; o]
    definition = models.CharField("Xquery for the constituent", max_length=MAX_TEXT_LEN, blank=False, null=False)
    # [1] Each tagset specification belongs to exactly one [Metavar]
    metavar = models.ForeignKey(Metavar, blank=False, null=False)

    def __str__(self):
        return "{}_{}".format(self.constituent.title, self.metavar.name)


class Corpus(models.Model):
    """Description of one XML text corpus"""

    # [1]
    name = models.CharField("Name of this corpus", max_length=MAX_TEXT_LEN)
    # [1]
    lng = models.CharField("Language of the texts", choices=build_choice_list(CORPUS_LANGUAGE), max_length=5, help_text=get_help(CORPUS_LANGUAGE))
    # [1]
    eth = models.CharField("Ethnologue 3-letter code of the text langauge", choices=build_choice_list(CORPUS_ETHNO), max_length=5, help_text=get_help(CORPUS_ETHNO))
    # [1]
    metavar = models.ForeignKey(Metavar, blank=False, null=False)
    # [1]
    status = models.CharField("The status (e.g. 'hidden')", choices=build_choice_list(CORPUS_STATUS), max_length=5, help_text=get_help(CORPUS_STATUS))

    def __str__(self):
        return self.name


class Part(models.Model):
    """Makeup of one part of a corpus"""

    # [1]
    name = models.CharField("Name of this part", max_length=MAX_TEXT_LEN)
    # [1]
    dir = models.CharField("Sub directory of this part", max_length=MAX_TEXT_LEN, default="/")
    # [1]
    descr = models.TextField("Full name of this part", default="(Put your description here)")
    # [1]
    url = models.URLField("Link to the (original) release of this corpus (part)")
    # [1]
    metavar = models.ForeignKey(Metavar, blank=False, null=False)
    # [1] Each 'Part' can only belong to one 'Corpus'
    corpus = models.ForeignKey(Corpus, blank=False, null=False)

    def __str__(self):
        return self.name


class Download(models.Model):
    """Download information for one corpus part in one format"""

    # [1]
    format = models.CharField("Format for this corpus (part)", choices=build_choice_list(CORPUS_FORMAT), max_length=5, help_text=get_help(CORPUS_FORMAT))
    # [1; f] Actual URL to place on the internet
    url = models.URLField("Link to download this corpus (part)")
    # [1]    Link to the [Part] this download belongs to
    part = models.ForeignKey(Part, blank=False, null=False)

    def __str__(self):
        return "{}_{}".format(self.part.name, choice_english(CORPUS_FORMAT, self.format))


