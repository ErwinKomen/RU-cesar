"""Models for the SEEKER app.

The seeker helps users define and execute searches through the texts that
are available at the back end
"""
from django.db import models, transaction
from django.contrib.auth.models import User, Group
from datetime import datetime
from cesar.utils import *
from cesar.settings import APP_PREFIX
from cesar.browser.models import build_choice_list, build_abbr_list, get_help, choice_value
import sys
import copy
import json

MAX_NAME_LEN = 50
MAX_TEXT_LEN = 200

SEARCH_FUNCTION = "search.function"
SEARCH_OPERATOR = "search.operator"
SEARCH_PERMISSION = "search.permission"
SEARCH_VARIABLE_TYPE = "search.variabletype"
SEARCH_ARGTYPE = "search.argtype"

WORD_ORIENTED = 'w'
CONSTITUENT_ORIENTED = 'c'
TARGET_TYPE_CHOICES = (
    ('0', '----'),
    (WORD_ORIENTED, 'Word(s)'),
    (CONSTITUENT_ORIENTED, 'Constituent(s)'),
)


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
        return "{}({}({}))".format(
            self.get_function_display(),
            self.get_operator_display(),
            self.value)

    def create_item(function, value, operator):
        operator_matches = choice_value(SEARCH_OPERATOR, operator)
        function_word = choice_value(SEARCH_FUNCTION, function)
        obj = SearchMain.objects.create(function=function_word,
                                        operator=operator_matches,
                                        value = value)
        return obj

    

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
    # [0-n] Additional search items
    # [1-n]

    # This line is needed, in order to add the Gateway.create_gateway() call
    objects = GatewayManager()

    def __str__(self):
        return self.name

    def delete(self, using = None, keep_parents = False):
        """Delete all the Construction items pointing to me"""
        cns_set = self.constructions.all()
        for cns_this in cns_set:
            cns_this.delete()
        # Now perform the normal deletion
        return super().delete(using, keep_parents)

    def get_vardef_list(self):
        # Get a list of all variables for this gateway
        var_pk_list = [var.pk for var in self.gatewayvariables.all()]
        # Now get the list of vardef variables coinciding with this
        vardef_list = [var for var in VarDef.objects.filter(pk__in=var_pk_list)]
        return vardef_list

    def get_construction_list(self):
        return [cns for cns in self.constructions.all()]

    def check_cvar(self):
        """Check all the CVAR connected to me, adding/deleting where needed"""

        with transaction.atomic():
            # Step 1: add CVAR for all Construction/Vardef combinations
            for vardef in self.get_vardef_list():
                # Walk all constructions
                for construction in self.constructions.all():
                    # Check if a cvar exists
                    qs = ConstructionVariable.objects.filter(variable=vardef, construction=construction)
                    if qs.count() == 0:
                        # Doesn't exist: create it
                        cvar = ConstructionVariable(variable=vardef, construction=construction)
                        cvar.save()
            # Step 2: Find CVAR that do not belong to a gateway
            gateway_pk_list = [item.pk for item in Gateway.objects.all()]
            cvar_orphans = [cvar for cvar in ConstructionVariable.objects.exclude(construction__gateway__in=gateway_pk_list)]
            # Remove these instances
            for cvar in cvar_orphans:
                cvar.delete()
            cvar_orphans = [cvar for cvar in ConstructionVariable.objects.exclude(variable__gateway__in=gateway_pk_list)]
            # Remove these instances
            for cvar in cvar_orphans:
                cvar.delete()
        # Make sure we are happy
        return True
      
      
class Construction(models.Model):
    """A search construction consists of a [search] element and one or more search items"""

    # [1] Construction name
    name = models.CharField("Name of this search construction", max_length=MAX_TEXT_LEN)
    # [1] Main search item
    search = models.ForeignKey(SearchMain, blank=False, null=False, on_delete=models.CASCADE)
    # [1] Every gateway has one or more constructions it may look for
    gateway = models.ForeignKey(Gateway, blank=False, null=False, related_name="constructions", on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def delete(self, using = None, keep_parents = False):
        # Also delete the searchMain
        self.search.delete()
        # And then delete myself
        return super().delete(using, keep_parents)

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
      save_result = super().save(force_insert, force_update, using, update_fields)
      # Check and add/delete CVAR instances for this gateway
      Gateway.check_cvar(self.gateway)
      # Return the result of normal saving
      return save_result

      
class Variable(models.Model):
    """A variable has a name and a value, possibly combined with a function and a condition"""

    # [1] Variable obligatory name
    name = models.CharField("Name of this variable", max_length=MAX_NAME_LEN)
    # [0-1] Description/explanation for this variable
    description = models.TextField("Description of this variable")
    # [1] Link to the Gateway the variable belongs to
    gateway = models.ForeignKey(Gateway, blank=False, null=False, related_name="gatewayvariables")

    def __str__(self):
        return self.name


class VarDef(Variable):
    """Each research project may have a number of variables that are construction-specific"""
    pass

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
      # Perform the normal saving
      save_result = super().save(force_insert, force_update, using, update_fields)
      # Check and add/delete CVAR instances for this gateway
      Gateway.check_cvar(self.gateway)
      # Return the result of normal saving
      return save_result


class GlobalVariable(Variable):
    """Each research project may have any number of global (static) variables"""

    # [1] Value of the variable
    value = models.TextField("Value")

    def __str__(self):
        # The default string-value of a global variable is its name
        return self.name


class FunctionDef(models.Model):
    """Definition of one function"""

    # [1] The short (internal) name of this function
    name = models.CharField("Short function name", max_length=MAX_NAME_LEN)
    # [1] The title of this function to be shown
    title = models.CharField("Function title", max_length=MAX_TEXT_LEN)
    # [1] Each function must have one or more arguments
    argnum = models.IntegerField("Number of arguments", default=1)

    def __str__(self):
        return self.name

    #def get_functiondef_display(self):
    #    return self.name


class Function(models.Model):
    """Realization of one function based on a definition"""

    # [1] Must point to a definition
    functiondef = models.ForeignKey(FunctionDef, null=False)
    # [1] A function belongs to a construction variable - but this is not necessarily the parent
    root = models.ForeignKey("ConstructionVariable", null=False, related_name="functionroot")
    # [0-1] A function MAY belong to a particular ARGUMENT, which then is its parent
    parent = models.ForeignKey("Argument", null=True, blank=True, related_name="functionparent")
    # [1] The value that is the outcome of this function
    #     This is a JSON list, so can be bool, int, string of any number
    output = models.TextField("JSON value", null=False, blank=True, default="[]")

    def __str__(self):
        return self.output

    def delete(self, using = None, keep_parents = False):
        # First delete any ARG elements pointing to me
        for arg in self.argument_set.all():
            arg.delete()
        # Now delete myself
        result = super().delete(using, keep_parents)
        # Save the changes
        self.save()
        return result

    @classmethod
    def create(cls, functiondef, functionroot):
        """Create a new instance of a function based on a 'function definition', binding it to a cvar"""
        with transaction.atomic():
            inst = cls(functiondef=functiondef, root=functionroot)
            # Save this function
            inst.save()
            # Add all the arguments that are needed
            for argdef in functiondef.arguments.all():
                arg = Argument(argumentdef=argdef, argtype=argdef.argtype, 
                               functiondef=functiondef, function=inst)
                # Save this argument
                arg.save()
        return inst


      
class ArgumentDef(models.Model):
    """Definition of one argument for a function"""

    # [1] The descriptive name of this argument
    name = models.CharField("Descriptive name", max_length=MAX_TEXT_LEN)
    # [1] The text to precede this argument within the specification element
    text = models.CharField("Preceding text", blank=True, max_length=MAX_TEXT_LEN)
    # [1] The numerical order of this argument
    order = models.IntegerField("Order", blank=False, default=0)
    # [1] The value can be of type: fixed, global variable, construction variable, function-output
    argtype = models.CharField("Variable type", choices=build_abbr_list(SEARCH_ARGTYPE), 
                              max_length=5, help_text=get_help(SEARCH_ARGTYPE))
    # [1] The value that is the outcome of this function: 
    #     This is a JSON list, it can contain any number of bool, int, string
    argval = models.TextField("JSON value", blank=True, default="[]")
    # Each function may take a number of input arguments
    function = models.ForeignKey(FunctionDef, null=False, related_name = "arguments")


class Argument(models.Model):
    """The realization of an argument, based on its definition"""

    # [1] Must point to a definition
    argumentdef = models.ForeignKey(ArgumentDef, null=False)
    # [1] The value can be of type: fixed, global variable, construction variable, function-output
    argtype = models.CharField("Variable type", choices=build_abbr_list(SEARCH_ARGTYPE), 
                              max_length=5, help_text=get_help(SEARCH_ARGTYPE))
    # [1] In the end, the value is calculated and appears here
    argval = models.TextField("JSON value", blank=True, default="[]")
    # [0-1] This argument may link to a Global Variable
    gvar = models.ForeignKey("GlobalVariable", null=True)
    # [0-1] This argument may link to a Construction Variable
    cvar = models.ForeignKey("ConstructionVariable", null=True)
    # [0-1] This argument may link to a Function (not its definition)
    function = models.ForeignKey("Function", null=True)
    # [0-1] If a function is needed, we need to have a link to its definition
    functiondef = models.ForeignKey(FunctionDef, null=True)

    #def get_argtype_display(self):
    #    return self.get_argtype_display()

    #def get_functiondef_display(self):
    #    return self.functiondef.name



class ConstructionVariable(models.Model):
    """Each construction may provide its own value to the variables belonging to the gateway"""

    # [1] Link to the Construction the variable value belongs to
    construction = models.ForeignKey(Construction, blank=False, null=False, related_name="constructionvariables")
    # [1] Link to the name of this variable
    variable = models.ForeignKey(VarDef,  blank=False, null=False, on_delete=models.CASCADE, related_name="variablenames")
    # [1] Type of value: string or expression
    type = models.CharField("Variable type", choices=build_abbr_list(SEARCH_VARIABLE_TYPE), 
                              max_length=5, help_text=get_help(SEARCH_VARIABLE_TYPE))
    # [1] String value of the variable for this combination of Gateway/Construction
    svalue = models.TextField("Value", blank=True)
    # [0-1] This variable may be determined by a Global Variable
    gvar = models.ForeignKey("GlobalVariable", null=True)
    # [0-1] This variable may be determined by a Function
    function = models.OneToOneField(Function, null=True)
    # [0-1] If a function is supplied, then here's the place to define the function def to be used
    functiondef = models.ForeignKey(FunctionDef, null=True)

    def __str__(self):
        sConstruction = self.construction.name
        sVariable = self.variable.name
        return "C:[{}|{}]=[{}]".format(sConstruction, sVariable, self.svalue)

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
        return super().save(force_insert, force_update, using, update_fields)


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
    construction = models.ForeignKey(Construction, blank=False, null=False, related_name="searchitems")

    def __str__(self):
        return self.name


class Research(models.Model):
    """Main entry for a research project"""

    # [1] Name of the CRP from which the results come (does not necessarily have to be here)
    name = models.CharField("Research project name", max_length=MAX_TEXT_LEN)
    # [1] Purpose of this research
    purpose = models.TextField("Purpose")
    # [1] The main type of this research: is it word oriented or constituent oriented?
    targetType = models.CharField("Main element type", choices=TARGET_TYPE_CHOICES, 
                              max_length=5)
    # [1] Each research project has a 'gateway': a specification for the $search element
    gateway = models.OneToOneField(Gateway, blank=False, null=False, on_delete=models.CASCADE)
    # [1] Each research project has its owner: obligatory, but not to be selected by the user himself
    owner = models.ForeignKey(User, editable=False)

    def __str__(self):
        return self.name

    def gateway_name(self):
        return self.gateway.name

    def delete(self, using = None, keep_parents = False):
        # Delete the gateway
        self.gateway.delete()
        # Delete all the sharegroup instances pointing to this research instance
        for grp in self.sharegroups.all():
            grp.delete()
        # Delete myself
        return super().delete(using, keep_parents)

    def username(self):
        return self.owner.username


class ShareGroup(models.Model):
    """Group witch which a project is shared"""

    # [1] The group a project is shared with
    group = models.OneToOneField(Group, blank=False, null=False)
    # [1] THe permissions granted to this group
    permission = models.CharField("Permissions", choices=build_choice_list(SEARCH_PERMISSION), 
                              max_length=5, help_text=get_help(SEARCH_PERMISSION))
    # [1] Each Research object can be shared with any number of groups
    research = models.ForeignKey(Research, blank=False, null=False, related_name="sharegroups")


