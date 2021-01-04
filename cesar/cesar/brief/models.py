import os
import sys
import time
import json
import re
import copy
from io import StringIO 
from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from markdown import markdown
from django.utils.html import mark_safe
from cesar.utils import ErrHandle
from cesar.seeker.models import import_data_file
from cesar.settings import WRITABLE_DIR

RESPONSE_TYPE = "brief.response.type"
NECESSITY_TYPE = "brief.necessity.type"
PROJECT_STATUS = "brief.project.status"
PROJECT_PROGRESS = "brief.project.progress"

qids = {'a':1, 'b':2, 'c':3, 'd':4, 'e':5, 'f':6, 'g':7, 'h':8, 'i':9, 'j':10, 'k':11, 'l':12, 'm':13}


MAXPARAMLEN = 255

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


class BriefModule(models.Model):
    """A module within the project brief"""

    # [1] Each module has a name
    name = models.CharField("Full name", max_length=MAXPARAMLEN)
    # [1] Short name of the brief to be used as a label
    short = models.CharField("Short name", max_length=MAXPARAMLEN)
    # [1] Each module has an order number
    order = models.IntegerField("Order", default=-1)
    # [0-1] Introductory words - markup language
    intro = models.TextField("Introduction", null=True, blank=True)
    # [1] Each Brief Module has been created at one point in time
    created = models.DateTimeField(default=timezone.now)
    # [0-1] Time this module was last updated
    saved = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.short

    def update(name, short, order):

        oErr = ErrHandle()
        module = None
        try:
            # Try get the module
            module = BriefModule.objects.filter(Q(name=name)|Q(short=short)).first()
            if module == None:
                module = BriefModule.objects.create(name=name, short=short, order=order)
            else:
                bNeedSaving= False
                # Possibly update
                if module.name != name:
                    module.name = name
                    bNeedSaving = True
                if module.short != short:
                    module.short = short
                    bNeedSaving = True
                if module.order != order:
                    module.order = order
                    bNeedSaving = True
                if bNeedSaving:
                    module.save()
        except:
            msg = oErr.get_error_message()
            oErr.DoError("briefmodule/update")
        return module


class BriefSection(models.Model):
    """Section within a module"""

    # [1] Each section has a name
    name = models.CharField("Full name", max_length=MAXPARAMLEN)
    # [1] Each section has an order number
    order = models.IntegerField("Order", default=-1)
    # [0-1] Introductory words - markup language
    intro = models.TextField("Introduction", null=True, blank=True)

    # [1] Each section belongs to a module
    module = models.ForeignKey(BriefModule, on_delete=models.CASCADE, related_name="modulesections")

    class Meta:
        ordering = ["module", "order"]

    def __str__(self):
        return self.name

    def update(name, order, module):

        oErr = ErrHandle()
        obj = None
        try:
            # Try get the section
            obj = BriefSection.objects.filter(module=module, order=order).first()
            if obj == None:
                obj = BriefSection.objects.create(name=name, module=module, order=order)
            else:
                bNeedSaving= False
                # Possibly update
                if obj.name != name:
                    obj.name = name
                    bNeedSaving = True
                if obj.order != order:
                    obj.order = order
                    bNeedSaving = True
                if obj.module != module:
                    obj.module = module
                    bNeedSaving = True
                if bNeedSaving:
                    obj.save()
        except:
            msg = oErr.get_error_message()
            oErr.DoError("briefsection/update")
        return obj

    def get_intro_markdown(self):
        sBack = adapt_markdown(self.intro, lowercase=False, nopara=False)
        return sBack

    def get_todo_html(self, project):
        # Initialize obligatoriness counting
        cnt_obl_needed = 0
        cnt_obl_done = 0
        todo = ""

        oErr = ErrHandle()
        try:
            # FIgure out what is really needed
            obl_needed = ['alw']
            if project.ptype != "ini":
                obl_needed.append("fir")
            for question in self.sectionquestions.all().order_by("order"):
                if question.ntype in obl_needed:
                    cnt_obl_needed += 1
                    # Check if question has been dealt with
                    obj = AnswerQuestion.objects.filter(project=project, question=question).first()
                    if obj != None and obj.content.strip() != "":
                        cnt_obl_done += 1
            if cnt_obl_needed > 0:
                if cnt_obl_done == cnt_obl_needed:
                    # Everything done
                    todo = "<span class='glyphicon glyphicon-flag' style='color: green;'></span>"
                else:
                    cnt_color = "red" if cnt_obl_done == 0 else "orange"
                    todo = "{}/{} <span class='glyphicon glyphicon-flag' style='color: {};'></span>".format(
                        cnt_obl_done, cnt_obl_needed, cnt_color)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("get_todo_html")
        # Return what we have figured out
        return todo


class BriefQuestion(models.Model):
    """Section within a module"""

    # [1] Each question has a content
    content = models.TextField("Question")
    # [1] Each question has an order number
    order = models.IntegerField("Order", default=-1)
    # [0-1] Additional information - markup language
    help = models.TextField("Additional information", null=True, blank=True)
    # [0-1] Placeholder, depending on the response type
    placeholder = models.CharField("Placeholder", max_length=MAXPARAMLEN, null=True, blank=True)
    # [1] Each question has a particular response type
    rtype = models.CharField("Response type", choices=build_abbr_list(RESPONSE_TYPE), max_length=5, blank=True, default = "")
    # [1] Each question has a particular necessity type
    ntype = models.CharField("Necessity type", choices=build_abbr_list(NECESSITY_TYPE), max_length=5, blank=True, default = "")

    # [1] Each question belongs to a section
    section = models.ForeignKey(BriefSection, on_delete=models.CASCADE, related_name="sectionquestions")

    class Meta:
        ordering = ["section", "order"]

    def __str__(self):
        return self.content

    def update(section, order, content, help, rtype, entries):

        oErr = ErrHandle()
        obj = None
        try:
            # Try get the question
            obj = BriefQuestion.objects.filter(section=section, order=order).first()
            if obj == None:
                obj = BriefQuestion.objects.create(section=section, order=order, content=content, rtype=rtype, help=help)
            else:
                bNeedSaving= False
                # Possibly update
                if obj.content != content:
                    obj.content = content
                    bNeedSaving = True
                if obj.order != order:
                    obj.order = order
                    bNeedSaving = True
                if obj.help != help:
                    obj.help = help
                    bNeedSaving = True
                if obj.rtype != rtype:
                    obj.rtype = rtype
                    bNeedSaving = True
                if obj.section != section:
                    obj.section = section
                    bNeedSaving = True
                if bNeedSaving:
                    obj.save()
            # What about [entries]?
            if len(entries) > 0:
                # there are entries to be processed!
                for idx, item in enumerate(entries):
                    order = idx + 1
                    content = item[0]
                    help = item[1]
                    # Check if this entry already exists
                    entry = obj.questionentries.filter(content=content).first()
                    if entry == None:
                        entry = BriefEntry.objects.create(content=content, order=order, help=help, question=obj)
                    else:
                        bNeedSaving= False
                        # Possibly update
                        if entry.help != help:
                            entry.help = help
                            bNeedSaving = True
                        if entry.order != order:
                            entry.order = order
                            bNeedSaving = True
                        if bNeedSaving:
                            entry.save()
        except:
            msg = oErr.get_error_message()
            oErr.DoError("briefsection/update")
        return obj

    def get_order_letter(self):
        """Convert the order integer into a letter"""

        letter = None
        if self.order > 0:
            for k,v in qids.items():
                if v == self.order:
                    letter = k
        if letter == None:
            letter = self.order
        letter = "{}.".format(letter)
        return letter

    def get_help_markdown(self):
        sBack = adapt_markdown(self.help, lowercase=False, nopara=False)
        return sBack


class BriefEntry(models.Model):
    """Some questions contain sub-questions, which we call [Entry]"""

    # [1] Each entry has a contents (short)
    content = models.CharField("Sub question", max_length=MAXPARAMLEN)
    # [0-1] Each entry may have some short help information
    help = models.CharField("Help information", max_length=MAXPARAMLEN, blank=True, null=True)
    # [0-1] Placeholder, depending on the response type
    placeholder = models.CharField("Placeholder", max_length=MAXPARAMLEN, null=True, blank=True)
    # [1] Each entry has an order number
    order = models.IntegerField("Order", default=-1)

    # [1] Each entry belongs to a question
    question = models.ForeignKey(BriefQuestion, on_delete=models.CASCADE, related_name="questionentries")

    def __str__(self):
        return self.content


class Project(models.Model):
    """A project name"""

    # [1] Each project has a name
    name = models.CharField("Name", max_length=MAXPARAMLEN)
    # [0-1] Description
    description = models.TextField("Description", null=True, blank=True)
    # [1] the status of this project (can e.g. be 'archived')
    status = models.CharField("Status", choices=build_abbr_list(PROJECT_STATUS), max_length=5, default="val")
    # [1] The amount of publications done by this project 
    ptype = models.CharField("Progress", choices=build_abbr_list(PROJECT_PROGRESS), max_length=5, default="ini")

    # [1] Each Brief Module has been created at one point in time
    created = models.DateTimeField(default=timezone.now)
    # [0-1] Time this module was last updated
    saved = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
        # Adapt the save date
        self.saved = timezone.now()
        # Now do the saving
        response = super(Project, self).save(force_insert, force_update, using, update_fields)
        # Return the response
        return response

    def get_created(self):
        """Get the creation date"""
        return self.created.strftime("%d/%B/%Y (%H:%M)")

    def get_saved(self):
        sBack = "-"
        if self.saved != None:
            sBack = self.saved.strftime("%d/%B/%Y (%H:%M)")
        return sBack

    def get_todo_html(self):
        # Initialize obligatoriness counting
        cnt_obl_needed = 0
        cnt_obl_done = 0
        todo = ""
        project = self

        oErr = ErrHandle()
        try:
            # FIgure out what is really needed
            obl_needed = ['alw']
            if project.ptype != "ini":
                obl_needed.append("fir")
            for question in BriefQuestion.objects.all().order_by("order"):
                if question.ntype in obl_needed:
                    cnt_obl_needed += 1
                    # Check if question has been dealt with
                    obj = AnswerQuestion.objects.filter(project=project, question=question).first()
                    if obj != None and obj.content.strip() != "":
                        cnt_obl_done += 1
            if cnt_obl_needed > 0:
                if cnt_obl_done == cnt_obl_needed:
                    # Everything done
                    todo = "<span class='glyphicon glyphicon-flag' style='color: green;'></span>"
                else:
                    cnt_color = "red" if cnt_obl_done == 0 else "orange"
                    todo = "{}/{} <span class='glyphicon glyphicon-flag' style='color: {};'></span>".format(
                        cnt_obl_done, cnt_obl_needed, cnt_color)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("get_todo_html")
        # Return what we have figured out
        return todo


class AnswerQuestion(models.Model):
    """Answer of one project to one question"""

    # [1] Each entry has a contents (short)
    content = models.CharField("Answer", max_length=MAXPARAMLEN)

    # [1] Each answer belongs to a question
    question = models.ForeignKey(BriefQuestion, on_delete=models.CASCADE, related_name="questionanswers")
    # [1] Each answer belongs to a project
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="projectquestionanswers")

    def __str__(self):
        return self.content


class AnswerEntry(models.Model):
    """Answer of one project to one entry (=sub-question)"""

    # [1] Each entry has a contents (short)
    content = models.CharField("Answer", blank=True, null=True, max_length=MAXPARAMLEN)

    # [1] Each entry-answer belongs to a question
    question = models.ForeignKey(BriefQuestion, on_delete=models.CASCADE, null=True, related_name="questionentryanswers")
    # [1] Each entry-answer also belongs to a particular entry
    entry = models.ForeignKey(BriefEntry, on_delete=models.CASCADE, related_name="entryanswers")
    # [1] Each answer belongs to a project
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="projectentryanswers")

    def __str__(self):
        return self.content


class BriefProduct(models.Model):
    """Scripture product"""

    # [1] Name of this product
    name = models.CharField("Product", max_length=MAXPARAMLEN)
    # [0-1] Scripture: books or passages included in this product
    scripture = models.TextField("Scripture", null=True, blank=True, help_text="list books, passages")
    # [0-1] The format of this product
    format = models.CharField("Format", null=True, blank=True, max_length=MAXPARAMLEN, help_text="e.g. text / audio / video")
    # [0-1] The media on which this product is available
    media = models.TextField("Media", null=True, blank=True, help_text="e.g. print / digital / broadcast / live performance etc")
    # [0-1] What desire(s), felt need(s) or concern(s) or values does this product address?
    goal = models.TextField("Goal", null=True, blank=True)
    # [0-1] Audiences this product is targetting
    audience = models.TextField("Audience(s)", null=True, blank=True)
    # [0-1] Timing
    timing = models.TextField("Timing", null=True, blank=True)

    # [1] Each Brief Product has been created at one point in time
    created = models.DateTimeField(default=timezone.now)
    # [0-1] Time this module was last updated
    saved = models.DateTimeField(null=True, blank=True)

    # [1] Each product has an order number within the products for one particular project
    order = models.IntegerField("Order", default=-1)

    # [1] Each answer belongs to a question
    question = models.ForeignKey(BriefQuestion, on_delete=models.CASCADE, related_name="questionproducts")
    # [1] Each answer belongs to a project
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="projectquestionproducts")

    def __str__(self):
        return self.name

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
        # Adapt the save date
        self.saved = timezone.now()
        # Now do the saving
        response = super(Project, self).save(force_insert, force_update, using, update_fields)
        # Return the response
        return response

    def get_created(self):
        """Get the creation date"""
        return self.created.strftime("%d/%B/%Y (%H:%M)")

    def get_saved(self):
        sBack = "-"
        if self.saved != None:
            sBack = self.saved.strftime("%d/%B/%Y (%H:%M)")
        return sBack

    def get_summary_html(self):
        """Get a summary of this product in HTML"""

        sBack = ""
        lhtml = []
        lhtml.append("<b>{}</b>".format(self.name))        
        return sBack



