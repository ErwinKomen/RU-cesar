"""Models for the SEEKER app.

The seeker helps users define and execute searches through the texts that
are available at the back end
"""
from django.db import models, transaction
from django.db.models import Q, Aggregate, Sum
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from datetime import datetime
from cesar.utils import *
from cesar.settings import APP_PREFIX
from cesar.browser.models import build_choice_list, build_abbr_list, \
                                 get_help, choice_value, choice_abbreviation, get_instance_copy, \
                                 copy_m2m, copy_fk, Part, CORPUS_FORMAT, Text, get_format_name
from cesar.seeker.services import crpp_exe, crpp_send_crp, crpp_status, crpp_dbinfo, crpp_stop
import sys
import copy
import json
import math
import re

MAX_NAME_LEN = 50
MAX_TEXT_LEN = 200
    
SEARCH_FUNCTION = "search.function"                 # woordgroep
SEARCH_OPERATOR = "search.operator"                 # groeplijktop
SEARCH_PERMISSION = "search.permission"
SEARCH_VARIABLE_TYPE = "search.variabletype"        # fixed, calc, gvar
SEARCH_RELATION_TYPE = "search.relationtype"        # axis, const, cond
SEARCH_ARGTYPE = "search.argtype"                   # fixed, gvar, cvar, dvar, func, cnst, axis, hit
SEARCH_CONDTYPE = "search.condtype"                 # func, dvar
SEARCH_FEATTYPE = "search.feattype"                 # func, dvar
SEARCH_TYPE = "search.type"                         # str, int, bool, cnst
SEARCH_INCLUDE = "search.include"                   # true, false
SEARCH_FILTEROPERATOR = "search.filteroperator"     # first, and, andnot

ERROR_CODE = "$__error__$"
SIMPLENAME = "_simplesearch"   # Name of the simple project

WORD_ORIENTED = 'w'
CONSTITUENT_ORIENTED = 'c'
EXTENDED_SEARCH = 'e'
TARGET_TYPE_CHOICES = (
    ('0', '----'),
    (WORD_ORIENTED, 'Word(s)'),
    (CONSTITUENT_ORIENTED, 'Constituent(s)'),
    (EXTENDED_SEARCH, 'Extended'),
)
STYPE_PLAIN = "p"
STYPE_SIMPLE = "s"
STYPE_CHOICES = (
    ('0', '----'),
    (STYPE_PLAIN, 'Plain'),
    (STYPE_SIMPLE, 'Simple')
)



# ============================= LOCAL CLASSES ======================================
errHandle = ErrHandle()
integer_format = re.compile(r'^\-?[0-9]+$')

def is_integer(sInput):
    if sInput == None:
        return False
    else:
        return (integer_format.search(sInput) != None)

def is_boolean(sInput):
    if sInput == None:
        return False
    else:
        sInput = sInput.lower()
        return sInput == 'false' or sInput == 'true'

def arg_matches(expected, actual, value = None):
    """Does the actual argument match the expected one?"""

    bMatch = (expected == actual)
    # Check if no match
    if not bMatch:
        # If str is expected, then int or bool are okay
        if expected == 'str':
            bMatch = (actual == 'int' or actual == 'bool')
        elif expected == 'bool':
            # If a boolean is expected, str may also be good, provided that is_boolean() holds
            bMatch = (actual == 'str' and is_boolean(value))
        elif expected == 'int':
            bMatch = (actual == 'str' and is_integer(value))
        elif expected == 'clist':
            # If [clist] expected, one single [cnst] is okay too
            bMatch = (actual == 'cnst')
        elif expected == 'cnst':
            # If [cnst] expected, and we have a [clist], then that is okay, but we do need to take the FIRST
            bMatch = (actual == 'clist')

    return bMatch

def get_crpp_date(dtThis):
    """Convert datetime to string"""

    # Model: yyyy-MM-dd'T'HH:mm:ss
    sDate = dtThis.strftime("%Y-%m-%dT%H:%M:%S")
    return sDate

def strip_varname(sName):
    varName = sName
    if varName.startswith("$_"):
        varName = varName[2:]
    elif varName.startswith("$"):
        varName = varName[1:]
    return varName


def import_data_file(sContents, arErr):
    """Turn the contents of [data_file] into a string array"""

    try:
        # Validate
        if sContents == "":
            return {}
        # Adapt the contents into an object array
        lines = []
        for line in sContents:
            lines.append(line.decode("utf-8").strip())
        ## Combine again
        #sContents = "\n".join(lines)
        #oData = json.loads(sContents)
        ## This is the data
        #return oData

        # This already is the array of strings
        return lines
    except:
        sMsg = errHandle.get_error_message()
        arErr.DoError("import_data_file error:")
        return {}



class SearchMain(models.Model):
    """The main search item defined for this gateway"""

    # [1] Functions are e.g: word-text, word-category, constituent-text, constituent-category
    function = models.CharField("Format for this corpus (part)", choices=build_choice_list(SEARCH_FUNCTION), 
                              max_length=5, help_text=get_help(SEARCH_FUNCTION))
    # [1] The value for this function
    value = models.CharField("Value", max_length=MAX_TEXT_LEN)
    # [0-1] The exclude value for this function
    exclude = models.CharField("Exclude", max_length=MAX_TEXT_LEN, null=True, blank=True)
    # [0-1] Extended: pos-tag
    category = models.CharField("Constituent category", max_length=MAX_TEXT_LEN, null=True, blank=True)
    # [0-1] Extended: lemma
    lemma = models.CharField("Lemma", max_length=MAX_TEXT_LEN, null=True, blank=True)
    # [0-1] Extended: feature category
    fcat = models.CharField("Feature category", max_length=MAX_TEXT_LEN, null=True, blank=True)
    # [0-1] Extended: feature value
    fval = models.CharField("Feaure value", max_length=MAX_TEXT_LEN, null=True, blank=True)
    # [0-1] Extended: related
    related = models.TextField("Related constituent(s)", null=True, blank=True)
    # [0-1] None of the above: CQL
    cql = models.CharField("Cql", max_length=MAX_TEXT_LEN, null=True, blank=True)
    # [1] Comparison operator: equals, matches, contains etc
    operator = models.CharField("Operator", choices=build_choice_list(SEARCH_OPERATOR), 
                              max_length=5, help_text=get_help(SEARCH_OPERATOR))

    def __str__(self):
        return "{}({}({}))".format(
            self.get_function_display(),
            self.get_operator_display(),
            self.value)

    def get_json(self):
        """Get a JSON definition of myself"""
        oJson = dict(function=self.get_function_display(),
                     value=self.value,
                     operator=self.get_operator_display())
        if self.exclude != None:
            oJson['exclude'] = self.exclude
        return oJson

    def get_copy(self, **kwargs):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def create_item(function, value, operator, exclude=None, category=None, lemma=None, fcat=None, fval=None, related=None, cql=None):
        operator_matches = choice_value(SEARCH_OPERATOR, operator)
        function_word = choice_value(SEARCH_FUNCTION, function)
        # Create initial object
        obj = SearchMain.objects.create(function=function_word,
                                        operator=operator_matches,
                                        value = value)
        need_saving = False
        if exclude != None: 
            obj.exclude = exclude
            need_saving = True
        if category != None: 
            obj.category = category
            need_saving = True
        if lemma != None: 
            obj.lemma = lemma
            need_saving = True
        if fcat != None:
            obj.fcat = fcat
            need_saving = True
        if fval != None:
            obj.fval = fval
            need_saving = True
        if related != None: 
            obj.related = related
            need_saving = True
        if cql != None:
            obj.cql = cql
            need_saving = True

        if need_saving:
            # Make sure it is saved
            obj.save()

        # Return the object as we have it
        return obj

    def adapt_item(self, function, value, operator, exclude=None, category=None, lemma=None, fcat=None, fval=None, related=None, cql=None):
        """Adapt the search and save it"""

        operator_matches = choice_value(SEARCH_OPERATOR, operator)
        function_word = choice_value(SEARCH_FUNCTION, function)

        need_saving = False
        # Set the items
        if self.function != function_word: 
            self.function = function_word
            need_saving = True
        if self.operator != operator_matches: 
            self.operator = operator_matches
            need_saving = True
        if self.value != value: 
            self.value = value
            need_saving = True
        if self.exclude != exclude:
            self.exclude = exclude
            need_saving = True
        if self.category != category: 
            self.category = category
            need_saving = True
        if self.lemma != lemma: 
            self.lemma = lemma
            need_saving = True
        if self.fcat != fcat:
            self.fcat = fcat
            need_saving = True
        if self.fval != fval:
            self.fval = fval
            need_saving = True
        if self.related != related: 
            self.related = related
            need_saving = True
        if cql != None:
            self.cql = cql
            need_saving = True
        # Need saving?
        if need_saving:
            # Save myself
            self.save()
        return self

    def get_search_spec(self, targetType):
        """Get the relevant search arguments in appropriate forms.
        
        w: Combine all single-word lines into a string like 'aap|noot|mies'
           Divide the remainder into a list of line-objects, containing a list of word-objects
           
        c: Give the include and exclude values"""

        def val_convert(value):
            """Convert word value"""

            # Initialisations
            lSingle = []
            lLine = []
            # Convert the string into a list of lines, disregarding the \r symbols of Windows
            input_line_list = self.value.replace('\r', '').split('\n')
            for input_line in input_line_list:
                input_word_list = input_line.split()
                if len(input_word_list) == 1:
                    lSingle.append(input_line)
                else:
                    lLine.append(input_line)
            sSingle = "|".join(lSingle)
            sMulti = tuple(lLine)
            if len(sMulti) == 1:
                sMulti = str(sMulti).replace(",)", ")")
            return sSingle, sMulti

        response = {}
        if targetType == 'w':
            # Only look for one or more words
            sSingle, sMulti = val_convert(self.value)
            response =  {'single': sSingle, 'line_list': sMulti}
        elif targetType == 'c':
            # Only look for a category
            response =  {'cat_incl': self.value, 'cat_excl': self.exclude}
        elif targetType == 'q': 
            # CQL definition
            response =  {'cql': self.cql }
        elif targetType == 'e': 
            # Extended: look for combination of word/lemma/category/fcat/fval
            sSingle, sMulti = val_convert(self.value)
            response = {'single': sSingle, 
                    'line_list': sMulti,
                    'cat_incl': self.category, 
                    'cat_excl': self.exclude,
                    'fcat': self.fcat,
                    'fval': self.fval,
                    'lemma': self.lemma}
        # Only add 'related'if it is there
        if self.related != None and self.related != "":
            # Translate the String into JSON
            response['related'] = json.loads(self.related)
        # Return the response
        return response
        

class GatewayManager(models.Manager):

    def create_gateway(self, name='leeg'):
        # Get all the gateways that ARE used
        gateway_ids = Research.objects.values_list('gateway__id', flat=True)
        # Remove any gateways that are not used
        gateway_unused = list(Gateway.objects.exclude(id__in=gateway_ids))
        for obj in gateway_unused:
            obj.delete()

        # Create a new gateway
        gateway = self.create(name=name)
        return gateway


class Gateway(models.Model):
    """One gateway is one possible search definition
    
    A gateway has 1 or more 'Construction' elements that define what construction to look for.
    A gateway may also have any number of defined 'Variable' elements.
    The values of these variables can be construction-dependant.
    """

    # [1] Gateway option name
    name = models.CharField("Name of this gateway option", max_length=MAX_TEXT_LEN, default='leeg')
    # [0-1] Description
    description = models.TextField("Description for this option", blank=True)
    # [0-1] Stringified JSON list of errors
    errors = models.TextField("Errors", default="")

    # This line is needed, in order to add the Gateway.create_gateway() call
    objects = GatewayManager()

    def __str__(self):
        return "{}:{}".format(self.id, self.name)

    def error_add(self, sMsg):
        self.refresh_from_db()
        lErrors = [] if self.errors == "" else json.loads(self.errors)
        lErrors.append(sMsg)
        self.errors = json.dumps(lErrors)
        self.save()

    def add_errors(self, arErr):
        self.refresh_from_db()
        # Get the errors that are already here
        lErrors = [] if self.errors == "" else json.loads(self.errors)
        # Add errors
        for err in arErr:
            lErrors.append(err)
        # Turn into string
        self.errors = json.dumps(lErrors)
        self.save()

    def error_clear(self):
        self.refresh_from_db()
        self.errors = ""
        self.save()

    def get_errors(self):
        self.refresh_from_db()
        return self.errors

    def get_json(self):
        """Get a JSON representation of myself"""

        # Initialize
        oJson = {}

        # Get the global variables
        gvar_list = []
        for gvar in self.globalvariables.order_by('order', 'id'):
            gvar_list.append({"name": gvar.name, 
                              "value": gvar.value, 
                              "description": gvar.description,
                              "type": gvar.type})
        oJson['gvars'] = gvar_list

        # List the constructions
        cons_list = []
        for cons in self.get_construction_list():
            # Get the SearchMain output
            oCons = cons.search.get_json()
            oCons['name'] = cons.name
            cons_list.append(oCons)
        oJson['constructions'] = cons_list

        # List the data-dependant variables
        dvar_list = []
        for dvar in self.get_vardef_list():
            dvar_list.append({"name": dvar.name, 
                              "order": dvar.order, 
                              "description": dvar.description,
                              "type": dvar.type})
        oJson['dvars'] = dvar_list

        # Get the construction variables
        cvar_list = []
        for cons in self.get_construction_list():
            # Walk all vardefs
            for dvar in self.get_vardef_list():
                cvar = ConstructionVariable.objects.filter(construction=cons, variable=dvar).first()
                oCvar = cvar.get_json()
                oCvar['cons'] = cons.name
                oCvar['dvar'] = dvar.name
                cvar_list.append(oCvar)
        oJson['cvars'] = cvar_list

        # Get the Conditions
        cond_list = []
        for cond in self.get_condition_list():
            oCond = cond.get_json()
            oCond['name'] = cond.name
            cond_list.append(oCond)
        oJson['conditions'] = cond_list

        # Get the Features
        feat_list = []
        for feat in self.get_feature_list():
            oFeat = feat.get_json()
            oFeat['name'] = feat.name
            feat_list.append(oFeat)
        oJson['features'] = feat_list

        # Return what we have found
        return oJson

    def get_copy(self, **kwargs):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Prepare an object for further processing
        kwargs = {'gateway': new_copy}
        # Copy all 'VarDef' and 'GlobalVariable' instances linked to me
        dvar_list = copy_m2m(self, new_copy, "definitionvariables", **kwargs)
        gvar_list = copy_m2m(self, new_copy, "globalvariables", **kwargs)

        # Copy all constructions + all associated construction variables
        cons_list = copy_m2m(self, new_copy, "constructions", **kwargs)

        # Put the relevant variables into kwargs
        kwargs['dvar_list'] = dvar_list
        kwargs['gvar_list'] = gvar_list
        kwargs['cons_list'] = cons_list

        # Now visit all construction variables
        cvar_list = ConstructionVariable.objects.filter(construction__gateway=self).select_related()
        for cvar in cvar_list:
            # determine the correct (new) construction and vardef
            construction_src = cvar.construction
            construction = next(x['dst'] for x in cons_list if x['src'] == construction_src)
            variable_src = cvar.variable
            variable = next(x['dst'] for x in dvar_list if x['src'] == variable_src)
            kwargs['construction'] = construction
            kwargs['variable'] = variable
            # Keep track of Functions linked to the 'old' cvar
            func_old_id = [item.id for item in cvar.functionroot.all()]
            # Create a new cvar using the correspondence lists
            cvar_new = cvar.get_copy(**kwargs)
            # Adapt the 'Function.root' of all 'new' FUnction instances 
            lstQ = []
            lstQ.append(~Q(id__in=func_old_id))
            lstQ.append(Q(root=cvar))
            with transaction.atomic():
                for function in Function.objects.filter(*lstQ):
                    function.root = cvar_new
                    function.save()

        # Visit the conditions
        cond_list = Condition.objects.filter(gateway=self).select_related()
        for cond in cond_list:
            # Keep track of Functions linked to the 'old' condition
            func_old_id = [item.id for item in cond.functioncondroot.all()]
            # Create a new cond using the correspondence lists
            cond_new = cond.get_copy(**kwargs)
            # Adapt the 'Function.root' of all 'new' FUnction instances 
            lstQ = []
            lstQ.append(~Q(id__in=func_old_id))
            lstQ.append(Q(rootcond=cond))
            with transaction.atomic():
                for function in Function.objects.filter(*lstQ):
                    function.rootcond = cond_new
                    function.save()

        # Visit the features
        feat_list = Feature.objects.filter(gateway=self).select_related()
        for feat in feat_list:
            # Keep track of Functions linked to the 'old' feature
            func_old_id = [item.id for item in feat.functionfeatroot.all()]
            # Create a new feat using the correspondence lists
            feat_new = feat.get_copy(**kwargs)
            # Adapt the 'Function.root' of all 'new' FUnction instances 
            lstQ = []
            lstQ.append(~Q(id__in=func_old_id))
            lstQ.append(Q(rootfeat=feat))
            with transaction.atomic():
                for function in Function.objects.filter(*lstQ):
                    function.rootfeat = feat_new
                    function.save()
                    
        # Return the new copy
        return new_copy

    def clear_search(self):
        """Clear any associated (a) data-dependant variables, (b) conditions, (c) features""" 

        oErr = ErrHandle()
        try:
            # Delete the definition variables
            dvar_set = self.definitionvariables.all().order_by('-order', '-id')
            for dvar in dvar_set:
                dvar.delete()
            # Delete the construction variables (not the constructions)
            cns_set = self.constructions.all()
            for cns_this in cns_set:
                for cvar_this in cns_this.constructionvariables.all():
                    cvar_this.delete()
            # Delete the conditions (and what is under them)
            cond_set = self.conditions.all()
            for cond_this in cond_set:
                cond_this.delete()
            # Delete the features (and what is under them)
            feat_set = self.features.all()
            for feat_this in feat_set:
                feat_this.delete()

            # Return okay
            return True
        except:
            sMsg = oErr.get_error_message()
            oErr.DoError("clear_search")
            return False

    def get_search_list(self):
        """List the names of the constructions plus their search group and specification"""

        oErr = ErrHandle()
        lBack = []
        try:
            qs = self.constructions.all().select_related()
            targetType = self.research.targetType
            for item in qs:
                oSearch = item.search.get_search_spec(targetType)
                if targetType == 'w':
                    # Only word
                    oItem = {'name': item.name, 'single': oSearch['single'], 'line_list': oSearch['line_list']}
                elif targetType == 'c':
                    # Only constituent category
                    oItem = {'name': item.name, 'cat_incl': oSearch['cat_incl'], 'cat_excl': oSearch['cat_excl']}
                elif targetType == 'e':
                    # Extended: combination of word(s), lemma, category, feature-category, feature-value
                    oItem = {'name': item.name, 
                             'single': oSearch['single'], 
                             'line_list': oSearch['line_list'], 
                             'cat_incl': oSearch['cat_incl'], 
                             'cat_excl': oSearch['cat_excl'],
                             'fcat': oSearch['fcat'],
                             'fval': oSearch['fval'],
                             'lemma': oSearch['lemma']}
                elif targetType == 'q':
                    # CQL type definition
                    oItem = {'cql': oSearch['cql'] }
                else:
                    oItem = {}
                # Potentially also 'related'
                if (targetType == 'c' or targetType == 'e' or targetType =='w') and ('related' in oSearch):
                    oItem['related'] = oSearch['related']
                lBack.append(oItem)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("get_search_list")
        return lBack

    def do_simple_related(self):
        """Evaluate the searches in the list, and expand 'Related' """

        oErr = ErrHandle()
        try:
            # Is this a SIMPLESEARCH of the correct target type?
            targetType = self.research.targetType
            gateway = self

            # if self.research.name == SIMPLENAME and ( targetType == "c" or targetType == "e" or targetType == "w"):
            if self.research.stype == STYPE_SIMPLE and ( targetType == "c" or targetType == "e" or targetType == "w"):
                # Clear any previous: (a) data-dependant variables, (b) conditions, (c) features
                if not self.clear_search():
                    # Show error message
                    oErr.DoError("ConvertProjectToXquery error: cannot clear previous search")
                    return

                # initializing
                dvar_order = 0
                cond_order = 0
                feat_order = 0

                bOldSystem = False  # Old translation system

                # Evaluate all constructions
                qs = self.constructions.all()
                for construction in qs:
                    # Get the search specification for this construction
                    oSearch = construction.search.get_search_spec(targetType)
                    # Check if this has related
                    if 'related' in oSearch:
                        # Yes, related criteria: interpret this list
                        for idx, oRel in enumerate(oSearch['related']):
                            # Get the characteristics of this construction
                            sName = oRel['name']        # Name of this variable
                            cat = oRel['cat']           # Syntactic category of the target
                            if cat == None or cat == "":
                                cat = "*"
                            raxis_id = oRel['raxis']    # Value number of the axis
                            towards = oRel['towards']   # Name of the item with which we relate
                            # text of the related element
                            reltext = "" if "reltext" not in oRel else oRel['reltext']
                            # lemma of the related (word)
                            rellemma = "" if "rellemma" not in oRel else oRel['rellemma']
                            # Figure out position
                            position = "1"
                            if 'pos' in oRel and oRel['pos'] != "": position = oRel['pos']
                            # Figure out skipping
                            skip = ""
                            if 'skip' in oRel: skip = oRel['skip']
                            skipcat = ""
                            if skip == "c" or skip == "e_c": skipcat = "CONJ|CONJP"
                            # General
                            varType = "calc"

                            # Get the correct relation from raxis_id
                            raxis = Relation.objects.filter(id=raxis_id).first()
                            if raxis == None:
                                # Proved a good error message
                                msg = "Gateway/do_simplerelated: there is no raxis id {}".format(raxis_id)
                                return False, msg

                            # Get the constituent towards with we are working
                            cnstype = "hit" if towards == "search" else "dvar"
                            if cnstype == "hit":
                                cnsval = "$search"
                            else:
                                # Prepend a dollar sign, if it is not there already
                                cnsval = towards
                                if cnsval[0] != "$":
                                    cnsval = "$" + cnsval
                        
                            # First add a DVAR for this line -- this automatically creates a CVAR
                            dvar_order += 1
                            dvar = VarDef(name=sName, order=dvar_order, 
                                          description="dvar for line #{}".format(idx),
                                          type=varType, gateway=gateway)
                            trials = 10
                            bDone = False
                            while not bDone:
                                try:
                                    dvar.save()
                                    bDone = True
                                except:
                                    # there is a database locked error probably
                                    sMsg = oErr.get_error_message()
                                    trials -= 1
                                    # Are we out of bounds?
                                    if trials <= 0:
                                        return False, sMsg
                            if dvar == None:
                                # Proved a good error message
                                msg = "Gateway/do_simplerelated: no dvar is created for line ${} trials={}".format(idx, trials)
                                return False, msg

                            # Retrieve the CVAR
                            cvar = ConstructionVariable.objects.filter(construction=construction, variable=dvar).first()
                            if cvar == None:
                                # Proved a good error message
                                msg = "Gateway/do_simplerelated: no cvar could be created for line {} (trials={})".format(idx, trials)
                                return False, msg
                            cvar.type=varType

                            # Add details for function [get_first_relative_cns]
                            arglist = []
                            if bOldSystem:
                                arglist.append({"order": 1, "name": "cns_1", "type":cnstype, "value": cnsval})
                                arglist.append({"order": 2, "name": "rel_1", "type":"raxis", "value": raxis.name})
                                arglist.append({"order": 3, "name": "cat_1", "type":"fixed", "value": cat})
                                lFunc = [ {"function": "get_first_relative_cns", "line": 0, "arglist": arglist}]
                            else:
                                # Use the new system: function depends on whether a category is specified
                                position = str(position)
                                if skip == "":
                                    # No skipping needed
                                    if position == "1":
                                        # Needed: cat
                                        arglist.append({"order": 1, "name": "cns_1", "type":cnstype, "value": cnsval})
                                        arglist.append({"order": 2, "name": "rel_1", "type":"raxis", "value": raxis.name})
                                        arglist.append({"order": 3, "name": "cat_1", "type":"fixed", "value": cat})
                                        lFunc = [ {"function": "get_first_relative_cns", "line": 0, "arglist": arglist}]
                                    else:
                                        if position == "1f": position = "1"
                                        # Needed: cat_pos
                                        arglist.append({"order": 1, "name": "cns_1", "type":cnstype, "value": cnsval})
                                        arglist.append({"order": 2, "name": "rel_1", "type":"raxis", "value": raxis.name})
                                        arglist.append({"order": 3, "name": "pos_1", "type":"fixed", "value": position})
                                        arglist.append({"order": 4, "name": "cat_1", "type":"fixed", "value": cat})
                                        lFunc = [ {"function": "get_related_cat_pos", "line": 0, "arglist": arglist}]
                                else:
                                    # Some skipping specified: e, c, e_c
                                    if position == "1":
                                        # Needed: cat_skip
                                        arglist.append({"order": 1, "name": "cns_1", "type":cnstype, "value": cnsval})
                                        arglist.append({"order": 2, "name": "rel_1", "type":"raxis", "value": raxis.name})
                                        arglist.append({"order": 3, "name": "skip_1", "type":"fixed", "value": skipcat})
                                        arglist.append({"order": 4, "name": "cat_1", "type":"fixed", "value": cat})
                                        lFunc = [ {"function": "get_first_cns_cat", "line": 0, "arglist": arglist}]
                                    else:
                                        if position == "1f": position = "1"
                                        # Needed: cat_skip_pos
                                        arglist.append({"order": 1, "name": "cns_1", "type":cnstype, "value": cnsval})
                                        arglist.append({"order": 2, "name": "rel_1", "type":"raxis", "value": raxis.name})
                                        arglist.append({"order": 3, "name": "skip_1", "type":"fixed", "value": skipcat})
                                        arglist.append({"order": 4, "name": "pos_1", "type":"fixed", "value": position})
                                        arglist.append({"order": 5, "name": "cat_1", "type":"fixed", "value": cat})
                                        lFunc = [ {"function": "get_related_cat_skip_pos", "line": 0, "arglist": arglist}]
                            # Create the function
                            func_main = Function.create_from_list(lFunc, gateway, "cvar", cvar, None, None)
                            func_main.save()
                            cvar.function = func_main
                            cvar.functiondef = func_main.functiondef
                            cvar.save()

                            # Add a condition to test that this related construction exists
                            cond_order += 1
                            cond = Condition(name="exist_{}".format(sName), order=cond_order,
                                          description="check existence of ${}".format(sName), include="true",
                                          condtype="func", gateway=gateway)
                            if cond == None:
                                # Proved a good error message
                                msg = "Gateway/do_simplerelated: could not create condition for {}".format(sName)
                                return False, msg
                            cond.save()
                            # Create and add details for the function: exist
                            arglist = []
                            arglist.append({"order": 1, "name": "cns_1", "type": "dvar", "value": "${}".format(sName)})
                            lFunc = [ {"function": "exists", "line": 0, "arglist": arglist}]
                            # Yes, create the functions
                            func_main = Function.create_from_list(lFunc, gateway, "cond", None, cond, None)
                            if func_main == None:
                                # Proved a good error message
                                msg = "Gateway/do_simplerelated: could not create main function for {}".format(sName)
                                return False, msg
                            func_main.save()
                            cond.function = func_main
                            cond.functiondef = func_main.functiondef
                            cond.save()

                            # If there is a reltext specification: add condition to test that the text matches
                            if reltext != "":
                                cond_order += 1
                                cond = Condition(name="hastext_{}".format(sName), order=cond_order,
                                              description="check text of ${}".format(sName), include="true",
                                              condtype="func", gateway=gateway)
                                cond.save()
                                # Create and add details for the function: exist
                                arglist = []
                                arglist.append({"order": 1, "name": "cns_1", "type": "dvar", "value": "${}".format(sName)})
                                arglist.append({"order": 2, "name": "str_1", "type": "fixed", "value": reltext})
                                lFunc = [ {"function": "has_text", "line": 0, "arglist": arglist}]
                                # Yes, create the functions
                                func_main = Function.create_from_list(lFunc, gateway, "cond", None, cond, None)
                                func_main.save()
                                cond.function = func_main
                                cond.functiondef = func_main.functiondef
                                cond.save()

                            # If there is a rellemma specification: add condition to test that the lemma is equal
                            if rellemma != "":
                                cond_order += 1
                                cond = Condition(name="haslemma_{}".format(sName), order=cond_order,
                                              description="check lemma of ${}".format(sName), include="true",
                                              condtype="func", gateway=gateway)
                                cond.save()
                                # Create and add details for the function: exist
                                arglist = []
                                arglist.append({"order": 1, "name": "cns_1", "type": "dvar", "value": "${}".format(sName)})
                                arglist.append({"order": 2, "name": "str_1", "type": "fixed", "value": rellemma})
                                lFunc = [ {"function": "has_lemma", "line": 0, "arglist": arglist}]
                                # Yes, create the functions
                                func_main = Function.create_from_list(lFunc, gateway, "cond", None, cond, None)
                                func_main.save()
                                cond.function = func_main
                                cond.functiondef = func_main.functiondef
                                cond.save()


                            # Add an output feature to show the TEXT of this related construction
                            feat_order += 1
                            feat = Feature(name="text_of_{}".format(sName), order=feat_order,
                                          description="The text of constituent ${}".format(sName), include="true",
                                          feattype="func", gateway=gateway)
                            feat.save()
                            # Create and add details for the function: exist
                            arglist = []
                            arglist.append({"order": 1, "name": "cns_1", "type": "dvar", "value": "${}".format(sName)})
                            lFunc = [ {"function": "get_text", "line": 0, "arglist": arglist}]
                            # create the functions
                            func_main = Function.create_from_list(lFunc, gateway, "feat", None, None, feat)
                            func_main.save()
                            feat.function = func_main
                            feat.functiondef = func_main.functiondef
                            feat.save()


                            # Add an output feature to show the CATEGORY of this related construction
                            feat_order += 1
                            feat = Feature(name="cat_of_{}".format(sName), order=feat_order,
                                          description="The category of constituent ${}".format(sName), include="true",
                                          feattype="func", gateway=gateway)
                            feat.save()
                            # Create and add details for the function: exist
                            arglist = []
                            arglist.append({"order": 1, "name": "cns_1", "type": "dvar", "value": "${}".format(sName)})
                            lFunc = [ {"function": "get_cat", "line": 0, "arglist": arglist}]
                            # create the functions
                            func_main = Function.create_from_list(lFunc, gateway, "feat", None, None, feat)
                            func_main.save()
                            feat.function = func_main
                            feat.functiondef = func_main.functiondef
                            feat.save()

            # Return positively
            return True, "ok"
        except:
            sMsg = oErr.get_error_message()
            oErr.DoError("Gateway/do_simple_related")
            return False, sMsg
        
    def delete(self, using = None, keep_parents = False):
        """Delete all items pointing to me, then delete myself"""

        oErr = ErrHandle()
        try:
            # Delete the global variables
            gvar_set = self.globalvariables.all()
            for gvar in gvar_set:
                gvar.delete()
            # Delete the definition variables
            dvar_set = self.definitionvariables.all().order_by('-order', '-id')
            for dvar in dvar_set:
                dvar.delete()
            # Delete the constructions (and what is under them)
            cns_set = self.constructions.all()
            for cns_this in cns_set:
                cns_this.delete()
            # Delete the conditions (and what is under them)
            cond_set = self.conditions.all()
            for cond_this in cond_set:
                cond_this.delete()
            # Delete the features (and what is under them)
            feat_set = self.features.all()
            for feat_this in feat_set:
                feat_this.delete()
            # Now perform the normal deletion
            # response = super(Gateway, self).delete(using, keep_parents)
            response = super(Gateway, self).delete(using, True)
        except:
            sMsg = oErr.get_error_message()
            response = None
        return response

    def get_vardef_list(self):

        # Get a list of all variables for this gateway
        vardef_list = self.definitionvariables.all().select_related().order_by('order')
        # Return this list
        return vardef_list

    def get_condition_list(self):
        # Get a list of conditions in order
        return self.conditions.all().select_related().order_by('order')

    def get_feature_list(self):
        # Get a list of features in order
        return self.features.all().select_related().order_by('order')

    def order_dvar(self):
        """Order the VarDef instances under me"""
        qs = self.definitionvariables.order_by('order', 'id')
        iOrder = 1
        with transaction.atomic():
            for dvar in qs:
                if dvar.order != iOrder:
                    dvar.order = iOrder
                    dvar.save()
                iOrder += 1
        return True

    def order_gvar(self):
        """Order the GlobalVariable instances under me"""
        qs = self.globalvariables.order_by('order', 'id')
        iOrder = 1
        with transaction.atomic():
            for gvar in qs:
                if gvar.order != iOrder:
                    gvar.order = iOrder
                    gvar.save()
                iOrder += 1
        return True

    def get_construction_list(self):
        # This method is nog used... :)
        return [cns for cns in self.constructions.select_related().all()]

    def check_cvar(self):
        """Check all the CVAR connected to me, adding/deleting where needed"""

        bResult = True
        sMsg = ""
        oErr = ErrHandle()
        try:
            # Step 1: Add combination[s] of vardef/construction if it doesn't yet exist
            with transaction.atomic():
                # Step 1: add CVAR for all Construction/Vardef combinations
                for vardef in self.get_vardef_list():
                    # Walk all constructions
                    for construction in self.constructions.all():
                        # Check if a cvar exists
                        cvar = ConstructionVariable.objects.filter(variable=vardef, construction=construction).first()
                        if cvar == None:
                            # Doesn't exist: create it
                            cvar = ConstructionVariable.objects.create(variable=vardef, construction=construction)

            # Step 2: Find CVAR that do not belong to a gateway
            gateway_pk_list = [x['id'] for x in Gateway.objects.all().values("id")]

            #cvar_orphans = [cvar['id'] for cvar in ConstructionVariable.objects.exclude(construction__gateway__in=gateway_pk_list).values("id")]
            #if len(cvar_orphans) > 0:
            #    ConstructionVariable.objects.filter(id__in=cvar_orphans).delete()

            #cvar_orphans = [cvar['id'] for cvar in ConstructionVariable.objects.exclude(variable__gateway__in=gateway_pk_list).values("id")]
            #if len(cvar_orphans) > 0:
            #    ConstructionVariable.objects.filter(id__in=cvar_orphans).delete()

            # GEt a list of Gateway IDs that are mentioned from ConstructionVariable
            delete_cv = []
            lst_variable_gateway = ConstructionVariable.objects.all().values("id", "variable__gateway__id").distinct()
            lst_construc_gateway = ConstructionVariable.objects.all().values("id", "construction__gateway__id").distinct()
            for item in lst_variable_gateway:
                cv_id=item['id']
                gw_id=item['variable__gateway__id']
                if gw_id not in gateway_pk_list:
                    # Add the CV id to the deletable ones
                    delete_cv.append(cv_id)
            for item in lst_construc_gateway:
                cv_id=item['id']
                gw_id=item['construction__gateway__id']
                if gw_id not in gateway_pk_list:
                    # Add the CV id to the deletable ones
                    delete_cv.append(cv_id)

            # If there is something to be deleted, then 
            if len(delete_cv) > 0:
                ConstructionVariable.objects.filter(id__in=delete_cv).delete()



        except:
            sMsg = oErr.get_error_message()
            oErr.DoError("Gateway/check_var")
            bResult = False
        # Make sure we are happy
        return bResult, sMsg

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
      # Save the gateway
      response = super(Gateway, self).save(force_insert, force_update, using, update_fields)
      # Adapt the saved date of the research project
      if Research.objects.filter(gateway=self).first() != None:
          self.research.save()
      return response

    def get_status(self):
        """The status of a gateway consists of checking arguments for cvar, condition, feature"""

        # Initialize
        oStatus = {'status': "ok", 'msg': ''}
        oErr = ErrHandle()
        try:
            # Check all cvars
            for cns in self.constructions.all():
                for dvar in self.definitionvariables.all():
                    cvar = ConstructionVariable.objects.filter(construction=cns, variable=dvar).first()
                    if cvar != None:
                        oCvarStatus = cvar.argcheck()
                        if oCvarStatus != None and 'status' in oCvarStatus and oCvarStatus['status'] != "ok":
                            # Adapt the status
                            oStatus['status'] = "error"
                            oStatus['msg'] = oCvarStatus['msg']
                            if 'type' in oCvarStatus:
                                oStatus['type'] = oCvarStatus['type']
                            if 'id' in oCvarStatus:
                                oStatus['id'] = oCvarStatus['id']
                            # And immediately return the status
                            return oStatus
            # Check all conditions
            for cnd in self.conditions.all():
                if cnd != None:
                    oCondStatus = cnd.argcheck()
                    if oCondStatus != None and 'status' in oCondStatus and oCondStatus['status'] != "ok":
                        # Adapt the status
                        oStatus['status'] = "error"
                        oStatus['msg'] = oCondStatus['msg']
                        if 'type' in oCondStatus:
                            oStatus['type'] = oCondStatus['type']
                        if 'id' in oCondStatus:
                            oStatus['id'] = oCondStatus['id']
                        # And immediately return the status
                        return oStatus
            # Check all features
            for feat in self.features.all():
                if feat != None:
                    oFeatStatus = feat.argcheck()
                    if oFeatStatus != None and 'status' in oFeatStatus and oFeatStatus['status'] != "ok":
                        # Adapt the status
                        oStatus['status'] = "error"
                        oStatus['msg'] = oFeatStatus['msg']
                        if 'type' in oFeatStatus:
                            oStatus['type'] = oFeatStatus['type']
                        if 'id' in oFeatStatus:
                            oStatus['id'] = oFeatStatus['id']
                        # And immediately return the status
                        return oStatus
            return oStatus
        except:
            sMsg = oErr.get_error_message()
            oStatus['status'] = "error"
            oStatus['msg'] = sMsg
            return oStatus


class Construction(models.Model):
    """A search construction consists of a [search] element and one or more search items"""

    # [1] Construction name
    name = models.CharField("Name of this search construction", max_length=MAX_TEXT_LEN)
    # [1] Main search item
    search = models.ForeignKey(SearchMain, blank=False, null=False, on_delete=models.CASCADE, related_name="search_constructions")
    # [1] Every gateway has one or more constructions it may look for
    gateway = models.ForeignKey(Gateway, blank=False, null=False, on_delete=models.CASCADE, related_name="constructions")

    def __str__(self):
        return self.name

    def get_copy(self, **kwargs):
        # Test
        if kwargs == None or 'gateway' not in kwargs:
            return None
        # Possibly copy the search element
        new_search = self.search
        if new_search != None:
            new_search = new_search.get_copy(**kwargs)
        # Make a clean copy
        new_copy = Construction(name=self.name, search=new_search, gateway=kwargs['gateway'])
        new_copy.save(check_cvar = False)
        # Return the new copy
        return new_copy

    def delete(self, using = None, keep_parents = False):
        """Delete all items pointing to me, then delete myself"""

        # Delete the related construction variables
        cvar_set = self.constructionvariables.all()
        for cvar in cvar_set:
            cvar.delete()
        # Also delete the searchMain
        self.search.delete()
        # And then delete myself
        return super(Construction, self).delete(using, keep_parents)

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None, check_cvar = True):
      save_result = super(Construction, self).save(force_insert, force_update, using, update_fields)
      # Check and add/delete CVAR instances for this gateway
      if check_cvar:
          Gateway.check_cvar(self.gateway)
      # Return the result of normal saving
      return save_result

    def get_dvars(self):
        """Get a list of all data-dependant variables for this construction"""
        qs = ConstructionVariable.objects.filter(construction=self).order_by('variable__order')
        return qs

      
class Variable(models.Model):
    """A variable has a name and a value, possibly combined with a function and a condition"""

    # [1] Variable obligatory name
    name = models.CharField("Name", max_length=MAX_NAME_LEN)
    # [1] The numerical order of this argument
    order = models.IntegerField("Order", blank=False, default=0)
    # [0-1] Description/explanation for this variable
    description = models.TextField("Description")
    # [0-1] The type of the variable. May be unknown initially and then calculated
    type = models.CharField("Type", blank=True, choices=build_choice_list(SEARCH_TYPE), 
                              max_length=5, help_text=get_help(SEARCH_TYPE))

    def __str__(self):
        return self.name


class VarDef(Variable):
    """Each research project may have a number of variables that are construction-specific"""

    # [1] Link to the Gateway the variable belongs to
    gateway = models.ForeignKey(Gateway, blank=False, null=False, on_delete=models.CASCADE, related_name="definitionvariables")

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
      # Perform the normal saving
      save_result = super(VarDef, self).save(force_insert, force_update, using, update_fields)
      oErr = ErrHandle()
      try:
          # Check and add/delete CVAR instances for this gateway
          bCheck, msg = Gateway.check_cvar(self.gateway)
      except:
          msg2 = oErr.get_error_message()
          oErr.DoError("VarDef/save ({})".format(msg))
      # Return the result of normal saving
      return save_result

    def get_code(self, cnsThis, format):
        """Provide Xquery code for this construction group and format"""
        lstQ = []
        lstQ.append(Q(construction=cnsThis))
        lstQ.append(Q(variable=self))
        cvar = ConstructionVariable.objects.filter(*lstQ).first()
        return cvar.get_code(format)

    def get_copy(self, **kwargs):
        # Test
        if kwargs == None or 'gateway' not in kwargs:
            return None
        # Make a clean copy
        new_copy = VarDef(name=self.name, description=self.description, order=self.order, type=self.type, gateway=kwargs['gateway'])
        new_copy.save()
        # Return the new copy
        return new_copy

    def delete(self, using = None, keep_parents = False):
        """Deleting a VarDef means: also delete all the CVAR instances pointing to me"""

        # Delete the CVAR instances under me
        for var_inst in self.variablenames.all():
            var_inst.delete()
        # Now delete myself
        result = super(VarDef, self).delete(using, keep_parents)
        # re-order the dvar collection under this gateway
        self.gateway.order_dvar()
        # Return the result
        return result

    def get_outputtype(self):

        # Default value
        sType = "-"
        # Get the *FIRST* construction variable under the dvar
        cvar = self.variablenames.first()
        if cvar != None:
            # take over the type of this cvar
            sType = cvar.get_outputtype()
        return sType

    def get_restricted_vardef_list(qs_dvar, obltype):
        dvar_list = []
        for dvar in qs_dvar:
            if obltype == None:
                # Just add it
                dvar_list.append(dvar.id)
            else:
                # Check the output type
                otype = dvar.get_outputtype()
                if otype == None:
                    pass
                else:
                    # This dvar has a specific output type 
                    if arg_matches(obltype, otype):
                        dvar_list.append(dvar.id)

        # Recombine into a new list
        return VarDef.objects.filter(Q(id__in=dvar_list)).select_related().order_by('order')

    def check_order(self, order):
        """Find out whether the [order] differs from the current [order], and if so, is it okay?"""

        if order == None:
            return True, ""
        # Check for integer
        if not isinstance(order, int):
            return False, "Check order: the order must be an integer but it now is [{}]".format(order)

        # Has the order changed?
        bValid = True
        oErr = ErrHandle()

        try:
            # Note: Right now we are *ALWAYS* checking the order!!!
            if order != self.order or True:
                # The order is being changed, so check all the actual construction variable pointing to me
                for cvar in ConstructionVariable.objects.filter(variable=self).order_by('variable__order'):
                    # Is this a function?
                    if cvar.type == 'calc':
                        # Get a list of all functions used for this cvar
                        func_list = Function.objects.filter(root=cvar)
                        for func in func_list:
                            # Visit all arguments of this function that point to a dvar
                            for idx, arg in enumerate(Argument.objects.filter(function=func, argtype='dvar').order_by('argumentdef__order')):
                                # Check out the order of this dvar
                                dvar = arg.dvar
                                if dvar != None and dvar.order > order:
                                    # We have an argument order problem - report this
                                    #sMsg = "The function defined for variable {} moving from {} to position {} refers to variable {} at a later position {}".format(
                                    #    self.name, self.order, order, dvar.name, dvar.order)
                                    sMsg = "The definition of variable {} at position {} has a function [{}] whose argument #{} refers to variable {} at a later position {}".format(
                                        self.name, order, func.functiondef.name, idx+1, dvar.name, dvar.order)
                                    return False, sMsg


            # Return our verdict
            return bValid, ""
        except:
            sMsg = oErr.get_error_message()
            return False, "Vardef check_order: {}".format(sMsg)


class GlobalVariable(Variable):
    """Each research project may have any number of global (static) variables"""

    # [1] Value of the variable
    value = models.TextField("Value")
    # [1] Link to the Gateway the variable belongs to
    gateway = models.ForeignKey(Gateway, blank=False, null=False, on_delete=models.CASCADE, related_name="globalvariables")

    def __str__(self):
        # The default string-value of a global variable is its name
        return self.name

    def get_copy(self, **kwargs):
        # Test
        if kwargs == None or 'gateway' not in kwargs:
            return None
        # Make a clean copy
        new_copy = GlobalVariable(name=self.name, description=self.description, order=self.order, value=self.value, type=self.type, gateway=kwargs['gateway'])
        new_copy.save()
        # Return the new copy
        return new_copy

    def can_delete(self):
        # A global variable can only be deleted, if it is not referred to from functions anymore
        qs = Argument.objects.filter(gvar=self)
        # The gvar can be deleted if the queryset is empty
        return qs.count() == 0

    def delete(self, using = None, keep_parents = False):
        # Note the gateway
        gateway = self.gateway
        # Delete myself
        result = super(GlobalVariable, self).delete(using, keep_parents)
        # TODO: re-order the gvar collection
        gateway.order_gvar()
        # Return the deletion result
        return result

    def get_outputtype(self):
        """Calculate the output type of a function"""

        # Look at the string value of [svalue]
        if is_integer(self.value):
            sType = "int"
        elif is_boolean(self.value):
            sType = "bool"
        else:
            sType = "str"
        return sType


class FunctionDef(models.Model):
    """Definition of one function"""

    # [1] The short (internal) name of this function
    name = models.CharField("Short function name", max_length=MAX_NAME_LEN)
    # [1] The title of this function to be shown
    title = models.CharField("Function title", max_length=MAX_TEXT_LEN)
    # [1] Each function must have one or more arguments
    argnum = models.IntegerField("Number of arguments", default=1)
    # [0-1] The output type of the function. May be unknown initially and then calculated
    type = models.CharField("Type", blank=True, choices=build_choice_list(SEARCH_TYPE), 
                              max_length=5, help_text=get_help(SEARCH_TYPE))

    def __str__(self):
        return "{} ({} args)".format(self.name, self.argnum)

    def get_list():
        return FunctionDef.objects.all().order_by('name')

    def get_function_count(self):
        """Calculate how many *functions* actually contain this functiondef"""

        cnt = Function.objects.filter(functiondef=self).count()
        return cnt

    def get_arguments(self):
        qs = self.arguments.all().select_related().order_by('order')
        return qs

    def get_functions_with_type(obltype):
        """Get a queryset of functiondef objects returning [obltype]"""

        # Any function delivering the exact type is okay
        query = Q(type=choice_value(SEARCH_TYPE, obltype))
        # Any function that has NO type is okay too
        query |= Q(type="")
        # Some other types are intercompatible too
        if obltype == 'str':
            query |= Q(type=choice_value(SEARCH_TYPE,'int'))
            query |= Q(type=choice_value(SEARCH_TYPE,'bool'))
        elif obltype == 'clist':
            # If we expect a clist, then one cnst is okay too
            query |= Q(type=choice_value(SEARCH_TYPE,'cnst'))
        elif obltype == 'cnst':
            # If we expect a constituent (cnst), then also allow [clist], but we need to take the *first* one...
            query |= Q(type=choice_value(SEARCH_TYPE,'clist'))
        # COmbine the possiblities with 'or' signs
        qs = FunctionDef.objects.filter(query).select_related().order_by('name')
        return qs


class FunctionCode(models.Model):
    """Basic Xquery code for a function in a particular format"""

    # [1] Must have a specific format
    format = models.CharField("XML format", choices=build_abbr_list(CORPUS_FORMAT), 
                              max_length=5, help_text=get_help(CORPUS_FORMAT))
    # [1] Room for a place to define the xquery code
    xquery = models.TextField("Xquery code", null=True, blank=True, default="(: Xquery code for function :)")
    # [1] Must belong to one functiondef
    functiondef = models.ForeignKey(FunctionDef, null=False, on_delete=models.CASCADE, related_name="functioncodings")
    
    def __str__(self):
        return "{} ({})".format(self.functiondef.name, self.format)


class Function(models.Model):
    """Realization of one function based on a definition"""

    # [1] Must point to a definition
    functiondef = models.ForeignKey(FunctionDef, null=False, on_delete=models.CASCADE, related_name="functiondef_functions")
    # [0-1] A function belongs to a construction variable - but this is not necessarily the parent
    root = models.ForeignKey("ConstructionVariable", null=True, on_delete=models.SET_NULL, related_name="functionroot")
    # [0-1] Alternatively, a function belongs to a condition
    rootcond = models.ForeignKey("Condition", null=True, on_delete=models.SET_NULL, related_name="functioncondroot")
    # [0-1] Alternatively, a function belongs to a condition
    rootfeat = models.ForeignKey("Feature", null=True, on_delete=models.SET_NULL, related_name="functionfeatroot")
    # [0-1] A function MAY belong to a particular ARGUMENT, which then is its parent
    parent = models.ForeignKey("Argument", null=True, blank=True, on_delete=models.SET_NULL, related_name="functionparent")
    # [0-1] The output type of the function. May be unknown initially and then calculated
    type = models.CharField("Type", blank=True, choices=build_choice_list(SEARCH_TYPE), 
                              max_length=5, help_text=get_help(SEARCH_TYPE))
    # [0-1] FIlled-in line number
    line = models.IntegerField("Line number", default=0)
    # [1] The value that is the outcome of this function
    #     This is a JSON list, so can be bool, int, string of any number
    output = models.TextField("JSON value", null=False, blank=True, default="[]")
    # [1] Text-json to indicate the status of this 
    status = models.TextField("Status", default="{}")

    def __str__(self):
        return "f_{}:{}".format(self.id,self.output)

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
        # Any change in the function results in the status being set to 'stale'
        myStatus = json.loads(self.status)
        myStatus['status'] = "stale"
        self.status = json.dumps(myStatus)
        return super(Function, self).save(force_insert, force_update, using, update_fields)

    def set_status(self, sStatus):
        """Set the status to the one indicated in [sStatus]"""

        myStatus = json.loads(self.status)
        myStatus['status'] = sStatus
        self.status = json.dumps(myStatus)
        self.save()

    def argcheck(self):
        """Check the argument-compatibility of this function"""

        # Assume the best
        oStatus = {'status': "ok", 'msg': ''}
        myStatus = json.loads(self.status)
        if not 'status' in myStatus or myStatus['status'] != "ok":
            # Reset the previous status
            self.status = "{}"
            # Get all the arguments in the argdef order
            arg_list = self.get_arguments()
            # Get all the argument definitions for this functiondef in the argdef order
            argdef_list = self.functiondef.get_arguments()
            # Compare the numbers
            if arg_list.count() != argdef_list.count():
                oStatus['status'] = "error"
                oStatus['msg'] = "Function [{}] of line {} has {} arguments, but {} are required".format(
                    self.functiondef.name, self.line, arg_list.count(), argdef_list.count())
            else:
                # The argument number is okay, now check the type of each argument
                for idx, arg in enumerate(arg_list):
                    # Also get the argdef
                    argdef = argdef_list[idx]
                    # Check if the argdef type is equal to my own arg's type
                    if argdef.obltype != None and arg != None:
                        # We need to compare types
                        arg_outputtype = arg.get_outputtype()
                        if not arg_matches(argdef.obltype, arg_outputtype, arg.argval):
                        # if argdef.obltype != arg_outputtype:
                            # Type mismatch
                            oStatus['status'] = "error"
                            oStatus['msg'] = "Function [{}], line {}, argument {}: argument type is {} but should be {}".format(
                                self.functiondef.name, self.line+1, idx+1, arg_outputtype, argdef.obltype)
                            # Break out of the for-loop
                            break
        return oStatus

    def get_output(self):
        """Calculate or return the stored output of me"""

        oErr = ErrHandle()
        oBack = {'value': None, 'status': "ok"}
        try:
            if self.output == "" or self.output == "[]" or self.output == "{}":
                # This means we need to re-calculate
                oCode = {"line": self.line, "function": self.functiondef.name, "arglist": []}
                # If I am part of an argument, I need a name
                if self.parent != None:
                    oCode['name'] = "$__line_{}".format(self.line)
                # Get all my arguments
                arglist = []
                for arg in self.get_arguments():
                    # Get the code of this argument
                    oArg = json.loads(arg.get_output())
                    arglist.append(oArg)
                oCode['arglist'] = arglist

                # Now adapt the output of myself
                # OLD: self.output = json.dumps(oCode)
                oBack['value'] = oCode
            # REturn the output
            # OLD: return self.output
            return oBack
        except:
            oBack['value'] = "error"
            oBack['status'] = "error"
            oBack['msg'] = oErr.get_error_message()
            return oBack

    def get_code(self, format, method="recursive"):
        """Create and return the required Xquery"""
        oErr = ErrHandle()
        sCode = ""
        oBack = {'code': ''}
        try:
            # Get the basis from the correct format part of the FunctionDef
            code = self.functiondef.functioncodings.filter(format=format).first()
            if code == None:
                # SOmething went wrong, so I am not able to get the code for this function
                self.root.construction.gateway.error_add("Cannot get the Xquery translation for function [{}]".format(self.functiondef.name))
            else:
                # Check: compare the number of arguments
                iArgNumReal = self.functionarguments.all().count()
                iArgNumDef = self.functiondef.arguments.all().count()
                if iArgNumDef != iArgNumReal:
                    oBack['error'] = "Function {} expects {} arguments, but gets {}".format(
                        self.functiondef.name, iArgNumDef, iArgNumReal)
                # Get the code of this current function
                sCode = code.xquery
                # Get and replace the code for the arguments
                for idx, arg in enumerate(self.get_arguments()):
                    # Check this argument for validity
                    sArgErr = arg.get_argument_error()
                    if sArgErr != "":
                        # Process the argument error
                        oBack['error'] = "Function {} reports an error in argument {}: {}".format(
                            self.functiondef.name, idx+1, sArgErr)
                    # Two alternatives for the argument-encoding
                    sArg = "$__arg[{}]".format(idx+1)
                    sAlt = "$_arg[{}]".format(idx+1)

                    # Get argument code: NOTE: pass on the method
                    sArgCode = arg.get_code(format, method)

                    # Replace the code in the basis
                    sCode = sCode.replace(sArg, sArgCode)
                    sCode = sCode.replace(sAlt, sArgCode)

                # If plain method, add assignment
                if method == "plain":
                    sCode = "let $__line{} := {}".format(self.get_line(), sCode)
            # Return the code that we have produced
            oBack['code'] = sCode
            return oBack
        except:
            oErr.DoError("Function/get_code error")
            oBack['error'] = "function/get_code error: $ERROR_FUNCTION_{}".format(self.id)
            return oBack

    def get_codedef(self, format):
        """Create and return the required Xquery for the 'definition' part of a function
        
        Note: this is only for the 'plain' method;
              the recursive method does not require pre-calculation of the definition part
        """

        sCode = ""

        # Return what has been made
        return sCode

    def get_copy(self, **kwargs):
        # Make a clean copy
        # new_copy = get_instance_copy(self)
        new_copy = Function(functiondef=self.functiondef,
                            type = self.type,
                            output=self.output)
        # Initial saving
        new_copy.save()
        # if the root is provided, change that straight away
        if kwargs != None and 'root' in kwargs:
            new_copy.root = kwargs['root']
        if kwargs != None and 'rootcond' in kwargs:
            new_copy.rootcond = kwargs['rootcond']
        if kwargs != None and 'rootfeat' in kwargs:
            new_copy.rootfeat = kwargs['rootfeat']
        # COpy other fields, if they are not yet set
        if self.root != None and new_copy.root == None:
            new_copy.root = self.root
        # COpy other fields, if they are not yet set
        if self.rootcond != None and new_copy.rootcond == None:
            new_copy.rootcond = self.rootcond
        # Same for rootfeat
        if self.rootfeat != None and new_copy.rootfeat == None:
            new_copy.rootfeat = self.rootfeat

        # Process parent
        if kwargs != None and 'parent' in kwargs:
            new_copy.parent = kwargs['parent']

        # Copy all 12m fields
        kwargs['function'] = new_copy
        copy_m2m(self, new_copy, "functionarguments", **kwargs)    # Argument
        # Save it ( but this may be delayed when transaction.atomic() is used)
        new_copy.save()
        # Return the new copy
        return new_copy

    def delete(self, using = None, keep_parents = False):
        # First delete any ARG elements pointing to me
        # qs = self.argument_set.all()
        qs = self.functionarguments.all()
        for arg in qs:
            arg.delete()
        # Now delete myself
        result = super(Function, self).delete(using, keep_parents)
        # # Save the changes
        # self.save()
        return result

    def create_from_list(lFunc, gateway, sType, root, rootcond, rootfeat):
        """Create the list of functions specified in [lFunc]
        
        The sType can be construction, condition or feature.
        Return the top function's instance
        """

        func_main = None
        try:
            # Prepare an object that provides a keymap to the functions
            func_map = {}
            # First pass: create all the functions in order
            for oFunc in lFunc:
                # Get the function definition
                functiondef = FunctionDef.objects.filter(name=oFunc['function']).first()
                # Create a bare function definition
                func = Function.create(functiondef, root, rootcond, None, rootfeat)
                # At least adapt what we know
                func.line = oFunc['line']
                # Note: function is already saved within create()
                oFunc['obj'] = func
                # Make sure we have the main function
                if func_main == None:
                    func_main = func
                # Possibly add the function to the map
                if 'name' in oFunc:
                    func_map[oFunc['name']] = func

            # Now evaluate the functions again, but with the accompanying arguments
            for oFunc in lFunc:
                # Get the function
                func = oFunc['obj']
                for oArg in oFunc['arglist']:
                    # Retrieve the argument (it has already been created)
                    arg = func.functionarguments.filter(argumentdef__order=oArg['order']).first()
                    arg.argtype = oArg['type']
                    argval = oArg['value']
                    if oArg['type'] == "func":
                        # The value points to the line through the func_map variable
                        if argval in func_map:
                            rel_func = func_map[argval]
                            # Bind that function to this argument
                            rel_func.parent = arg
                            rel_func.save()
                            # Set the functiondef of the argument correctly
                            arg.functiondef = rel_func.functiondef
                        else:
                            # TODO: there's a relation missing, but really
                            #       nothing we can do about it at this point, I suppose...
                            pass
                    elif oArg['type'] == "fixed":
                        arg.argval = argval
                    elif oArg['type'] == "rcnst":       # Relative constituent
                        arg.rconst = Relation.objects.filter(name=argval, type="const").first()
                    elif oArg['type'] == "rcond":       # Relative condition
                        arg.rcond = Relation.objects.filter(name=argval, type="cond").first()
                    elif oArg['type'] == "raxis":       # Relation/axis
                        arg.raxis = Relation.objects.filter(name=argval, type="axis").first()
                    elif oArg['type'] == "hit":         # Search hit
                        # No need to further specify the value
                        pass
                        # arg.argval = "$search"          # No need to further specify the value
                    elif oArg['type'] == "gvar":        # global variable
                        gvar = gateway.globalvariables.filter(name= strip_varname(argval)).first()
                        arg.gvar = gvar
                    elif oArg['type'] == "dvar":        # definition variable
                        dvar = gateway.definitionvariables.filter(name= strip_varname(argval)).first()
                        arg.dvar = dvar
                    elif oArg['type'] == "cnst":        # constituent
                        arg.argval = "[]"               # No need to further specify the value
                    # Make sure the adapted argument gets saved
                    arg.save()
        except:
            msg = errHandle.get_error_message()
            func_main = None
            # x = func_main.functionarguments.all()
        # Return the top function
        return func_main

    def get_research(self):
        """Get the Research instance to which this function is connected"""

        research = None
        gateway = None
        if self.root != None:
            # This seems to be a CVAR
            gateway = self.root.construction.gateway
        elif self.rootcond != None:
            # This seems to be a condition
            gateway = self.rootcond.gateway
        elif self.rootfeat != None:
            # This seems to be a feature
            gateway = self.rootfeat.gateway
        # Get from gateway to research
        if gateway != None:
            research = gateway.research
        # Return the research that has been located
        return research

    @classmethod
    def create(cls, functiondef, functionroot, functioncondroot, parentarg, functionfeatroot=None):
        """Create a new instance of a function based on a 'function definition', binding it to a cvar or a condition"""

        oErr = ErrHandle()
        with transaction.atomic():
            if parentarg == None:
                if functionroot != None:
                    inst = cls(functiondef=functiondef, root=functionroot)
                elif functioncondroot != None:
                    inst = cls(functiondef=functiondef, rootcond=functioncondroot)
                elif functionfeatroot != None:
                    inst = cls(functiondef=functiondef, rootfeat=functionfeatroot)
                else:
                    # This should actually create an error...
                    inst = cls(functiondef=functiondef)
            else:
                # There is a parentarg
                if functionroot != None:
                    inst = cls(functiondef=functiondef, root=functionroot, parent=parentarg)
                elif functioncondroot != None:
                    inst = cls(functiondef=functiondef, rootcond=functioncondroot, parent=parentarg)
                elif functionfeatroot != None:
                    inst = cls(functiondef=functiondef, rootfeat=functionfeatroot, parent=parentarg)
                else:
                    # This should actually create an error...
                    inst = cls(functiondef=functiondef, parent=parentarg)
            try:
                # Save this function
                inst.save()
                # Add all the arguments that are needed
                for argdef in functiondef.arguments.all():
                    arg = Argument(argumentdef=argdef, argtype=argdef.argtype, 
                                   functiondef=functiondef, function=inst)
                    # Save this argument
                    arg.save()
            except:
                oErr.DoError("Function.create error:")
        return inst

    def changedefinition(self, functiondef):
        """Change the function definition to the one indicated"""

        # Get the instance
        inst = self
        # Check if change is needed
        if inst.functiondef != functiondef:
            # Changes are needed, yes
            with transaction.atomic():
                # Adapt the functiondef
                inst.functiondef = functiondef
                # Remove associated arguments
                inst.functionarguments.all().delete()
                # Save this function
                inst.save()
                # Add all the arguments that are needed
                for argdef in functiondef.arguments.all():
                    arg = Argument(argumentdef=argdef, argtype=argdef.argtype, 
                                   functiondef=functiondef, function=inst)
                    # Save this argument
                    arg.save()
         # Return the function instance = self  
        return inst

    def get_level(self):
        """Find out at what level of depth this function is"""
        iLevel = 0
        parentarg = self.parent
        while parentarg != None:
            iLevel += 1
            parentarg = parentarg.function.parent
        return iLevel

    def get_level_range(self):
        iLevel = self.get_level()
        return range(0, iLevel)

    def get_line(self):
        """Determine which line in the function table this is at"""
        iLine = self.line
        if iLine == 0:
            id = self.id
            # The start function depends on there being a root or rootcond
            start_function = None
            if self.root != None:
                start_function = self.root.function
            elif self.rootcond != None:
                start_function = self.rootcond.function
            elif self.rootfeat != None:
                start_function = self.rootfeat.function
            # Double check: do we have a start_function?
            if start_function != None:
                lFunc = start_function.get_functions()
                for idx in range(len(lFunc)):
                    if lFunc[idx].id == id:
                        iLine = idx+1
                        break
            self.line = iLine
            self.save()
        return iLine

    def get_functions(self):
        """Get all the functions including myself and those descending under me"""

        func_this = self
        func_list = [func_this]
        # Walk all arguments
        for arg_this in func_this.functionarguments.all().select_related():
            # CHeck if this is a function argument
            if arg_this.argtype == "func":
                # Then add the function pointed to by the argument
                arg_func = arg_this.functionparent.first()
                if arg_func != None:
                    arg_func_list = arg_func.get_functions()
                    for func in arg_func_list:
                        func_list.append(func)
        return func_list

    def get_ancestors(self):
        """Provide a list of the most important information of all ancestors above me"""
        anc_list = []
        iLevel = 0
        parentarg = self.parent
        while parentarg != None:
            # Adapt the level
            iLevel += 1
            if parentarg.function and parentarg.function.parent:
                arg_id = parentarg.function.parent.id
            else:
                arg_id = None
            # Some information depends on root versus rootcond
            cvar_id = None if self.root == None else self.root.id
            cond_id = None if self.rootcond == None else self.rootcond.id
            feat_id = None if self.rootfeat == None else self.rootfeat.id
            # Get the information of this parent-argument
            info = {'level': iLevel, 
                    'arginfo': parentarg.get_info(),
                    'func_id': parentarg.function.id,
                    'arg_num': parentarg.function.functiondef.argnum,
                    'arg_order': parentarg.argumentdef.order,
                    'arg_id': arg_id,
                    'cvar_id': cvar_id,
                    'cond_id': cond_id,
                    'feat_id': feat_id,
                    'arg': parentarg }
            # Store it in the ancestor list
            anc_list.append(info)
            parentarg = parentarg.function.parent
        # Adapt the indentation levels
        num = len(anc_list)
        for item in anc_list:
            item['level'] = num - item['level']
        # Return the list we have made
        return anc_list

    def get_arguments(self):
        qs = self.functionarguments.all().select_related().order_by('argumentdef__order')
        return qs

    def get_arg_groups(self):
        """Divide the arguments into groups on the basis of being a function argument or not"""

        glist = []          # List of groups
        alist = None
        bInGroup = False    # Whether I am in a group of non-func arguments
        for arg in self.functionarguments.all().select_related().order_by('argumentdef__order'):
            if arg.argtype == 'func':
                # Do we need to finish an alist?
                if bInGroup:
                    bInGroup = False
                    if alist != None and len(alist)>0:
                        glist.append({"type": "plain", "list": alist})
                        alist = []
                # This is a function, so treat it separately
                alist = [arg]
                glist.append({"type": "func", "list": alist})
            else:
                # Start a new arglist or not?
                if not bInGroup:
                    alist = []
                    bInGroup = True
                # Add to the existing alist
                alist.append(arg)
        # Do we need to append the last alist?
        if bInGroup and len(alist)>0:
            glist.append({"type": "plain", "list": alist})                
        return glist

    def get_outputtype(self):
        """Calculate the output type of a function"""

        # Initial guess: unknown
        sType = "-"
        # Check if we have a type that is specified
        if self.type and self.type != "":
            # There already is a type, so return the abbreviation:
            #   'str', 'int', 'bool', 'cnst' (=constituent)
            sType = choice_abbreviation(SEARCH_TYPE, self.type)
        elif self.functiondef:
            # Does this functiondef come with an actual type?
            if self.functiondef.type == "":
                # No it does not -- try to look at its first argument with hasoutputtype set
                arg = self.functionarguments.filter(Q(argumentdef__hasoutputtype=True)).first()
                # Return the type of this argument
                sType = arg.get_outputtype()
            else:
                # So: have a look at what *should* be the output type of this function
                #     given its definition
                sType = choice_abbreviation(SEARCH_TYPE, self.functiondef.type)
        else:
            # Look for the first Argument that should have the output type
            qs = self.get_arguments()
            arg = qs.filter(Q(argumentdef__hasoutputtype=True)).first()
            if arg != None:
                # Get the abbreviation of the argtype (fixed, gvar, cvar, func, cnst, axis, hit, dvar)
                # sArgType = choice_abbreviation(SEARCH_ARGTYPE, arg.argtype)
                sArgType = arg.argtype
                if sArgType == "fixed":
                    # Look at the string value of [argval]
                    if is_integer(arg.argval):
                        sType = "int"
                    elif is_boolean(arg.argval):
                        sType = "bool"
                    else:
                        sType = "str"
                elif sArgType == "gvar":
                    # Global variables are always strings
                    if arg.gvar != None:
                        sType =arg.gvar.get_outputtype()
                elif sArgType == "cvar":
                    # The argtype 'cvar' should not be used
                    pass
                elif sArgType == "func":
                    # Return the output type of the function the argument points to
                    argfun = self.functionparent.all().first()
                    if argfun != None:
                        # Yes, there is a function pointing to me as parent
                        sType = argfun.get_outputtype()
                elif sArgType == "hit" or sArgType == "cnst":
                    # The argtype "constituent" is not really used now, is it...
                    sType = "cnst"
                elif sArgType == "raxis":
                    # The argtype 'raxis' has a special 'search.type'
                    sType = "raxis"
                elif sArgType == "rcond":
                    # The argtype 'rcond' has a special 'search.type'
                    sType = "rcond"
                elif sArgType == "rcnst":
                    # The argtype 'rcnst' boils down to constituent
                    sType = "cnst"
                elif sArgType == "dvar" and arg.dvar != None:
                    # Get the *FIRST* construction variable under the dvar
                    sType = arg.dvar.get_outputtype()

        
        # Return what we found
        return sType

    def get_target(self):
        """Figure out what the url-name is to edit me"""

        if self.root != None and self.root.id > 0 and self.root.function:
            # We are part of a construction variable
            if self.id == self.root.function.id:
                # We are the top field
                return "43"
            else:
                return "44"
        elif self.rootcond != None and self.rootcond.id > 0 and self.rootcond.function:
            # We are part of a condition
            if self.id == self.rootcond.function.id:
                return "62"
            else:
                return "63"
        elif self.rootfeat != None and self.rootfeat.id > 0 and self.rootfeat.function:
            # We are part of a feature
            if self.id == self.rootfeat.function.id:
                return "72"
            else:
                return "73"
        else:
            # This should not happen
            return ""

    def get_func_target(self):
        """Figure out what the url-name is to edit me"""

        # This should not happen
        return "8"

    def get_targetid(self, sTarget = None):
        if sTarget == None:
            sTarget = self.get_target()
        if sTarget == "":
            return ""
        else:
            return "research_part_{}".format(sTarget)

    def get_url_edit(self):
        """Get the URL to edit me"""

        target = self.get_target()
        targetid = self.get_targetid(target)
        if target == "43" and self.root:
            instanceid = self.root.id
        elif target == "62" and self.rootcond:
            instanceid = self.rootcond.id
        elif target == "72" and self.rootfeat:
            instanceid = self.rootfeat.id
        elif self.parent:
            instanceid = self.parent.id
        else:
            return ""
        sUrl = reverse(targetid, kwargs={"object_id": instanceid})
        return sUrl

    def get_func_url_edit(self):
        """Get the URL to edit me"""

        targetid = self.get_targetid(self.get_func_target())
        instanceid = self.id
        if instanceid == None:
            sUrl = ""
        else:
            sUrl = reverse(targetid, kwargs={"object_id": instanceid})
        return sUrl
  
          
class ArgumentDef(models.Model):
    """Definition of one argument for a function"""

    # [1] The descriptive name of this argument
    name = models.CharField("Descriptive name", max_length=MAX_TEXT_LEN)
    # [1] The text to precede this argument within the specification element
    text = models.CharField("Preceding text", blank=True, max_length=MAX_TEXT_LEN)
    # [1] The numerical order of this argument
    order = models.IntegerField("Order", blank=False, default=0)
    # [1] The value can be of type: fixed, global variable, construction variable, function-output
    argtype = models.CharField("Default variable type", choices=build_abbr_list(SEARCH_ARGTYPE), 
                              max_length=5, help_text=get_help(SEARCH_ARGTYPE))
    # [0-1] If specified, the argument MUST have this type
    obltype = models.CharField("Type", choices=build_abbr_list(SEARCH_TYPE), 
                              max_length=5, help_text=get_help(SEARCH_TYPE), 
                              blank=True, null=True)
    # [1] Boolean that says whether this argument should be equal to the [outputtype] of this function
    hasoutputtype = models.BooleanField("Equals outputtype", default=False)
    # [1] The value that is the outcome of this function: 
    #     This is a JSON list, it can contain any number of bool, int, string
    argval = models.TextField("(Default value)", blank=True, default="[]")
    # Each function may take a number of input arguments
    function = models.ForeignKey(FunctionDef, null=False, on_delete=models.CASCADE, related_name = "arguments")

    def __str__(self):
        return "argdef_{}".format(self.id)


class Argument(models.Model):
    """The realization of an argument, based on its definition"""

    # [1] Must point to a definition
    argumentdef = models.ForeignKey(ArgumentDef, null=False, on_delete=models.CASCADE, related_name="argumentdef_arguments" )
    # [1] The value can be of type: fixed, global variable, construction variable, function-output
    argtype = models.CharField("Variable type", choices=build_abbr_list(SEARCH_ARGTYPE), 
                              max_length=5, help_text=get_help(SEARCH_ARGTYPE))
    # [1] In the end, the value is calculated and appears here
    argval = models.TextField("JSON value", blank=True, default="[]")
    # [0-1] This argument may link to a Global Variable
    gvar = models.ForeignKey("GlobalVariable", null=True, on_delete=models.SET_NULL, related_name="gvar_arguments")
    # [0-1] This argument may link to a Construction Variable
    cvar = models.ForeignKey("ConstructionVariable", null=True, on_delete=models.SET_NULL, related_name="cvar_arguments")
    # [0-1] This argument may link to a Data-dependant Variable
    dvar = models.ForeignKey("VarDef", null=True, on_delete=models.SET_NULL, related_name="dvar_arguments")
    # [0-1] This argument is any of the three relation types (axis, const, cond)
    raxis = models.ForeignKey("Relation", null=True, limit_choices_to={'type': 'axis' }, on_delete=models.SET_NULL, related_name='arg_raxis')
    rcond = models.ForeignKey("Relation", null=True, limit_choices_to={'type': 'cond' }, on_delete=models.SET_NULL, related_name='arg_rcond')
    rconst = models.ForeignKey("Relation", null=True, limit_choices_to={'type': 'const' }, on_delete=models.SET_NULL, related_name='arg_rconst')
    # [0-1] This argument may link to a Function (not its definition)
    function = models.ForeignKey("Function", null=True, related_name ="functionarguments", on_delete=models.SET_NULL)
    # [0-1] If a function is needed, we need to have a link to its definition
    # NOTE: this is the definition of the function having function.parent = ME
    #       get it by ME.functionparent.all().first().functiondef
    functiondef = models.ForeignKey(FunctionDef, null=True, on_delete=models.SET_NULL, related_name="functiondef_arguments")

    def __str__(self):
        return "arg_{}".format(self.id)

    def get_function_child(self):
        """Get the function child pointing to me"""

        func = None
        if self.argtype == "func":
            func = self.functionparent.all().first()
        return func

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
        response = super(Argument, self).save(force_insert, force_update, using, update_fields)
        # Any change in the status of an argument results in the status of the function it belongs to changing
        if self.function:
            self.function.set_status('stale')
        # Return the save response
        return response

    def get_output(self):
        """Get or produce the JSON representing me"""

        oErr = ErrHandle()
        oCode = {"value": None}
        try:

            # Check if we need to recalculate
            if self.argval == "" or self.argval == "[]" or self.argtype == "fixed":
                # WE should recalculate
                # atype = self.get_argtype_display()
                oCode['type'] = self.argtype
                oCode['order'] = self.argumentdef.order
                oCode['name'] = self.argumentdef.name
                if self.argtype == "func":
                    # Take the id of the function pointing to me as basis
                    argfunction = self.functionparent.all().first()
                    func_id = "" if argfunction == None else argfunction.id
                    line_no = "(unknown)" if argfunction == None else argfunction.line
                    oCode['value'] = "$__line_{}".format(line_no)
                elif self.argtype == "fixed":
                    # Get the basic value
                    sValue = self.argval
                    # Make sure booleans are translated correctly
                    if sValue.lower() == "true" or sValue.lower() == "true()":
                        oCode['value'] = True
                    elif sValue.lower() == "false" or sValue.lower() == "false()":
                        oCode['value'] =  False
                    elif sValue.lower() == "last" or sValue.lower() == "last()":
                        oCode['value'] = "last"
                    elif re.match(integer_format, sValue):
                        # THis is an integer
                        # oCode['value'] = sValue
                        oCode['value'] = sValue if not is_integer(sValue) else int(sValue)
                    else:
                        # String value -- must be between quotes
                        # oCode['value'] = "'{}'".format(sValue.replace("'", "''"))
                        oCode['value'] = sValue
                elif self.argtype == "gvar":
                    if self.gvar != None:
                        oCode['value'] = "$_{}".format(self.gvar.name)
                elif self.argtype == "cnst":
                    # THis is not in use (yet)
                    oCode['value'] = "$CONSTITUENT"
                elif self.argtype == "hit":
                    oCode['value'] = "$search"
                elif self.argtype == "cvar":
                    # This is superceded, I think...
                    oCode['value'] =  "$CVAR"
                elif self.argtype == "dvar":
                    if self.dvar != None:
                        # Return the name of the variable
                        oCode['value'] =  "${}".format(self.dvar.name)
                elif self.argtype == "raxis":
                    if self.raxis != None:
                        # oCode['value'] = self.raxis.xpath
                        oCode['value'] = self.raxis.name
                elif self.argtype == "rcnst":
                    if self.rconst != None:
                        # oCode['value'] = self.rconst.xpath
                        oCode['value'] = self.rconst.name
                elif self.argtype == "rcond":
                    if self.rcond != None:
                        # oCode['value'] = self.rcond.xpath
                        oCode['value'] = self.rcond.name
                # Assign the code to me
                self.argval = json.dumps(oCode)
            return self.argval
        except:
            oCode['value'] = "error"
            oCode['msg'] = oErr.get_error_message()
            return oCode

    def get_argument_error(self):
        """Check and report an error in this argument"""

        sError = ""
        # Check the argument type
        sArgType = self.argtype
        if sArgType == None or sArgType == "" or sArgType == "-":
            sError = "No argument specified"
        elif sArgType == "cnst":
            # THis is not in use, so report error
            sError = "Argument is defined as constituent, but no constituent is specified (e.g. through dvar or search)"
        elif sArgType == "gvar" and (self.gvar == None or self.gvar == None):
            sError = "Argument should be a global variable, but it is not specified"
        elif sArgType == "cvar" and (self.cvar == None or self.cvar == None):
            sError = "Argument should be a data-dependant variable, but it is not specified"
        elif sArgType == "raxis" and (self.raxis == None ):
            sError = "Argument should be a relation axis, but it is not specified"
        elif sArgType == "rcnst" and (self.rconst == None ):
            sError = "Argument should be a relation constituent, but it is not specified"
        elif sArgType == "rcond" and (self.rcond == None ):
            sError = "Argument should be a relation condition, but it is not specified"
        elif sArgType == "dvar" and (self.dvar == None or self.dvar == None):
            sError = "Argument should be a data-dependant  variable, but it is not specified"
        return sError

    def get_code(self, format, method="recursive"):
        """Create and return the required Xquery for this argument"""

        oErr = ErrHandle()
        try:
            """Provide a viewable representation of this particular argument"""
            atype = self.get_argtype_display()
            sCode = ""
            if self.argtype == "func":
                # Get the function that has me as its parent (just one!!)
                argfunction = self.functionparent.all().first()
                if argfunction == None:
                    sCode = ""
                elif method == "recursive":
                    # Get the format-dependant Xquery for this function
                    oCode = argfunction.get_code(format)
                    sCode = oCode['code']
                else:
                    # The code: use the line where the function is defined
                    sCode = "$__line{}".format(argfunction.get_line())
            elif self.argtype == "fixed":
                # Get the basic value
                sValue = self.argval
                # Make sure booleans are translated correctly
                if sValue.lower() == "true" or sValue.lower() == "true()":
                    sCode = "true()"
                elif sValue.lower() == "false" or sValue.lower() == "false()":
                    sCode = "false()"
                elif sValue.lower() == "last" or sValue.lower() == "last()":
                    sCode = "last()"
                elif re.match(integer_format, sValue):
                    # THis is an integer
                    sCode = sValue
                else:
                    # String value -- must be between quotes
                    sCode = "'{}'".format(sValue.replace("'", "''"))
            elif self.argtype == "gvar":
                if self.gvar != None:
                    sCode = "$_{}".format(self.gvar.name)
            elif self.argtype == "cnst":
                # THis is not in use (yet)
                sCode = "$CONSTITUENT"
            elif self.argtype == "hit":
                sCode = "$search"
            elif self.argtype == "cvar":
                # This is superceded, I think...
                sCode = "$CVAR"
            elif self.argtype == "dvar":
                if self.dvar != None:
                    # Return the name of the variable
                    sCode = "${}".format(self.dvar.name)
            elif self.argtype == "raxis":
                if self.raxis != None:
                    sCode = self.raxis.xpath
            elif self.argtype =="rcnst":
                if self.rconst != None:
                    sXpath = self.rconst.xpath
                    if "$cns$" in sXpath:
                        sTag = "su" if format == "folia" else "eTree"
                        sXpath = sXpath.replace("$cns$", sTag)
                    if "$wrd$" in sXpath:
                        sTag = "wref" if format == "folia" else "eLeaf"
                        sXpath = sXpath.replace("$wrd$", sTag)
                    sCode = sXpath
            elif self.argtype == "rcond":
                if self.rcond != None:
                    sXpath = self.rcond.xpath

            return sCode
        except:
            oErr.DoError("Argument/get_code error")
            return "$ERROR_ARG_{}".format(self.id)

    def get_copy(self, **kwargs):
        # Possibly adapt gvar
        gvar = self.gvar
        if gvar != None and kwargs != None and 'gvar_list' in kwargs:
            # REtrieve the correct gvar from the list
            variable_src = gvar
            gvar = next(x['dst'] for x in kwargs['gvar_list'] if x['src'] == variable_src)
        # Possibly adapt dvar
        dvar = self.dvar
        if dvar != None and kwargs != None and 'dvar_list' in kwargs:
            # REtrieve the correct dvar from the list
            variable_src = dvar
            dvar = next(x['dst'] for x in kwargs['dvar_list'] if x['src'] == variable_src)
        if self.cvar != None:
            iStop = True
            # Don't know how to copy the proper CVAR yet

        # Make a clean copy
        new_copy = Argument(argumentdef=self.argumentdef,
                            argtype=self.argtype,
                            argval=self.argval,
                            functiondef=self.functiondef,
                            gvar=gvar,
                            cvar=self.cvar,
                            dvar=dvar,
                            raxis=self.raxis,
                            rcond=self.rcond,
                            rconst=self.rconst)
        # Initial saving
        new_copy.save()
        # Check if we have a new function parent
        if 'function' in kwargs:
            new_copy.function = kwargs['function']
        # Skip FK fields: argumentdef, functiondef
        # TODO: how to properly process: gvar, cvar??
        # Copy a potential function pointing to me
        kwargs['parent'] = new_copy
        copy_m2m(self, new_copy, "functionparent", **kwargs)    # Function

        # Save the new copy
        new_copy.save()
        # Return the new copy
        return new_copy

    def delete(self, using = None, keep_parents = False):
      # Check if there are any functions pointing to me
      func_child = self.functionparent.first()
      if func_child != None:
          func_child.delete()
      # Now delete myself
      result = super(Argument, self).delete(using, keep_parents)
      # Return the result
      return result

    def get_info(self):
        """Provide information on this particular argument"""
        atype = self.get_argtype_display()
        avalue = ""
        if self.argtype == "func":
            avalue = self.function.functiondef.name
        elif self.argtype == "fixed":
            avalue = self.argval
        elif self.argtype == "gvar":
            avalue = "G["+self.gvar.name+"]"
        elif self.argtype == "cnst":
            avalue = "CONSTITUENT"
        elif self.argtype == "hit":
            avalue = "Search hit"
        elif self.argtype == "cvar":
            avalue = "CVAR"
        elif self.argtype == "dvar":
            # Just the name DVAR?
            avalue = "DVAR"
            # Return the name of the variable
            avalue = self.dvar.name
        elif self.argtype == "raxis":
            avalue = self.raxis.name
        elif self.argtype == "rcnst":
            avalue = self.rconst.name
        elif self.argtype == "rcond":
            avalue = self.rcond.name
        return "{}: {}".format(atype, avalue)

    def get_view(self):
        """Provide a viewable representation of this particular argument"""
        atype = self.get_argtype_display()
        avalue = ""
        if self.argtype == "func":
            argfunction = self.functionparent.all().first()
            if argfunction == None:
                line = 0
            else:
                # level = argfunction.get_level()
                line = argfunction.get_line()
            # avalue = "f:{}[{}]".format(argfunction.functiondef.name, line)
            avalue = "line_{}".format(line)
        elif self.argtype == "fixed":
            avalue = "'{}'".format(self.argval)
        elif self.argtype == "gvar":
            if self.gvar != None:
                avalue = "$_{}".format(self.gvar.name)
        elif self.argtype == "cnst":
            avalue = "CONSTITUENT"
        elif self.argtype == "hit":
            avalue = "$search"
        elif self.argtype == "cvar":
            avalue = "CVAR"
        elif self.argtype == "dvar":
            if self.dvar != None:
                # Return the name of the variable
                avalue = "${}".format(self.dvar.name)
        elif self.argtype == "raxis":
            if self.raxis != None:
                avalue = "x:{}".format(self.raxis.name)
        elif self.argtype == "rcnst":
            if self.rconst != None:
                avalue = "rc:{}".format(self.rconst.name)
        elif self.argtype == "rcond":
            if self.rcond != None:
                avalue = "rb:{}".format(self.rcond.name)
        return avalue

    def get_title(self):
        """Provide a viewable representation of this particular argument's definition"""
        atype = self.get_argtype_display()
        avalue = ""
        if self.argtype == "func":
            avalue = ""
        elif self.argtype == "fixed":
            avalue = ""
        elif self.argtype == "gvar":
            if self.gvar != None:
                avalue = "{}".format(self.gvar.value)
        elif self.argtype == "cnst":
            avalue = ""
        elif self.argtype == "hit":
            avalue = "word that is found"
        elif self.argtype == "cvar":
            avalue = ""
        elif self.argtype == "dvar":
            if self.dvar != None:
                # Return the name of the variable
                avalue = ""
        elif self.argtype == "raxis":
            if self.raxis != None:
                avalue = ""
        elif self.argtype == "rcnst":
            if self.rconst != None:
                avalue = ""
        elif self.argtype == "rcond":
            if self.rcond != None:
                avalue = ""
        return avalue

    def get_outputtype(self):
        """Return the output type of this argument"""

        if self.argtype == "cnst":
            # This is not in use (yet)
            return ""
        elif self.argtype == "cvar":
            # Don't think this should work
            return ""
        elif self.argtype == "dvar":
            if self.dvar == None:
                return "arg.dvar.none"
            else:
                return self.dvar.get_outputtype()
        elif self.argtype == "fixed":
            # Look at the string value of [argval]
            if is_integer(self.argval):
                sType = "int"
            elif is_boolean(self.argval):
                sType = "bool"
            else:
                sType = "str"
            return sType
        elif self.argtype == "func":
            p = self.functionparent.first()
            return "" if p == None else p.get_outputtype()
        elif self.argtype == "gvar":
            if self.gvar == None:
                return "arg.gvar.none"
            else:
                return self.gvar.get_outputtype()
        elif self.argtype == "hit":
            return "cnst"
        elif self.argtype == "raxis":
            return "raxis"
        elif self.argtype == "rcnst":
            return "cnst"
        elif self.argtype == "rcond":
            return "rcond"
        else:
            return ""
    

class Relation(models.Model):
    """Simple relation like preceding and following"""

    # [1] The descriptive name of this argument
    name = models.CharField("Name", max_length=MAX_TEXT_LEN)
    # [1] Relation type: 'axis', 'constituent', 'condition'
    type = models.CharField("Relation type", choices=build_abbr_list(SEARCH_RELATION_TYPE), 
                              max_length=5, help_text=get_help(SEARCH_RELATION_TYPE), default='axis')
    # [1] Xpath implementation
    xpath = models.TextField("Implementation", null=False, blank=False, default=".")

    def __str__(self):
        return "{}".format(self.name)

    def get_subset(sType):
        return Relation.objects.filter(type=sType).order_by('name')

    def get_choices(sType):
        qs = Relation.objects.filter(type=sType).order_by('name')
        choices = [(item.id, item.name) for item in qs]
        return choices
    

class ConstructionVariable(models.Model):
    """Each construction may provide its own value to the variables belonging to the gateway"""

    # [1] Link to the Construction the variable value belongs to
    construction = models.ForeignKey(Construction, blank=False, null=False, on_delete=models.CASCADE, related_name="constructionvariables")
    # [1] Link to the name of this variable
    variable = models.ForeignKey(VarDef,  blank=False, null=False, on_delete=models.CASCADE, related_name="variablenames")
    # [1] Type of value: string or expression
    type = models.CharField("Variable type", choices=build_abbr_list(SEARCH_VARIABLE_TYPE), 
                              max_length=5, help_text=get_help(SEARCH_VARIABLE_TYPE))
    # [1] String value of the variable for this combination of Gateway/Construction
    svalue = models.TextField("Value", blank=True)
    # [0-1] This variable may be determined by a Global Variable
    gvar = models.ForeignKey("GlobalVariable", null=True, on_delete=models.SET_NULL, related_name="gvar_cvars")
    # [0-1] This variable may be determined by a Function
    function = models.OneToOneField(Function, null=True, on_delete=models.SET_NULL, related_name="function_cvars")
    # [0-1] If a function is supplied, then here's the place to define the function def to be used
    functiondef = models.ForeignKey(FunctionDef, null=True, on_delete=models.SET_NULL, related_name="functiondef_cvars")
    # [1] Text-json to indicate the status of this 
    status = models.TextField("Status", default="{}")

    def __str__(self):
        sConstruction = self.construction.name
        sVariable = self.variable.name
        return "[{}|{}]".format(sConstruction, sVariable)

    def argcheck(self):
        """Check the argument-compatibility of this function"""

        # Assume the best
        oStatus = {'status': "ok", 'msg': ''}
        # Check if status needs to be calculated
        self.refresh_from_db()
        myStatus = json.loads(self.status)
        if not 'status' in myStatus or myStatus['status'] != "ok":
            # first check if we have a function or not
            if self.type == "func":
                func_this = self.function
                if func_this != None:
                    # Get all functions that have this cvar as root
                    function_list = Function.objects.filter(root=self)
                    # Assume all is well
                    bArgCheck = True
                    for func in function_list:
                        # Check this function
                        oCheck = func_this.argcheck()
                        if oCheck['status'] != "ok":
                            # Copy the status and the message
                            oStatus['status'] = "error"
                            oStatus['msg'] = "Search construction {}, variable {}: {}".format(
                                self.construction.name, self.variable.name, oCheck['msg'])
                            oStatus['type'] = 'cvar'
                            oStatus['id'] = self.id
                            # Do not look any further
                            bArgCheck = False
                            break
                    # Make sure the status gets stored
                    self.status = json.dumps(oStatus)
                    self.save()

        return oStatus

    def set_status(self, sStatus):
        """Set the status to the one indicated in [sStatus]"""

        myStatus = json.loads(self.status)
        myStatus['status'] = sStatus
        self.status = json.dumps(myStatus)
        self.save()

    def get_json(self):
        """Get the output of this feature in JSON form"""

        oCode = {"type": self.type, "value": None}
        oErr = ErrHandle()
        try:
            # Action depends on feattype
            if self.type == "gvar":
                if self.gvar != None:
                    # Note: we pass on the name WITH the $_ prefix that is normally used for global variables
                    oCode['value'] = "$_{}".format(self.gvar.name)
            elif self.type == "fixed":
                    sValue = self.svalue
                    # Make sure booleans are translated correctly
                    if sValue.lower() == "true" or sValue.lower() == "true()":
                        oCode['value'] =  True
                    elif sValue.lower() == "false" or sValue.lower() == "false()":
                        oCode['value'] =  False
                    elif re.match(integer_format, sValue):
                        # THis is an integer
                        # oCode['value'] =  sValue
                        # oCode['value'] =  int(sValue)
                        oCode['value'] = sValue if not is_integer(sValue) else int(sValue)
                    else:
                        # String value -- must be between quotes
                        # oCode['value'] =  "'{}'".format(sValue.replace("'", "''"))
                        oCode['value'] =  sValue
            elif self.type == "calc":
                if self.function != None:
                    # Get the code for this function
                    lFunc = []
                    for func in self.get_functions():
                        #oFunc = json.loads(func.get_output())
                        #lFunc.append(oFunc)

                        oFunc = func.get_output()
                        if 'value' in oFunc and oFunc['value'] != "error" and oFunc['value'] != None:
                            # Return the code of this argument
                            lFunc.append(oFunc['value'])
                        else:
                            lFunc.append(None)

                    oCode['value'] = lFunc
            return oCode
        except:
            sMsg = oErr.get_error_message()
            oCode['value'] = "error"
            oCode['msg'] = sMsg
            return oCode

    def get_copy(self, **kwargs):
        # Make a clean copy of the CVAR, but don't save it yet
        new_copy = get_instance_copy(self, commit=False)
        # Set the construction and the variable correctly
        new_copy.construction = kwargs['construction']
        new_copy.variable = kwargs['variable']
        # Copy the function associated with the current CVAR
        if self.function != None:
            function = self.function.get_copy(**kwargs)
            # Set the function 
            new_copy.function = function
        # Only now save it
        try:
            new_copy.save()
        except:
            sMsg = sys.exc_info()[0]
        # FK fields: do NOT copy 'construction', 'vardef', 'functiondef'
        # Get a pointer to the 'gateway' of the new copy
        gateway = new_copy.variable.gateway
        # Prepare an object for further processing
        kwargs = {'lst_m2m': ["constructionvariables"],
                  'cvar_list': ConstructionVariable.objects.filter(construction=new_copy.construction, construction__gateway=gateway),
                  'gvar_list': GlobalVariable.objects.filter(gateway=gateway)}
        # Return the new copy
        return new_copy

    def get_code(self, format, method):
        """Provide Xquery 'main' and 'def' code for this cns var"""

        oErr = ErrHandle()
        oBack = {'main': "", 'def': "", 'dvars': [], 'dvarnum': 0}
        sDef = ""
        sMain = ""
        try:
            if self.type == "gvar":
                if self.gvar == None:
                    # This is not good. The CVAR points to a gvar that does not exist
                    self.construction.gateway.error_add("The data-dependant variable {} for search element {} is not defined correctly (gvar)".format(
                      self.variable.name, self.construction.name))
                    return ERROR_CODE
                else:
                    sMain = "$_{}".format(self.gvar.name)
            elif self.type == "fixed":
                sValue = self.svalue
                # Make sure booleans are translated correctly
                if sValue.lower() == "true" or sValue.lower() == "true()":
                    sMain = "true()"
                elif sValue.lower() == "false" or sValue.lower() == "false()":
                    sMain = "false()"
                elif re.match(integer_format, sValue):
                    # THis is an integer
                    sMain = sValue
                else:
                    # String value -- must be between quotes
                    sMain = "'{}'".format(sValue.replace("'", "''"))
            elif self.type == "calc":
                # Find out which definition variables are available for me
                lstQ = []
                lstQ.append(Q(gateway=self.construction.gateway))
                lstQ.append(Q(order__lt=self.variable.order))
                qs = VarDef.objects.filter(*lstQ).order_by('order')
                oBack['dvars'] = ", ".join( ["$" + item.name for item in qs])
                oBack['dvarnum'] = qs.count()
                # Check if a function has been defined
                if self.function == None:
                    # This is not good: no function specified
                    self.construction.gateway.error_add("The data-dependant variable {} for search element {} is not defined correctly (function)".format(
                      self.variable.name, self.construction.name))
                    return ERROR_CODE
                elif method == "recursive":
                    oMain = self.function.get_code(format, method)
                    sMain = oMain['code']
                    if 'error' in oMain:
                        oBack['error'] = oMain['error']
                else:
                    # Method is plain: get the code for all the functions with me as 'root'
                    func_list = [item.get_code(format, method) 
                                 for item in Function.objects.filter(root=self).order_by('id') ]
                    sMain = func_list
                    # sMain = self.function.get_code(format, method)
                    # Append the code for the definition
                    sDef = self.function.get_codedef(format)
                    oBack['def'] = sDef
            else:
                sMain = "concat('{}', '{}')".format(self.type, format)
            # Store code and definition
            oBack['main'] = sMain
            return oBack
        except:
            oErr.DoError("cvar/get_code error")
            oBack['error'] = "cvar/get_code error" 
            return oBack

    def delete(self, using = None, keep_parents = False):
        """Delete a CVAR"""

        # Delete all that is pointing to me
        # Check if this CVAR can be deleted
        qs = Argument.objects.filter(cvar=self)
        for arg_inst in qs:
            # Delete this argument
            arg_inst.delete()
        # Delete the function(s) pointing to me
        if self.function != None:
            self.function.delete()
        # Now delete myself
        return super(ConstructionVariable, self).delete(using, keep_parents)

    def get_functions(self):
        """Get all the functions belonging to this construction variable"""

        func_list = []
        # Only works for the correct type
        if self.type == "calc":

            # Get all the functions pointing to me
            func_list = Function.objects.filter(root=self).order_by('line')

        return func_list

    def get_outputtype(self):
        """Calculate the output type of a function"""

        # Initial guess: unknown
        sType = "-"
        if self.type != None:
            # Action depends on which type we have
            if self.type == "fixed":
                # Look at the string value of [svalue]
                if is_integer(self.svalue):
                    sType = "int"
                elif is_boolean(self.svalue):
                    sType = "bool"
                else:
                    sType = "str"
            elif self.type == "calc" and self.function != None:
                # Take over the value from the function attached to me
                sType = self.function.get_outputtype()
            elif self.type == "gvar" and self.gvar != None:
                sType = self.gvar.get_outputtype()
        # Return the type we found
        return sType
    
    
class Condition(models.Model):
    """Each research project may contain any number of conditions defining a search hit"""

    # [1] Condition name
    name = models.CharField("Name", max_length=MAX_TEXT_LEN)
    # [0-1] Description of the condition
    description = models.TextField("Description", blank=True)
    # [1] A condition is a boolean, and can be of two types: Function or Dvar
    condtype = models.CharField("Condition type", choices=build_abbr_list(SEARCH_CONDTYPE), 
                              max_length=5, help_text=get_help(SEARCH_CONDTYPE))
    # [0-1] One option for a condition is to be equal to the value of a data-dependant variable
    variable = models.ForeignKey(VarDef, null=True, on_delete=models.SET_NULL, related_name ="variablecondition")
    # [1] The numerical order of this argument
    order = models.IntegerField("Order", blank=False, default=0)

    # [0-1] Another option for a condition is to be defined in a function
    function = models.OneToOneField(Function, null=True, on_delete=models.SET_NULL)
    # [0-1] If a function is needed, we need to have a link to its definition
    functiondef = models.ForeignKey(FunctionDef, null=True, on_delete=models.SET_NULL, related_name ="functiondefcondition")

    # [0-1] Include this condition in the search or not?
    include = models.CharField("Include", choices=build_abbr_list(SEARCH_INCLUDE), 
                              max_length=5, help_text=get_help(SEARCH_INCLUDE), default="true")

    # [1] Text-json to indicate the status of this 
    status = models.TextField("Status", default="{}")
    # [1] Every gateway has zero or more conditions it may look for
    gateway = models.ForeignKey(Gateway, blank=False, null=False, on_delete=models.CASCADE, related_name="conditions")

    def __str__(self):
        return self.name

    def argcheck(self):
        """Check the argument-compatibility of this function"""

        # Assume the best
        oStatus = {'status': "ok", 'msg': ''}
        # Check if status needs to be calculated
        self.refresh_from_db()
        myStatus = json.loads(self.status)
        if not 'status' in myStatus or myStatus['status'] != "ok":
            # Reset the previous status
            self.status = "{}"
            # first check if we have a function or not
            if self.condtype == "func":
                func_this = self.function
                if func_this != None:
                    # Get all functions that have this condition as root
                    function_list = Function.objects.filter(rootcond=self)
                    # Assume all is well
                    bArgCheck = True
                    for func in function_list:
                        # Check this function
                        oCheck = func_this.argcheck()
                        if oCheck['status'] != "ok":
                            # Copy the status and the message
                            oStatus['status'] = "error"
                            oStatus['msg'] = "Feature {}: {}".format(
                                self.name, oCheck['msg'])
                            oStatus['type'] = 'cond'
                            oStatus['id'] = self.id
                            # Do not look any further
                            bArgCheck = False
                            break
                    # Make sure the status gets stored
                    self.status = json.dumps(oStatus)
                    self.save()

        return oStatus

    def set_status(self, sStatus):
        """Set the status to the one indicated in [sStatus]"""

        myStatus = json.loads(self.status)
        myStatus['status'] = sStatus
        self.status = json.dumps(myStatus)
        self.save()

    def get_json(self):
        """Get the output of this feature in JSON form"""

        oErr = ErrHandle()
        oCode = {"value": None}
        try:
            oCode["type"] = self.condtype
            oCode["description"] =  self.description
            oCode["order"] =  self.order
            oCode["include"] =  self.include
            # Action depends on feattype
            if self.condtype == "dvar":
                if self.variable != None:
                    oCode['value'] = "${}".format(self.variable.name)
            elif self.condtype == "func":
                if self.function != None:
                    # Get the code for this function
                    lFunc = []
                    for func in self.get_functions():
                        #oFunc = json.loads(func.get_output())
                        #lFunc.append(oFunc)

                        oFunc = func.get_output()
                        if 'value' in oFunc and oFunc['value'] != "error" and oFunc['value'] != None:
                            # Return the code of this argument
                            lFunc.append(oFunc['value'])
                        else:
                            lFunc.append(None)
                    oCode['value'] = lFunc
            return oCode
        except:
            oCode['value'] = "error"
            oCode['msg'] = oErr.get_error_message()
            return oCode

    def get_copy(self, **kwargs):
        """Make a copy of this condition"""

        # Test for the existence of 'gateway'
        if kwargs == None or 'gateway' not in kwargs:
            return None
        # If there is a function, copy it
        new_function = None
        if self.function != None:
            new_function = self.function.get_copy(**kwargs)
        # Look for correct dvar
        dvar = self.variable
        if dvar != None and kwargs != None and  'dvar_list' in kwargs:
             dvar = next(x['dst'] for x in kwargs['dvar_list'] if x['src'] == dvar)

        new_copy = Condition(name=self.name, description=self.description,
                             condtype=self.condtype, variable=dvar,
                             functiondef=self.functiondef, order=self.order,
                             include=self.include,
                             function=new_function, gateway=kwargs['gateway'])
        # Only now save it
        try:
            new_copy.save()
        except:
            sMsg = sys.exc_info()[0]
        # Return the new copy
        return new_copy

    def get_code(self, format, method):
        """Create and return the required Xquery for main and def"""

        oBack = {'main': "", 'def': "", 'dvars': []}
        sDef = ""
        sMain = ""
        if self.condtype == "dvar":
            if self.variable == None:
                # sMain = "$undefined_{}".format(self.name)
                sMain = ""
            else:
                # A variable has been defined
                sMain = "${}".format(self.variable.name)
        elif self.condtype == "func":
            if method == "recursive":
                # REturn the code of this function
                oMain = self.function.get_code(format, method)
                sMain = oMain['code']
                if 'error' in oMain:
                    oBack['error'] = oMain['error']
            else:
                # Method is plain: get the code for all the functions with me as 'root'
                func_list = [item.get_code(format, method) 
                              for item in Function.objects.filter(rootcond=self).order_by('id') ]
                sMain = func_list
                # sMain = self.function.get_code(format, method)
                # Append the code for the definition
                sDef = self.function.get_codedef(format)
                oBack['def'] = sDef
                # Find out which definition variables are available for me
                lstQ = []
                lstQ.append(Q(gateway=self.gateway))
                qs = VarDef.objects.filter(*lstQ).order_by('order')
                oBack['dvars'] = ["$" + item.name for item in qs]
        else:
            # This is something else
            sMain = "$UnknownCode"
        oBack['main'] = sMain
        return oBack
      
    def delete(self, using = None, keep_parents = False):
        """Delete all items pointing to me, then delete myself"""

        # Delete the function(s) pointing to me
        if self.function != None:
            self.function.delete()
        # NOTE: do not delete the functiondef, gateway or cvar -- those are independant of me
        # And then delete myself
        return super(Condition, self).delete(using, keep_parents)

    def get_functions(self):
        """Get all the functions belonging to this condition"""

        func_list = []
        # Only works for the correct type
        if self.condtype == "func":

            # Get all the functions pointing to me
            func_list = Function.objects.filter(rootcond=self).order_by('line')

        return func_list

    def get_outputtype(self):
        """Get the output type of myself"""

        sType = "-"
        if self.condtype:
            if self.condtype == "func" and self.function != None:
                sType = self.function.get_outputtype()
            elif self.condtype == "dvar" and self.variable != None:
                # Get the first cvar attached to this dvar
                sType = self.variable.get_outputtype()
        return sType


def get_function_main(function, format, cvar_until):
    """Get the function call in Xquery"""

    # Validate
    if function == None: return ""
    # Create correct function name
    sCode = "tb:function_{}({})".format(function.name, get_cvar_list(cvar_until))
    # REturn the code
    return sBasCodeck


class Feature(models.Model):
    """Each research project may contain any number of features calculated later on"""

    # [1] Feature name
    name = models.CharField("Name", max_length=MAX_TEXT_LEN)
    # [0-1] Description of the feature
    description = models.TextField("Description", blank=True)
    # [1] A condition is a boolean, and can be of two types: Function or Cvar
    feattype = models.CharField("Feature type", choices=build_abbr_list(SEARCH_FEATTYPE), 
                              max_length=5, help_text=get_help(SEARCH_FEATTYPE))
    # [0-1] One option for a condition is to be equal to the value of a data-dependant variable
    variable = models.ForeignKey(VarDef, null=True, on_delete=models.SET_NULL, related_name ="variablefeature")
    # [1] The numerical order of this argument
    order = models.IntegerField("Order", blank=False, default=0)

    # [0-1] Another option for a condition is to be defined in a function
    function = models.OneToOneField(Function, null=True, on_delete=models.SET_NULL)
    # [0-1] If a function is needed, we need to have a link to its definition
    functiondef = models.ForeignKey(FunctionDef, null=True, on_delete=models.SET_NULL, related_name ="functiondeffeature")

    # [0-1] Include this condition in the search or not?
    include = models.CharField("Include", choices=build_abbr_list(SEARCH_INCLUDE), 
                              max_length=5, help_text=get_help(SEARCH_INCLUDE), default="true")

    # [1] Boolean to indicate this feature has been checked
    status = models.TextField("Status", default="{}")
    # [1] Every gateway has zero or more output features
    gateway = models.ForeignKey(Gateway, blank=False, null=False, on_delete=models.CASCADE, related_name="features")

    def __str__(self):
        return self.name

    def argcheck(self):
        """Check the argument-compatibility of this function"""

        # Assume the best
        oStatus = {'status': "ok", 'msg': ''}
        oErr = ErrHandle()
        try:
            # Check if status needs to be calculated
            self.refresh_from_db()
            myStatus = json.loads(self.status)
            if not 'status' in myStatus or myStatus['status'] != "ok":
                # first check if we have a function or not
                if self.feattype == "func":
                    func_this = self.function
                    if func_this != None:
                        # Get all functions that have this feature as root
                        function_list = Function.objects.filter(rootfeat=self)
                        # Assume all is well
                        bArgCheck = True
                        for func in function_list:
                            # Check this function
                            oCheck = func_this.argcheck()
                            if oCheck['status'] != "ok":
                                # Copy the status and the message
                                oStatus['status'] = "error"
                                oStatus['msg'] = "Feature {}: {}".format(
                                    self.name, oCheck['msg'])
                                oStatus['type'] = 'feat'
                                oStatus['id'] = self.id
                                # Do not look any further
                                bArgCheck = False
                                break
                        # Make sure the status gets stored
                        self.status = json.dumps(oStatus)
                        self.save()

            return oStatus
        except:
            sMsg = oErr.get_error_message()
            oStatus['status'] = "error"
            oStatus['msg'] = sMsg
            return oStatus

    def set_status(self, sStatus):
        """Set the status to the one indicated in [sStatus]"""

        myStatus = json.loads(self.status)
        myStatus['status'] = sStatus
        self.status = json.dumps(myStatus)
        self.save()

    def get_json(self):
        """Get the output of this feature in JSON form"""

        oCode = {"value": None}
        oErr = ErrHandle()
        try:
            oCode['type'] = self.feattype
            oCode['order'] = self.order
            oCode['description'] = self.description
            oCode['include'] = self.include     # Use the INCLUDE value straight, *NOT* this: self.get_include_display()
            # Action depends on feattype
            if self.feattype == "dvar":
                if self.variable != None:
                    oCode['value'] = "${}".format(self.variable.name)
            elif self.feattype == "func":
                if self.function != None:
                    # Get the code for this function
                    lFunc = []
                    for func in self.get_functions():
                        #oFunc = json.loads(func.get_output())
                        #lFunc.append(oFunc)

                        oFunc = func.get_output()
                        if 'value' in oFunc and oFunc['value'] != "error" and oFunc['value'] != None:
                            # Return the code of this argument
                            lFunc.append(oFunc['value'])
                        else:
                            lFunc.append(None)

                    oCode['value'] = lFunc
            return oCode
        except:
            oCode['value'] = "error"
            oCode['msg'] = oErr.get_error_message()
            return oCode

    def get_copy(self, **kwargs):
        """Make a copy of this feature"""

        # Test for the existence of 'gateway'
        if kwargs == None or 'gateway' not in kwargs:
            return None
        # If there is a function, copy it
        new_function = None
        if self.function != None:
            new_function = self.function.get_copy(**kwargs)

        # Look for correct dvar
        dvar = self.variable
        if dvar != None and kwargs != None and  'dvar_list' in kwargs:
             dvar = next(x['dst'] for x in kwargs['dvar_list'] if x['src'] == dvar)

        new_copy = Feature(name=self.name, description=self.description,
                             feattype=self.feattype, variable=dvar,
                             functiondef=self.functiondef,
                             order=self.order,
                             function=new_function, gateway=kwargs['gateway'])
        # Only now save it
        try:
            new_copy.save()
        except:
            sMsg = sys.exc_info()[0]
        # Return the new copy
        return new_copy

    def get_code(self, format, method):
        """Create and return the required Xquery"""

        oBack = {'main': "", 'def': "", 'dvars': []}
        sDef = ""
        sMain = ""
        if self.feattype == "dvar":
            if self.variable == None:
                sMain = ""
            else:
                # A variable has been defined
                sMain = "${}".format(self.variable.name)
        elif self.feattype == "func":
            if method == "recursive":
                # REturn the code of this function
                oMain = self.function.get_code(format, method)
                sMain = oMain['code']
                if 'error' in oMain:
                    oBack['error'] = oMain['error']
            else:
                # Method is plain: get the code for all the functions with me as 'root'
                func_list = [item.get_code(format, method) 
                              for item in Function.objects.filter(rootfeat=self).order_by('id') ]
                sMain = func_list
                # sMain = self.function.get_code(format, method)
                # Append the code for the definition
                sDef = self.function.get_codedef(format)
                oBack['def'] = sDef
                # Find out which definition variables are available for me
                lstQ = []
                lstQ.append(Q(gateway=self.gateway))
                qs = VarDef.objects.filter(*lstQ).order_by('order')
                oBack['dvars'] = ["$" + item.name for item in qs]
        else:
            # This is something else
            sMain = "$UnknownCode"
        oBack['main'] = sMain
        return oBack
      
    def delete(self, using = None, keep_parents = False):
        """Delete all items pointing to me, then delete myself"""

        # Delete the function(s) pointing to me
        if self.function != None:
            self.function.delete()
        # NOTE: do not delete the functiondef, gateway or cvar -- those are independant of me
        # And then delete myself
        return super(Feature, self).delete(using, keep_parents)

    def get_functions(self):
        """Get all the functions belonging to this condition"""

        func_list = []
        # Only works for the correct type
        if self.feattype == "func":

            # Get all the functions pointing to me
            func_list = Function.objects.filter(rootfeat=self).order_by('line')

        return func_list

    def get_outputtype(self):
        """Get the output type of myself"""

        sType = "-"
        if self.feattype:
            if self.feattype == "func" and self.function != None:
                sType = self.function.get_outputtype()
            elif self.feattype == "dvar" and self.variable != None:
                # Get the first cvar attached to this dvar
                sType = self.variable.get_outputtype()
        return sType

      
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
    # [1] Every ConstructionVariable instance can have one or more search items
    construction = models.ForeignKey(Construction, blank=False, null=False, on_delete=models.CASCADE, related_name="searchitems")

    def __str__(self):
        return self.name


class ResGroup(models.Model):
    """A group can consist of a number of Research projects"""

    # [1] Name of the group of research projects this belongs to
    name = models.CharField("Research project group", max_length=MAX_TEXT_LEN)
    # [1] Description of this group
    description = models.TextField("Description", default="-")
    # [1] Each research group has its owner: obligatory, but not to be selected by the user himself
    owner = models.ForeignKey(User, editable=False, on_delete=models.CASCADE, related_name="owner_resgroups")
    # [0-1] Each group may be part of another group
    parent = models.ForeignKey("ResGroup", null=True, blank=True, on_delete=models.SET_NULL, related_name="parentgroup")

    def __str__(self):
        return self.name

    def group_depth(self):
        """Get the amount of parents above me"""

        depth = 0
        item = self
        while item != None:
            depth += 1
            item = item.parent
        # Return the depth we found
        return depth
    

class Research(models.Model):
    """Main entry for a research project"""

    # [1] Name of the CRP from which the results come (does not necessarily have to be here)
    name = models.CharField("Research project name", max_length=MAX_TEXT_LEN)
    # [1] Purpose of this research
    purpose = models.TextField("Purpose")
    # [1] The main type of this research: is it word oriented or constituent oriented?
    targetType = models.CharField("Main element type", choices=TARGET_TYPE_CHOICES, max_length=5)
    # [1] The search type: simple, plain, ...
    stype = models.CharField("Search type", choices=STYPE_CHOICES, max_length=5, default="p")
    # [0-1] A stringified JSON representation of the search, if it is simple
    compact = models.TextField("Compressed specification", null=True, blank=True)
    # [1] Each research project has a 'gateway': a specification for the $search element
    gateway = models.OneToOneField(Gateway, blank=False, null=False, on_delete=models.CASCADE)
    # [1] Each research project has its owner: obligatory, but not to be selected by the user himself
    owner = models.ForeignKey(User, editable=False, on_delete=models.CASCADE, related_name="owner_researches")
    # [0-1] create date and lastsave date
    created = models.DateTimeField(default=timezone.now)
    saved = models.DateTimeField(null=True, blank=True)
    # [0-1] A research project can optionally belong to a group
    group = models.ForeignKey(ResGroup, null=True, blank=True, on_delete=models.SET_NULL, related_name="childresearch")

    def __str__(self):
        return self.name

    def group_parent(self):
        """Get the parent of the group I belong to """
        if self.group == None or self.group.parent == None:
            return None
        else:
            return self.group.parent.name

    def group_depth(self):
        """Get the amount of parents above me"""

        depth = 0
        item = self.group
        while item != None:
            depth += 1
            item = item.parent
        # Return the depth we found
        return depth

    def group_path(self):
        """Return the path above me"""

        path = ""
        oErr = ErrHandle()
        try:
            item = self.group
            while item != None:
                path = "/" + item.name + path
                item = item.parent
            ## Add the name itself to the path
            #path = path + "/" + self.name
            path = path.lower()
        except:
            msg = oErr.get_error_message()
            path = ""
        return path
    
    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
      # Adapt the save date
      # self.saved = datetime.now()
      self.saved = timezone.now()
      response = super(Research, self).save(force_insert, force_update, using, update_fields)
      return response

    def create_simple(oSearch, name, owner, overwrite=False):
        """Create a simple search based on the parameters in oSearch"""

        obj = None
        msg = ""
        try:
            if oSearch != None:
                # Compact it
                sSearch = json.dumps(oSearch)

                # Look for the correct research project
                qs = Research.objects.filter(owner=owner, name=name)
                if qs.count() > 0 and not overwrite:
                    # This name is already in use -- warn the user
                    obj=None
                    msg = "The project [{}] already exists. First delete it if you want to import this version.".format(name)
                else:
                    # Get the target type
                    targetType = oSearch['targetType']

                    if overwrite and qs.count() > 0:
                        # Retreive the correct object
                        obj = qs.first()
                        # Save the compact representation
                        obj.compact = sSearch
                        # Change the stype accordingly
                        obj.stype = STYPE_SIMPLE
                        # Adapt the object's parameters
                        obj.purpose = "Derived from simple search"
                        obj.targetType = targetType
                        
                    else:
                        # Create a new gateway
                        gateway = Gateway.objects.create()
                        gateway.name = "simple"
                        gateway.description = "simple search as described in research.compact"
                        gateway.save()
                        # Create a new project
                        obj = Research.objects.create(name=name, purpose="Derived from simple search", 
                                       targetType=targetType, gateway=gateway,
                                       stype=STYPE_SIMPLE, compact=sSearch,
                                       owner=owner)
                    # Save the Research project
                    obj.save()
        except:
            msg = errHandle.get_error_message()
            errHandle.DoError("Research/create_simple")
            obj=None

        # Return the object that has been created
        return obj, msg

    def gateway_name(self):
        return self.gateway.name

    def delete(self, using = None, keep_parents = False):
        try:
            # Delete all the sharegroup instances pointing to this research instance
            for grp in self.sharegroups.all():
                grp.delete()

            # Delete all Basket objects (=RESULTS) pointing to me
            for bsk in self.baskets.all():
                bsk.delete()
        except:
            sMsg = oErr.get_error_message()

        # Look for the gateway
        try:
            gateway = self.gateway
            gateway.delete()
        except:
            if self.gateway_id:
                gateway = Gateway.objects.filter(id=self.gateway_id)
                if gateway:
                    gateway.delete()
        
        # Delete myself
        try:
            response = super(Research, self).delete(using, keep_parents)
        except:
            sMsg = oErr.get_error_message()
            response = None
        return response

    def username(self):
        return self.owner.username

    def integrity(self):
        """Check the integrity of this project"""

        oBack = {'status': 'ok'}
        oErr = ErrHandle()
        try:
            # Integrity of the Features
            feat_list = []
            for feat in self.gateway.get_feature_list():
                if feat.include:
                    oFeat = feat.get_json()
                    fValue = oFeat['value'] 
                    if fValue == None or fValue == "error":
                        # This feature will cause trouble
                        oBack['status'] = "error"
                        oBack['msg'] = "Please review the specification of this feature: {}".format(feat.name)
                        return oBack
        except:
            # Prepare an error return object
            oBack['status'] = 'error'
            oBack['msg'] = oErr.get_error_message()

        # Return the integrity object (which should normally have status 'ok')
        return oBack

    def get_json(self):
        # Prepare a back object
        oBack = {}
        oErr = ErrHandle()
        try:
            # Get the basics
            oJson = dict(name=self.name, 
                         purpose=self.purpose, 
                         targetType=self.targetType, 
                         stype=self.stype,
                         owner=self.owner.username,
                         created= get_crpp_date(self.created),
                         saved=get_crpp_date(self.saved))
            if self.compact and self.compact != "":
                oJson['compact'] = json.loads(self.compact)
            # Get the gateway stuff
            oGateway = self.gateway.get_json()
            for key in oGateway:
                oJson[key] = oGateway[key]
            oBack['status'] = 'ok'
            oBack['json_data'] = json.dumps(oJson,indent=2).encode("utf-8")
            oBack['json_name'] = self.name
            # Add the
            return oBack
        except:
            oBack['status'] = 'error'
            oBack['msg'] = oErr.get_error_message()
            return oBack

    def read_data(username, data_file, arErr, oData = None, sName = None):
        """Import a JSON specification and create a new research object from it"""

        obj = None
        try:
            if oData == None:
                oData = import_data_file(data_file, arErr)
                # Turn the array of strings into a large string
                oData = json.loads("\n".join(oData))
            # Get the name of the new project
            if sName == None:
                sName = "{}_{}".format(oData['name'], oData['owner'])
            # Get a handle to the user
            owner = User.objects.filter(username=username).first()
            # Check if we can use this name or if it is already in use
            lstQ = []
            lstQ.append(Q(owner=owner))
            lstQ.append(Q(name=sName))
            qs = Research.objects.filter(owner=owner, name=sName)
            if qs.count() > 0:
                # This name is already in use -- warn the user
                obj=None
                arErr.append("The project [{}] already exists. First delete it if you want to import this version.".format(sName))
            else:
                # Create a new gateway
                gateway = Gateway.objects.create()
                gateway.save()
                # Get the targettype
                targetType = oData['targetType']
                # Get the stype
                stype = "p"
                if 'stype' in oData: stype = oData['stype']
                compact = None
                if 'compact' in oData: 
                    if isinstance(oData['compact'], str):
                        compact = oData['compact']
                    else:
                        compact = json.dumps(oData['compact'])

                # Create a new project
                obj = Research.objects.create(name=sName, purpose=oData['purpose'], 
                               targetType=targetType, gateway=gateway, stype=stype,
                               compact=compact, owner=owner)
                # Save the Research project
                obj.save()

                # Add constructions, dvars, gvars
                with transaction.atomic():
                    for cns in oData['constructions']:
                        # Create this construction and its associated SearchMain
                        search = SearchMain.create_item(cns['function'], cns['value'], cns['operator'])
                        if targetType == 'c':
                            search.exclude = cns['exclude']
                        elif targetType == 'e':
                            search.exclude = cns['exclude']
                            search.category = cns['category']
                            search.lemma = cns['lemma']
                            search.fcat = cns['fcat']
                            search.fval = cns['fval']
                        elif targetType == "q":
                            search.cql = cns['cql']
                        search.save()
                        construction = Construction(name=cns['name'], search=search, gateway=gateway)
                        construction.save()

                    for oGvar in oData['gvars']:
                        # Get the name without the $_ prefix if needed
                        varName = strip_varname(oGvar['name'])
                        gvar = GlobalVariable(name=varName, description=oGvar['description'],
                                              type=oGvar['type'], value=oGvar['value'], gateway=gateway)
                        gvar.save()

                    # NOTE: creating a VarDef also creates its accompanying CVAR (through Gateway.check_cvar() )
                    for oDvar in oData['dvars']:
                        dvar = VarDef(name=oDvar['name'], order=oDvar['order'],
                                      description=oDvar['description'],
                                      type=oDvar['type'], gateway=gateway)
                        dvar.save()
                # Now walk all the cvars and create them
                with transaction.atomic():
                    for oCvar in oData['cvars']:
                        # Get the correct construction and definitionvariable
                        construction = gateway.constructions.filter(name=oCvar['cons']).first()
                        dvar = gateway.definitionvariables.filter(name=oCvar['dvar']).first()
                        # Retrieve the CVAR
                        cvar = ConstructionVariable.objects.filter(construction=construction, variable=dvar).first()
                        cvar.type=oCvar['type']
                        ## Need to save it preliminarily
                        #cvar.save()
                        # Create possible function, if this is 'calc'
                        if oCvar['type'] == 'calc':
                            # Yes, create the functions
                            func_main = Function.create_from_list(oCvar['value'], gateway, "cvar", cvar, None, None)
                            func_main.save()
                            cvar.function = func_main
                            cvar.functiondef = func_main.functiondef
                        elif oCvar['type'] == 'fixed':
                            cvar.svalue = oCvar['value']
                        elif oCvar['type'] == 'gvar':
                            varName = strip_varname(oCvar['value'])
                            gvar = gateway.globalvariables.filter(name=varName).first()
                            cvar.gvar = gvar
                        cvar.save()
                # Now walk all the conditions and create them
                with transaction.atomic():
                    for oCond in oData["conditions"]:
                        # Create the condition
                        cond = Condition(name=oCond['name'], order=oCond['order'],
                                      description=oCond['description'], include=oCond['include'],
                                      condtype=oCond['type'], gateway=gateway)
                        cond.save()
                        # Create possible function, if this is 'calc'
                        if oCond['type'] == 'func':
                            # Yes, create the functions
                            func_main = Function.create_from_list(oCond['value'], gateway, "cond", None, cond, None)
                            func_main.save()
                            cond.function = func_main
                            cond.functiondef = func_main.functiondef
                        elif oCond['type'] == 'dvar':
                            varName = strip_varname(oCond['value'])
                            dvar = gateway.definitionvariables.filter(name=varName).first()
                            cond.variable = dvar
                        cond.save()
                # Now walk all the conditions and create them
                with transaction.atomic():
                    for oFeat in oData["features"]:
                        # Create the Feature
                        feat = Feature(name=oFeat['name'], order=oFeat['order'],
                                      description=oFeat['description'], include=oFeat['include'],
                                      feattype=oFeat['type'], gateway=gateway)
                        feat.save()
                        # Create possible function, if this is 'calc'
                        if oFeat['type'] == 'func':
                            # Yes, create the functions
                            func_main = Function.create_from_list(oFeat['value'], gateway, "feat", None, None, feat)
                            func_main.save()
                            feat.function = func_main
                            feat.functiondef = func_main.functiondef
                        elif oFeat['type'] == 'dvar':
                            varName = strip_varname(oFeat['value'])
                            dvar = gateway.definitionvariables.filter(name=varName).first()
                            feat.variable = dvar
                        feat.save()

        except:
            sError = errHandle.get_error_message()
            obj=None

        # Return the object that has been created
        return obj

    def get_copy(self, **kwargs):
        # Make a clean copy
        new_copy = get_instance_copy(self, commit=False)
        # Copy the FK contents
        copy_fk(self, new_copy, "gateway")
        # Adapt the name of the project to reflect that this is a copy
        lstQ = []
        # Make it user-independent...
        lstQ.append(Q(name=self.name))
        iCount = Research.objects.filter(*lstQ).count()
        new_copy.name = "{}_{}".format(self.name, iCount+1)
        # Make sure that "I", the current user, am the owner of this new copy
        if 'currentuser' in kwargs:
            new_copy.owner = kwargs['currentuser']
        # Now save it
        new_copy.save()
        # Note: the 'owner' needs no additional copying, since the user remains the same
        # Return the new copy
        return new_copy

    def get_copy_url(self):
        """Produce an URL to be called when requesting to copy [self]"""

        return reverse('seeker_copy', kwargs={'object_id': self.id})

    def get_downloadjson_url(self):
        """Produce an URL to be called when requesting to copy [self]"""

        return reverse('search_json', kwargs={'object_id': self.id})

    def get_delete_url(self):
        """Produce an URL to be called when requesting to delete [self]"""

        sUrl = reverse('seeker_delete', kwargs={'object_id': self.id})
        if sUrl == "":
            iStop = 1
        return sUrl

    def has_permission(self, usr, permission):
        """CHeck if this user has the indicated permission"""

        # Is this me?
        if usr == None:
            bMay = False
        else:
            bMay = (usr == self.owner)
            # Is this not me?
            if not bMay:
                # Visit all the sharegroups we share
                lstQ = []
                lstQ.append(Q(group__in=usr.groups.all()))
                lstQ.append(Q(permission__contains=permission))
                qs = self.sharegroups.filter(*lstQ)
                bMay = (qs.count() > 0)
        return bMay

    def get_status(self):
        """Get the execution status"""
        return ""

    def stop(self):
        """Reset project"""
        pass

    def to_xquery(self, partId, sFormat, bRefresh, basket):
        """Translate project into Xquery"""

        # Import the correct function
        from cesar.seeker.convert import ConvertProjectToXquery
        
        # Validate
        if partId == None or partId == "" or sFormat == None or sFormat == "":
            return None

        try:
            # Prepare data
            oData = {'targetType': self.targetType,
                     'format': sFormat,
                     'gateway': self.gateway}

            # Check if we have Xquery code and there is no 'error' status
            if bRefresh or basket.codedef == "" or basket.codeqry == "" or basket.get_status() == "error":
                # Create the Xquery code
                basket.set_status("convert_xq")
                basket.codedef, basket.codeqry, arErr = ConvertProjectToXquery(oData, basket)
                # Possibly add errors to gateway
                self.gateway.add_errors(arErr)
                # Check errors
                errors = self.gateway.get_errors()
                if errors != "" and errors != "[]":
                    # Also show errors here
                    errHandle.Status("Error in to_xquery: {}".format(errors))
                    return None
                # Save the basket
                basket.save()


            # Return the basket
            return basket
        except:
            self.gateway.error_add("Research/to_xquery error")
            sError = errHandle.get_error_message()
            if sError != "":
                self.gateway.error_add(sError)
            errHandle.DoError("Research/to_xquery error")
            return None

    def to_crpx(self, partId, sFormat, basket):
        """Send command to /crpp to start the project"""

        oErr = ErrHandle()
        # Import the correct function
        from cesar.seeker.convert import ConvertProjectToCrpx
        # Prepare reply
        oBack = {'status': 'ok', 'msg': ''}
        # Get the correct Basket
        try:
            # Clear the errors
            self.gateway.error_clear()

            # Check the status = the functions and arguments
            # BUT: skip if it is simplesearch?
            if self.stype != STYPE_SIMPLE and self.name != SIMPLENAME:
                oArgStatus = self.gateway.get_status()
                if oArgStatus != None and 'status' in oArgStatus and oArgStatus['status'] != "ok":
                    oBack['status'] = "error"
                    oBack['msg'] = oArgStatus['msg']
                    if 'type' in oArgStatus:
                        oBack['type'] = oArgStatus['type']
                    if 'id' in oArgStatus:
                        oBack['id'] = oArgStatus['id']
                    return oBack

            # Check the integrity of the search project
            oCheck = self.integrity()
            if oCheck['status'] != 'ok':
                oBack['msg'] = oCheck['msg']
                oBack['status'] = "error"
                return oBack

            # Create the Xquery
            bRefresh = True # Make sure that Xquery is calculated afresh
            basket = self.to_xquery(partId, sFormat, bRefresh, basket)

            # Check on what was returned
            if basket == None:
                if partId == None or partId == "":
                    sMsg = "First specify a corpus (or a part of a corpus) to search in"
                else:
                    sMsg = "to_crpx: Something is wrong. Cesar is unable to execute."
                    # sErrors = self.gateway.errors
                    sErrors = self.gateway.get_errors()
                    if sErrors != "" and sErrors != "[]":
                        lErrors = json.loads(sErrors)
                        lErrors.append(sMsg)
                        sMsg = "<br>\n".join(lErrors)
                        # Clear the errors
                        self.gateway.error_clear()
                oBack['msg'] = sMsg
                oBack['status'] = 'error'
                # Also show this error in the console
                oErr.Status("Error in to_crpx: {}".format(sMsg))
                return oBack
        except:
            msg_list = []
            msg_list.append("Failed to convert project to Xquery. Python error:")
            sErr = oErr.get_error_message()
            msg_list.append(sErr)
            oBack['msg_list'] = msg_list
            oBack['msg'] = " ".join(msg_list)
            oBack['status'] = 'error'
            # Also show this error in the console
            oErr.Status("Error in to_crpx: {}".format(" ".join(msg_list)))
            return oBack
        # Add basket to the return object, provided all went well
        oBack['basket'] = basket
        # Create CRPX project
        basket.set_status("create_crpx")
        try:
            sCrpxName, sCrpxText = ConvertProjectToCrpx(basket)
            oBack['crpx_text'] = sCrpxText
            oBack['crpx_name'] = sCrpxName
        except:
            oBack['msg'] = 'Failed to convert project to Crpx'
            oBack['status'] = 'error'
            return oBack

        # Check what is returned
        if sCrpxName == "":
            # An error has returned
            oBack['status'] = 'error'
            oBack['msg'] = "\n".join(sCrpxText)
            return oBack

        # Return what we have created
        return oBack

    def stop_execute(self, basket):
        """Stop execution"""

        oErr = ErrHandle()
        oBack = {'status': 'ok', 'msg': 'init stop'}
        try:
            basket.set_status("stopping...")
            # Get the userid
            sUser = self.owner.username
            # Get jobid
            jobid = basket.jobid
            # Adapt message
            basket.set_status('stopping job number {}'.format(jobid))
            # Try to stop it
            oCrpp = crpp_stop(sUser, jobid)      
            if oCrpp['commandstatus'] == 'ok':   
                oBack['status'] = "ok"
                oBack['msg'] = "Stopped search job gracefully"
                basket.set_status('stopped')
            else:
                oBack['status'] = 'error'
                oBack['msg'] = 'Could not perform execute at /crpp'
                basket.set_status('error')
        except:
            # Could not send this to the CRPX
            oBack['status'] = 'error'
            oBack['msg'] = oErr.DoError('Failed to stop the project properly')
        # Return what we have
        return oBack

    def execute(self, basket):
        """Send command to /crpp to start the project"""

        oErr = ErrHandle()
        # Get the part and the format from the basket
        partId = basket.part.id
        sFormat = basket.format

        # Get the execution options from the basket
        if basket.options == None or basket.options == "":
            oOptions = {}
        else:
            oOptions = json.loads(basket.options)

        # Convert the project
        basket.set_status("creating crpx")
        oBack = self.to_crpx(partId, sFormat, basket)

        # Al okay?
        if oBack['status'] == "error": 
            # Set the status of the basket to error
            basket.set_status('error')
            return oBack

        # GEt the basket
        # basket = oBack['basket']
        sCrpxText = oBack['crpx_text']
        sCrpxName = oBack['crpx_name']

        # Send the CRPX to /crpp and execute it
        try:
            # Get the userid
            sUser = self.owner.username
            # First send over the CRP code
            basket.set_status("send_crpx")
            oCrpp = crpp_send_crp(sUser, sCrpxText, sCrpxName)
            if oCrpp['commandstatus'] == 'ok':
                basket.set_status("asking crpp to start execution...")
                # Last information
                sLng = basket.part.corpus.get_lng_display()   # Language of the corpus
                sDir = basket.part.dir          # Directory where the part is located
                # Now start execution
                oCrpp = crpp_exe(sUser, sCrpxName, sLng, sDir, oOptions)      
                if oCrpp['commandstatus'] == 'ok':   
                    # Get the status object
                    oExeStatus = oCrpp['status']
                    # NOTE: the exeStatus may be a string or an object (hmmm)
                    if oExeStatus == "error":
                        # The server is complaining, it seems
                        msg_list = ['The server gives an error']
                        # oBack['msg'] = msg_part
                        if 'code' in oCrpp:
                            msg_list.append("Code: " + oCrpp['code'])
                        if 'message' in oCrpp:
                            msg_list.append("Message from the server:")
                            sMsg = oCrpp['message']
                            try:
                                if sMsg.startswith("{"):
                                    # Possibly do away with [] code
                                    idx = sMsg.find("[{\"msg\":")
                                    if idx >=0:
                                        sMsg = sMsg[:idx-1]
                                    # If this has multiple lines, then only take the first line
                                    lMulti = sMsg.split("\n")
                                    lMsg = []
                                    for oneMsg in lMulti:
                                        oMsg = json.loads(oneMsg)
                                        # This message may, in turn, contain a 'msg' part
                                        if 'msg' in oMsg and 'ex' in oMsg and 'cls' in oMsg and oMsg['msg'].startswith("{"):
                                            lMsg.append("class: {}".format(oMsg['cls']))
                                            if oMsg['ex'] != '':
                                                lMsg.append("ex: {}".format(oMsg['ex']))
                                            oInside = json.loads(oMsg['msg'])
                                            for key, value in oInside.items():
                                                lMsg.append("{}: {}<br>".format(key,value))
                                                msg_list.append("{}: {}".format(key,value))
                                        else:
                                            for key, value in oMsg.items():
                                                lMsg.append("{}: {}<br>".format(key,value))
                                                msg_list.append("{}: {}".format(key,value))
                                    # Combine all messages into a string
                                    sMsg = "\n".join(lMsg)
                                else:
                                    msg_list.append(sMsg)
                            except:
                                sEx = oErr.get_error_message()
                                sMsg = oCrpp['message']
                                msg_list.append(sMsg)
                        oBack['msg'] = "<br>".join(msg_list)
                        oBack['msg_list'] = msg_list
                        oBack['status'] = 'error'
                        basket.set_status('error')
                    else:
                        # Set all that is needed in the basket
                        if 'jobid' in oCrpp:
                            basket.set_jobid(oCrpp['jobid'])
                        elif 'jobid' in oExeStatus:
                            basket.set_jobid(oExeStatus['jobid'])
                        else:
                            # Not sure why we do not have jobid
                            sStop = "Yes"
                        basket.set_status("exe_starting")
                        # Adapt the message
                        oBack['msg'] = 'sent to the server'
                else:
                    oBack['status'] = 'error'
                    oBack['msg'] = 'Could not perform execute at /crpp'
                    basket.set_status('error')
            else:
                oBack['status'] = 'error'
                oBack['msg'] = 'Could not send CRP to /crpp. Status=['+oCrpp['commandstatus'] +']'
                basket.set_status('error')
        except:
            # Could not send this to the CRPX
            oBack['status'] = 'error'
            oBack['msg'] = oErr.DoError('Failed to send or execute the project to /crpp')
        # Return the status
        return oBack


class Basket(models.Model):
    """A basket of material needed for the transformation and execution of a research project"""

    # [1] Format of the corpus this basket searches in
    format = models.CharField("XML format", choices=build_abbr_list(CORPUS_FORMAT), 
                              max_length=5, help_text=get_help(CORPUS_FORMAT))
    # [1] The corpus-part this points to
    part = models.ForeignKey(Part, blank=False, null=False, on_delete=models.CASCADE, related_name="part_baskets")
    # [1] The Xquery definitions (targeted for the corpus)
    codedef = models.TextField("Xquery definitions", blank=True)
    # [1] The Xquery code for the main query
    codeqry = models.TextField("Xquery main query", blank=True)
    # [1] The status of (a) code generation and (b) execution
    status = models.CharField("Status", max_length=MAX_TEXT_LEN)
    # [0-1] The jobid generated by /crpp
    jobid = models.CharField("Job identifier", max_length=MAX_NAME_LEN, blank=True)
    # [0-1] Options (in JSON string) for this particular search
    options = models.TextField("Search options", blank=True)
    # [0-1] create date and lastsave date
    created = models.DateTimeField(default=timezone.now)
    saved = models.DateTimeField(null=True, blank=True)
    # [1] Each basket is linked to one research project
    research = models.ForeignKey(Research, blank=False, null=False, on_delete=models.CASCADE, related_name="baskets")

    def __str__(self):
        # COmbine: research project name, research id, processing status
        return "{}_{}: {}".format(self.research.name, self.id, self.status)

    def delete(self, using = None, keep_parents = False):
        # Delete all Quantor objects associated with me
        for q in self.myquantor.all():
            q.delete()
        # Delete all  kwiclines
        for k in self.kwiclines.all():
            k.delete()
        return super(Basket, self).delete(using, keep_parents)

    def get_delete_url(self):
        """Produce an URL to be called when requesting to delete [self]"""

        return reverse('result_delete', kwargs={'object_id': self.id})

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
        # Adapt the save date
        self.saved = timezone.now()
        response = super(Basket, self).save(force_insert, force_update, using, update_fields)
        return response

    def set_status(self, sStatus):
        oErr = ErrHandle()
        self.status = sStatus
        self.save()
        oErr.Status("Basket status="+sStatus)
        return True

    def get_status(self):
        self.refresh_from_db()
        return self.status

    def set_jobid(self, jobid):
        self.jobid = jobid
        self.save()
        return True

    def get_progress(self):
        """Issue a progress request for this job and return the status"""

        # Initialise the status
        oBack = {'commandstatus': 'ok'}
        oErr = ErrHandle()

        # Do we have a jobid already?
        if self.jobid == None or self.jobid == "":
            oCrpp = dict(commandstatus="ok",
                         status="preparing",
                         code="preparing",
                         message="Converting",
                         userid="erwin") 
        else:

            # Issue a status request
            sUser = self.research.owner.username
            oCrpp = crpp_status(sUser, self.jobid)

        # Now process the [oCrpp]
        try:
            if oCrpp['commandstatus'] == 'ok':
                for item in oCrpp:
                    if item != 'commandstatus':
                        oBack[item] = oCrpp[item]
            else:
                oBack['commandstatus'] = 'error'
                if 'message' in oCrpp:
                    oBack['msg'] = oCrpp['message']
                elif 'code' in oCrpp:
                    oBack['msg'] = oCrpp['code']

        except:
            oBack['commandstatus'] = "error"
            oBack['msg'] = oErr.DoError("get_progress error")

        # And then we return what we have
        return oBack

    def set_quantor(self, oResults):
        """Get or create a quantor and put all the results from [oResults] into it"""

        oErr = ErrHandle()
        oBack = {'status': 'ok'}
        try:
            self.set_status("creating quantor")
            # Get all quantors (if any) still attached to me
            qs = Quantor.objects.filter(basket=self)
            # Remove them
            qs.delete()

            # Preparation: get necessary instances
            instPart = self.part
            instFormat = choice_value(CORPUS_FORMAT, self.format)

            # Do all in one go
            # with transaction.atomic():
            iNumQc = len(oResults['table'])
            # Create a completely new quantor
            iFiles = 0
            if 'table' in oResults and len(oResults['table'] )>0 and 'hits' in oResults['table'][0]:
                iFiles = len(oResults['table'][0]['hits'])
            quantor = Quantor(basket=self, searchTime=oResults['searchTime'],
                                total=iFiles, qcNum=iNumQc)
            quantor.save()
            # Get or create the required QC lines
            for idx in range(0, iNumQc):
                # Access the result information for this QC
                oQcResults = oResults['table'][idx]
                # Set the QC number
                qc = idx + 1
                qcline = QCline(quantor=quantor, qc=qc, count=oQcResults['total'])
                qcline.save()
                # Create all the necessary subcategories
                numsubcats = len(oQcResults['subcats'])
                subcats = []
                with transaction.atomic():
                    for subnum in range(0, numsubcats):
                        # Get or create this subject
                        qsubcat = Qsubcat(qcline=qcline, 
                                            name=oQcResults['subcats'][subnum],
                                            count=oQcResults['counts'][subnum])
                        qsubcat.save()
                        subcats.append(qsubcat)
                last_file = ""
                text = None
                # Get the number of documents that contain 0 or more hits
                hits = len(oQcResults['hits'])

                # Divide this into packages of 1000 hits, after which a real 'save' happens
                idx = 0
                iChunkSize = 10000
                iShowSize = 1000
                iNumLines = 0
                iNumWords = 0
                # Sort the hitlist
                # hit_list = oQcResults['hits'].sort(key=lambda x: x['file'])
                hit_list = sorted(oQcResults['hits'], key=lambda hit: hit['file'])
                # Sort texts
                text_list = Text.sorted_texts(instPart, instFormat)
                # Check if there are any results
                if len(text_list) == 0:
                    msg = "set_quantor error: there are no texts of type {} in part {}".format(
                        get_format_name(instFormat), instPart )
                    oBack['status'] = 'error'
                    oBack['msg'] = msg
                    return oBack
                # Get the first text
                text_list_iter = text_list.iterator()
                text = next(text_list_iter)
                if text != None:
                    chunks = math.ceil( hits / iChunkSize)
                    for chunk in range(chunks):
                        # Set the max idx
                        max_idx = (chunk + 1) * iChunkSize
                        with transaction.atomic():
                            while idx < max_idx and idx < hits:
                                if idx % iShowSize == 0:
                                    sMsg = "set_quantor hits: {} / {}".format(idx, hits)
                                    oErr.Status(sMsg)
                                hit = hit_list[idx]

                                # Get the file name
                                file = Text.strip_ext( hit['file'])

                                # Check if we have the right file
                                while file != text.fileName:
                                    # text = next(text_list.iterator())
                                    try:
                                        text = next(text_list_iter)
                                    except StopIteration as e:
                                        # This is the normal 'end' of the iteration.
                                        # But getting here means that the 'file' has not been found within [text_list_iter]
                                        # WHY ??? - Is it not in [text_list]?? Double check...
                                        print(e)
                                        break

                                # Keep track of the number of words and lines
                                iNumLines += text.lines
                                iNumWords += text.words

                                # Process the sub categories
                                for subnum in range(0, numsubcats):
                                    # Get this Qsubcat and the count for it
                                    qsubcat = subcats[subnum]
                                    subcount = hit['subs'][subnum]
                                    # Add the appropriate Qsubinfo
                                    qsubinfo = Qsubinfo(subcat = qsubcat, 
                                                        text= text,
                                                        count = subcount)
                                    qsubinfo.save()
                                # Go to the next hit
                                idx += 1

                    # Put the number of lines and words in the quantor
                    quantor.lines = iNumLines
                    quantor.words = iNumWords
                    quantor.save()
                                
            # Create KWIC material for each QC line
            for idx in range(0, iNumQc):
                if not self.set_kwic(idx+1, oErr):
                    oBack['status'] = 'error'
                    oBack['msg'] = oErr.get_error_stack()
                    return oBack

            # REturn positively
            return oBack
        except:
            # Failure
            msg = oErr.get_error_message()
            oErr.DoError('set_quantor could not read the hit information')
            oBack['status'] = 'error'
            oBack['msg'] = msg
            return oBack

    def create_kwic_objects(self):
        """Create all needed KWIC objects"""

        # Get the quantor (if existing)
        quantor = Quantor.objects.filter(basket=self).first()
        if quantor != None:
            # We can only proceed if there is a Quantor
            iNumQc = quantor.qcNum
            # Now create the KWIC instances
            for idx in range(0, iNumQc):
                self.set_kwic(idx+1)

    def get_kwic(self, iQcLine):
        """Get the Kwic object under this basket with the indicated QC line"""

        return Kwic.objects.filter(basket=self, qc=iQcLine).first()

    def set_kwic(self, iQcLine, oErr = None):
        """Check if a KWIC table is available; otherwise make one"""

        if oErr == None: oErr = ErrHandle()
        try:
            # Get the number of results from the associated QCline object
            lstQ = []
            lstQ.append(Q(quantor__basket = self))
            lstQ.append(Q(qc=iQcLine))
            oQcLine = QCline.objects.filter(*lstQ).first()
            if oQcLine == None:
                # No results can be retrieved
                return False
            quantor_count_for_this_qc = oQcLine.count

            # Get the /crpp/dbinfo count for this QC line
            sUser = self.research.owner.username
            sCrpName = self.research.name
            sPartDir = self.part.dir
            oDbInfoBack = crpp_dbinfo(sUser, sCrpName, iQcLine, -1, 0,sPart=sPartDir)
            if oDbInfoBack['commandstatus'] != 'ok':
                oErr.DoError("set_kwic: didn't get a positive reply from /crpp/dbinfo")
                # Cannot get a positive reply
                return False
            dbinfo_count_for_this_qc = oDbInfoBack['Size']
            feature_list = json.dumps(oDbInfoBack['Features'])

            # TEst to see if the counts coincide
            if quantor_count_for_this_qc != dbinfo_count_for_this_qc:
                oErr.DoError("set_kwic: the dbinfo count of the results differs from the quantor count")
                return False

            # Accept the count for this QC
            count_for_this_qc = dbinfo_count_for_this_qc

            # Check for the presence of enough elements
            qs = Kwic.objects.filter(basket=self, qc=iQcLine)
            if qs.count() != 0:
                # Delete what is there
                qs.delete()
            # Create a KWIC object for this information
            kwic = Kwic(basket=self, 
                        qc=iQcLine, 
                        features=feature_list,
                        hitcount=count_for_this_qc,
                        textcount=oQcLine.quantor.total)
            kwic.save()
            
            # All is well now: the correct KWIC is ready
            return True
        except:
            # Failure
            oErr.DoError('set_kwic could not read the hit information')
            return False

    def get_filters(self):
        filters = []
        for item in self.kwiclines.all():
            # filters.append(item.get_filter())
            filters.append(item.kwicfilters.all())
        return filters

    def get_filter_list(self, iQcLine):
        kwic = self.get_kwic(iQcLine)
        if kwic == None:
            if self.set_kwic(iQcLine):
                kwic = self.get_kwic(iQcLine)
        if kwic == None:
            return []
        else:
            return kwic.kwicfilters.all()

    def get_feature_list(self, iQcLine):
        kwic = self.get_kwic(iQcLine)
        return kwic.get_features()
    

class Kwic(models.Model):
    """Keyword-in-context results
    
    Note: The actual results reside on the /crpp server.
          This model only provides an abstract layer, so that KwicListView works.
    """

    # [1] Each KWIC belongs to a particular QCline
    qc = models.IntegerField("QC number", default=1)
    # [1] Number of texts
    textcount = models.IntegerField("Number of texts", default=0)
    # [1] Number of hits
    hitcount = models.IntegerField("Number of hits", default=0)
    # [1] String JSON list of feature names
    features = models.TextField("Features", default="[]")
    # [0-1] Stringified JSON that explains which results (if any) are already present
    resultKey = models.TextField("Result key", blank=True, null=True)
    # [1] There must be a link to the Basket the results belong to
    basket = models.ForeignKey(Basket, blank=False, null=False, on_delete=models.CASCADE, related_name="kwiclines")

    def __str__(self):
        return "{}".format(self.qc)

    def delete(self, using = None, keep_parents = False):
        # Delete the quantor and all under it
        with transaction.atomic():
            # (1) Walk all the kwicfilters
            self.kwicfilters.all().delete()
            # (2) Walk all the kwicresults
            self.kwicresults.all().delete()
        # Remove myself
        response = super(Kwic, self).delete(using, keep_parents)
        return response

    def add_filter(self, sField, sValue):
        # Add this to the set of filters belonging to this Kwic object
        obj = KwicFilter(kwic=self, field=sField, value=sValue)
        obj.save()

    def get_filter(self):
        # Combine all filters into a JSON object to be sent
        oFilter = {}
        for item in self.kwicfilters.all():
            oFilter[item.field] = item.value
        return oFilter

    def get_features(self):
        lFeatures = json.loads(self.features)
        return lFeatures

    def apply_filter(self, oFilter=None):
        oErr = ErrHandle()
        # Combine all filters into a JSON object to be sent
        if oFilter == None:
            oFilter = self.get_filter()
        # Send to /crpp/dbinfo to get the correct amounts
        sUser = self.basket.research.owner.username
        sCrpName = self.basket.research.name
        sPartDir = self.basket.part.dir
        iQcLine = self.qc
        oDbInfoBack = crpp_dbinfo(sUser, sCrpName, iQcLine, -1, 0, filter=oFilter, sPart=sPartDir)
        if oDbInfoBack['commandstatus'] != 'ok':
            oErr.DoError("apply_filter: didn't get a positive reply from /crpp/dbinfo")
            # Cannot get a positive reply
            return False
        # Adapt the hitcount
        self.hitcount = oDbInfoBack['Size']
        self.save()
        # REturn positively
        return True
      
    def add_result(self, oResult):
        iResId = oResult['ResId']
        sResult = json.dumps(oResult)
        obj = KwicResult(resId=iResId, result=sResult, kwic=self)
        obj.save()
        return True

    def has_filter(self, oFilter):
        """Check if the CURRENT kwic object contains the filter indicated"""

        if self.resultKey == None or self.resultKey == "":
            return False
        # Get the filter we currently have
        oResultKey = json.loads(self.resultKey)
        if not 'filter' in oResultKey:
            return False
        sStoredFilter = json.dumps( oResultKey['filter'])
        sCurrentFilter = json.dumps(self.get_filter())
        return (sStoredFilter == sCurrentFilter)

    def has_page(self, page):
        """Check if the CURRENT kwic object pertains to the page indicated"""

        if self.resultKey == None or self.resultKey == "":
            return False
        # Get the filter we currently have
        oResultKey = json.loads(self.resultKey)
        if not 'page' in oResultKey:
            return False
        sStoredPage = json.dumps( oResultKey['page'])
        return (sStoredPage == page)

    def has_results(self, oFilter, page):
        """Check if the CURRENT kwic object contains the results and the filter indicated"""

        if self.resultKey == None or self.resultKey == "" or page == None:
            return False
        # Create an object for comparison
        oResultKey = {'filter': oFilter, 'page': page}
        sResultKey = json.dumps(oResultKey)
        return (sResultKey == self.resultKey)

    def add_result_list(self, result_list, page):
        # Create a result key and add it
        oResultKey = {'filter': self.get_filter(), 'page': page}
        self.resultKey = json.dumps(oResultKey)
        with transaction.atomic():
            self.kwicresults.all().delete()
            for result in result_list:
                self.add_result(result)
            # Save the result key
            self.save()
        return True

    def get_result(self, iResId):
        """Get the result with the indicated ResId"""

        result = self.kwicresults.filter(resId=iResId).first()
        if result == None:
            return None
        else:
            return json.loads( result.result)

    def clear_results(self):
        """Remove all the result objects that were made for me until now"""
        with transaction.atomic():
            self.kwicresults.all().delete()
        return True

    def get_lines(self):
        # Find out what quantor we have
        quantor = self.basket.myquantor.first()
        return quantor.get_lines()

    def get_words(self):
        # Find out what quantor we have
        quantor = self.basket.myquantor.first()
        return quantor.get_words()


class KwicFilter(models.Model):
    """A filter that needs to be applied to the KWIC it is attached to"""

    # [1] The database field this filter applies to
    field = models.CharField("Database field", max_length=MAX_NAME_LEN)
    # [1] Either 'and' or 'and not'
    operator = models.CharField("Filter operator", choices=build_abbr_list(SEARCH_FILTEROPERATOR), 
                              max_length=5)
    # [1] The value of the filter
    value = models.CharField("Value", max_length=MAX_TEXT_LEN)
    # [1] Link this filter the the KWIC it belongs to
    kwic = models.ForeignKey(Kwic, blank=False, null=False, on_delete=models.CASCADE, related_name="kwicfilters")

    def __str__(self):
        return "{}".format(self.field)


class KwicResult(models.Model):
    """Details of selected results that are or have been requested by the user"""

    # [1] Identification of this result by the ResId (also within [result] field)
    resId = models.IntegerField("Result identifier")
    # [1] Result details in the form of a JSON object (stringified)
    result = models.TextField("JSON details")
    # [1] Link this filter the the KWIC it belongs to
    kwic = models.ForeignKey(Kwic, blank=False, null=False, on_delete=models.CASCADE, related_name="kwicresults")

    def __str__(self):
        return "{}".format(self.resId)


class Quantor(models.Model):
    """QUantificational results of executing one basket"""

    # [1] A Quantor is linked to a basket
    basket = models.ForeignKey(Basket, blank=False, null=False, on_delete=models.CASCADE, related_name="myquantor")
    # [1] THe number of files (texts) that have been searched
    total = models.IntegerField("Number of files", default=0)
    # [0-1] The number of lines in the texts
    lines = models.IntegerField("Number of lines", blank=True, null=True)
    # [0-1] The number of words in the searched texts
    words = models.IntegerField("Number of words", blank=True, null=True)
    # [1] Keep the number of milliseconds the search took
    searchTime = models.IntegerField("Search time (ms)", default=0)
    # [1] Need to know the number of QCs for this search
    qcNum = models.IntegerField("Number of query lines", default=1)

    def __str__(self):
        return "{}".format(self.total)

    def get_quantor(basket):
        # CHeck if this exists
        item = Quantor.objects.filter(basket=basket).first()
        if item == None:
            item = Quantor(basket=basket)
            item.save()
        # Return the fetched or created item
        return item

    def delete(self, using = None, keep_parents = False):
        # Delete the quantor and all under it
        with transaction.atomic():
            # (1) Walk all its qclines
            for qcline in self.qclines.all():
                # (2) Each qcline has qsubcats
                for qsubcat in qcline.qsubcats.all():
                    # (3) Remove all the related qsubinfo elements
                    qsubcat.qsubinfos.all().delete()
                # Now we can remove the qsubcats
                qcline.qsubcats.all().delete()
            # Now remove the qclines
            self.qclines.all().delete()
        # Remove myself
        response = super(Quantor, self).delete(using, keep_parents)
        return response

    def get_lines(self):
        """Return or retrieve the number of lines in the texts that have been searched"""

        iCount = -1
        if self.lines == None:
            oCount = Qsubinfo.objects.filter(Q(subcat__qcline__quantor=self)).values("text").annotate(num_lines=Sum('text__lines')).aggregate(Sum('num_lines'))
            if 'num_lines__sum' in oCount:
                iCount = oCount['num_lines__sum']
                self.lines = iCount
                self.save()
        else:
            iCount = self.lines
        # Return what we have
        return iCount

    def get_words(self):
        """Return or retrieve the number of words in the texts that have been searched"""

        iCount = -1
        if self.words == None:
            oCount = Qsubinfo.objects.filter(Q(subcat__qcline__quantor=self)).values("text").annotate(num_words=Sum('text__words')).aggregate(Sum('num_words'))
            if 'num_words__sum' in oCount:
                iCount = oCount['num_words__sum']
                self.words = iCount
                self.save()
        else:
            iCount = self.words
        # Return what we have
        return iCount


class QCline(models.Model):

    # [1] A subcategory belongs to a particular QC of the quantor
    qc = models.IntegerField("QC number", default=1)
    # [1] The number of hits for this QC line
    count = models.IntegerField("Number of hits", default=0)
    # [1] Every QCline is linked to a Quantor with results
    quantor = models.ForeignKey(Quantor, blank=False, null=False, on_delete=models.CASCADE, related_name="qclines")

    def __str__(self):
        return "{}".format(self.qc)

    def get_qcline(quantor, qcnum):
        # CHeck if this exists
        item = QCline.objects.filter(qc=qcnum, quantor=quantor).first()
        if item == None:
            item = QCline(qc=qcnum, quantor=quantor)
            item.save()
        # Return the fetched or created item
        return item

    def set_count(self, count):
        self.count = count
        self.save()


class Qsubcat(models.Model):
    """Subcategory made when executing one project"""

    # [1] Subcategory must have a name--but not too long
    name = models.CharField("Name", max_length=MAX_TEXT_LEN)
    # [1] The number of hits for this subcat
    count = models.IntegerField("Number of hits", default=0)
    # [1] Every subcategory is linked to a QCline
    qcline = models.ForeignKey(QCline, blank=False, null=False, on_delete=models.CASCADE, related_name="qsubcats")

    def __str__(self):
        return self.name

    def get_qsubcat(qcline, name):
        # CHeck if this exists
        item = Qsubcat.objects.filter(qcline=qcline, name=name).first()
        if item == None:
            item = Qsubcat(qcline=qcline, name=name)
            item.save()
        # Return the fetched or created item
        return item

    def set_count(self, count):
        self.count = count
        self.save()


class Qsubinfo(models.Model):   
    """Information on one subcategory of one file"""

    # [1] subcatinfo links to a QUantor-Subcat name
    subcat = models.ForeignKey(Qsubcat, blank=False, null=False, on_delete=models.CASCADE, related_name="qsubinfos")
    # [1] subcatinfo also links to a Text (which is under the part)
    text = models.ForeignKey(Text, blank=False, null=False, on_delete=models.CASCADE, related_name="text_qsubinfos")
    # [1] The new information is the COUNT - the number of hits
    count = models.IntegerField("Hits", default=0)

    def __str__(self):
        return "{}".format(self.count)

    def get_qsubinfo(subcat, text):
        # CHeck if this exists
        item = Qsubinfo.objects.filter(subcat=subcat, text=text).first()
        if item == None:
            item = Qsubinfo(subcat=subcat, text=text)
            item.save()
        # Return the fetched or created item
        return item

    def set_count(self, count):
        self.count = count
        self.save()


class ShareGroup(models.Model):
    """Group witch which a project is shared"""

    # [1] The group a project is shared with
    group = models.ForeignKey(Group, blank=False, null=False, on_delete=models.CASCADE, related_name="group_sharegroups")
    # [1] THe permissions granted to this group
    permission = models.CharField("Permissions", choices=build_abbr_list(SEARCH_PERMISSION), 
                              max_length=5, help_text=get_help(SEARCH_PERMISSION))
    # [1] Each Research object can be shared with any number of groups
    research = models.ForeignKey(Research, blank=False, null=False, on_delete=models.CASCADE, related_name="sharegroups")

    def __str__(self):
        return "{}-{}".format(self.group, self.permission)

