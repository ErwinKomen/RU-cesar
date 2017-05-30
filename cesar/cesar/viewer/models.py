"""Models for the viewer app.

The viewer allows viewing search results.
The results are user-specific, and are loaded in the viewer when a user wants to start viewing.
"""
from django.db import models, transaction
from django.contrib.auth.models import User
from datetime import datetime
from cesar.settings import APP_PREFIX
from cesar.browser.models import *
import sys
import copy
import json

MAX_IDENTIFIER_LEN = 10
MAX_TEXT_LEN = 200


class ResultSet(models.Model):
    """The general section of a corpus research project result database"""

    # [1] Name of the CRP from which the results come (does not necessarily have to be here)
    crpName = models.CharField("The Corpus Research Project that produced the results", max_length=MAX_TEXT_LEN)
    # [1] Date when the results were created
    created = models.CharField("Date created", max_length=MAX_TEXT_LEN)
    # [1] Link to the relevant [Part] from 'browser'
    #     (This is determined by the combination of "Part" and "Language" in the results database)
    part = models.ForeignKey(Part, blank=False, null=False)
    # [1] The line number from the QC (Query Constructor)
    qc = models.IntegerField("QC line number")
    # [0-1] Notes on these results
    notes = models.TextField("Notes on the results", blank=True)

    def __str__(self):
        # Each result is uniquely identified by: text, sentence, constituent
        sResId = self.fileName + ":" + self.sentId + ":" + self.constId
        return self.name


class ResultFeatName(models.Model):
    # [1]
    name = models.CharField("Name of this feature", max_length=MAX_TEXT_LEN)
    # [1] Names belong together to one set
    set = models.ForeignKey(ResultSet, blank=False, null=False)


class ResultFeature(models.Model):
    # [1] One feature is a key/value paier
    ftname = models.ForeignKey(ResultFeatName, blank=False, null=False)


class ResultText(models.Model):
    """The text from which a number of results have been taken"""

    # [1] Name of the TEXT in which this result occurred - should coincice with browser.Text.fileName
    #     fileName = models.CharField("Name of the text file", max_length=MAX_TEXT_LEN)
    text = models.ForeignKey(Text, blank=False, null=False)
    # [1] Each result text belongs to a particular ResultGeneral
    general = models.ForeignKey(ResultSet, blank=False, null=False)

    def __str__(self):
        return self.fileName


class Result(models.Model):
    """One result from a corpus search"""

    # [1] Link to the text
    text = models.ForeignKey(ResultText)
    # [1] Sentence identifier
    sentId = models.CharField("Sentence identifier", max_length=MAX_TEXT_LEN)
    # [1] Constituent identifier
    constId = models.CharField("Constituent identifier", max_length=MAX_TEXT_LEN)
    
    def __str__(self):
        # Each result is uniquely identified by: text, sentence, constituent
        sResId = "{}:{}:{}".format(self.fileName,
                                   self.sentId,
                                   self.constId)
        return sResId

    def get_item(sName):
        qs = Result.objects.filter(name=sName)
        if qs == None or len(qs) == 0:
            return None
        else:
            return qs[0]