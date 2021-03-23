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
from random import choice
from string import ascii_lowercase

# From Cesar
from cesar.utils import ErrHandle
from cesar.settings import WRITABLE_DIR

GENDER_TYPE = "woord.gender"


MAXPARAMLEN = 255
MAXQUESTION = 10

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


class WoordUser(models.Model):
    """User who has received a 'name'"""

    # [1] Each module has a name
    name = models.CharField("Full name", max_length=MAXPARAMLEN)
    # [0-1] We would lik to have metadata
    gender = models.CharField("Gender", choices=build_abbr_list(GENDER_TYPE), max_length=5, blank=True, default = "")
    # [0-1] Age
    age = models.IntegerField("Age", blank=True, null=True)
    # [0-1] Any comments by user
    about = models.TextField("User comments", blank=True, null=True)

    # [1] Status of this user
    status = models.CharField("Status", default="created", max_length=MAXPARAMLEN)

    def generate_new():
        """Generate a new user, assigning it a random name"""

        # Get a list of current user names
        current_names = [x.name for x in WoordUser.objecs.all()]

        bFound = False
        counter = 100000
        sName = "0000000000"
        while not bFound and counter > 0:
            # Generate a new string
            sName = "".join(choice(ascii_lowercase) for i in range(10))
            # Check if the string is already there
            if not sName in current_names:
                bFound = True
                break
            counter -= 1

        # A new name has been found
        return sName

    def is_user(sName):
        obj = WoordUser.objects.filter(name__iexact=sName).first()
        return (not obj is None)


class Result(models.Model):
    """A result of one user"""

    # [1] must know the user
    user = models.ForeignKey(WoordUser, related_name="userresults", on_delete=models.CASCADE)
    # [1] each result must be the answer to a particular question
    question = models.CharField("Question tag", max_length=MAXQUESTION)
    # [1] The judgment scale of this result
    judgment = models.IntegerField("Judgment", default=0)
