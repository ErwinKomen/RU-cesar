"""Models for the SEEKER app.

The seeker helps users define and execute searches through the texts that
are available at the back end
"""
from django.db import models, transaction
from django.contrib.auth.models import User
from datetime import datetime
from cesar.utils import *
from cesar.settings import APP_PREFIX
from cesar.browser.models import build_choice_list, get_help
import sys
import copy
import json

MAX_NAME_LEN = 50
MAX_TEXT_LEN = 200

SEARCH_FUNCTION = "search.function"
SEARCH_OPERATOR = "search.operator"

# ============================= LOCAL CLASSES ======================================
errHandle = ErrHandle()


class SearchMain(models.Model):
    """The main search item defined for this gateway"""

    # [1] Functions are e.g: word-text, word-category, constituent-text, constituent-category
    function = models.CharField("Format for this corpus (part)", choices=build_choice_list(SEARCH_FUNCTION), 
                              max_length=5, help_text=get_help(SEARCH_FUNCTION))
    # [1] The value for this function
    value = models.CharField("Value", max_length=MAX_TEXT_LEN)
    # [1] Comparison operator: equals, matches, contains etc
    operator = models.CharField("Operator", choices=build_choice_list(SEARCH_OPERATOR), 
                              max_length=5, help_text=get_help(SEARCH_OPERATOR))

    def __str__(self):
        return "{}{}{}".format(
            self.get_function_display(),
            self.value,
            self.get_operator_display())
    

class SearchItem(models.Model):
    """A search item is one 'search' variable specification for a gateway"""

    # [1] Each search item has a name
    name = models.CharField("Name of this search item", max_length=MAX_TEXT_LEN)
    # [1] Functions are e.g: word-text, word-category, constituent-text, constituent-category
    function = models.CharField("Format for this corpus (part)", choices=build_choice_list(SEARCH_FUNCTION), 
                              max_length=5, help_text=get_help(SEARCH_FUNCTION))
    # [1] The value for this function
    value = models.CharField("Value", max_length=MAX_TEXT_LEN)
    # [1] Comparison operator: equals, matches, contains etc
    operator = models.CharField("Operator", choices=build_choice_list(SEARCH_OPERATOR), 
                              max_length=5, help_text=get_help(SEARCH_OPERATOR))
    # [1] Every construction has one or more search items
    construction = models.ForeignKey(Construction, blank=False, null=False, related_name="searchitems")

    def __str__(self):
        return self.name


class Construction(models.Model):
    """A search construction consists of a [search] element and one or more search items"""

    # [1] Construction name
    name = models.CharField("Name of this search construction", max_length=MAX_TEXT_LEN)
    # [1] Main search item
    search = models.ForeignKey(SearchMain, blank=False, null=False)
    # [1] Every gateway has one or more constructions it may look for
    gateway = models.ForeignKey(Construction, blank=False, null=False, related_name="constructions")

    def __str__(self):
        return self.name


class Variable(models.Model):
    """A variable has a name and a value, possibly combined with a function and a condition"""

    # [1] Variable obligatory name
    name = models.CharField("Name of this variable", max_length=MAX_NAME_LEN)
    # [1] A variable may optionally have a pre-defined value
    value = models.CharField("Value", max_length=MAX_TEXT_LEN)


class Gateway(models.Model):
    """One gateway is one possible search definition"""

    # [1] Gateway option name
    name = models.CharField("Name of this gateway option", max_length=MAX_TEXT_LEN)
    # [0-n] Additional search items
    # [1-n]



class Research(models.Model):
    """Main entry for a research project"""

    # [1] Name of the CRP from which the results come (does not necessarily have to be here)
    name = models.CharField("Name of this research", max_length=MAX_TEXT_LEN)
    # [1] Purpose of this research
    purpose = models.TextField("Purpose")
    # [1] Each research project has a gateway
    gateway = models.ForeignKey(Gateway, blank=False, null=False)
    # [1] Each research project 

    def __str__(self):
        return self.name
