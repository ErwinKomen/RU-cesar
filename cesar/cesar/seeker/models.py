"""Models for the SEEKER app.

The seeker helps users define and execute searches through the texts that
are available at the back end
"""
from django.db import models, transaction
from django.db.models import Q
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from datetime import datetime
from cesar.utils import *
from cesar.settings import APP_PREFIX
from cesar.browser.models import build_choice_list, build_abbr_list, \
                                 get_help, choice_value, get_instance_copy, \
                                 copy_m2m, copy_fk, Part, CORPUS_FORMAT, Text
from cesar.seeker.services import crpp_exe, crpp_send_crp, crpp_status, crpp_dbinfo
import sys
import copy
import json

MAX_NAME_LEN = 50
MAX_TEXT_LEN = 200
    
SEARCH_FUNCTION = "search.function"                 # woordgroep
SEARCH_OPERATOR = "search.operator"                 # groeplijktop
SEARCH_PERMISSION = "search.permission"
SEARCH_VARIABLE_TYPE = "search.variabletype"        # fixed, calc, gvar
SEARCH_ARGTYPE = "search.argtype"                   # fixed, gvar, cvar, dvar, func, cnst, axis, hit
SEARCH_CONDTYPE = "search.condtype"                 # func, dvar
SEARCH_TYPE = "search.type"                         # str, int, bool, cnst
# SEARCH_FILTER = "search.filteroperator"
SEARCH_FILTEROPERATOR = "search.filteroperator"     # first, and, andnot
# SEARCH_FILTEROPERATOR = (('first', 'first'), ('and', 'and'), ('andnot', 'andnot'))

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

    def get_copy(self, **kwargs):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def create_item(function, value, operator):
        operator_matches = choice_value(SEARCH_OPERATOR, operator)
        function_word = choice_value(SEARCH_FUNCTION, function)
        obj = SearchMain.objects.create(function=function_word,
                                        operator=operator_matches,
                                        value = value)
        return obj

    def get_search_spec(self):
        """Combine all single-word lines into a string like 'aap|noot|mies'
           Divide the remainder into a list of line-objects, containing a list of word-objects"""

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
        return {'single': sSingle, 'line_list': sMulti}
        

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
        return "{}:{}".format(self.id, self.name)

    def get_copy(self, **kwargs):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Prepare an object for further processing
        kwargs = {'gateway': new_copy}
        # Copy all 'VarDef' and 'GlobalVariable' instances linked to me
        dvar_list = copy_m2m(self, new_copy, "definitionvariables", **kwargs)
        gvar_list = copy_m2m(self, new_copy, "globalvariables", **kwargs)

        # Prepare an object for further processing
        # kwargs['lst_m2m'] = ["constructionvariables"]
        # Copy all constructions + all associated construction variables
        cons_list = copy_m2m(self, new_copy, "constructions", **kwargs)
        # Now visit all construction variables
        cvar_list = ConstructionVariable.objects.filter(construction__gateway=self)
        kwargs['dvar_list'] = dvar_list
        kwargs['gvar_list'] = gvar_list
        kwargs['cons_list'] = cons_list
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
        # Return the new copy
        return new_copy

    def get_search_list(self):
        """List the names of the constructions plus their search group and specification"""
        qs = self.constructions.all()
        lBack = []
        for item in qs:
            oSearch = item.search.get_search_spec()
            oItem = {'name': item.name, 'single': oSearch['single'], 'line_list': oSearch['line_list']}
            lBack.append(oItem)
        return lBack

    def delete(self, using = None, keep_parents = False):
        """Delete all items pointing to me, then delete myself"""

        # Delete the global variables
        gvar_set = self.globalvariables.all()
        for gvar in gvar_set:
            gvar.delete()
        # Delete the definition variables
        dvar_set = self.definitionvariables.all()
        for dvar in dvar_set:
            dvar.delete()
        # Delete the constructions (and what is under them)
        cns_set = self.constructions.all()
        for cns_this in cns_set:
            cns_this.delete()
        # Now perform the normal deletion
        return super().delete(using, keep_parents)

    def get_vardef_list(self):
        # Get a list of all variables for this gateway
        #var_pk_list = [var.pk for var in self.gatewayvariables.all()]
        ## Now get the list of vardef variables coinciding with this
        #vardef_list = [var for var in VarDef.objects.filter(pk__in=var_pk_list)]
        vardef_list = self.definitionvariables.all().order_by('order')
        return vardef_list

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

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
      # Save the gateway
      response = super().save(force_insert, force_update, using, update_fields)
      # Adapt the saved date of the research project
      if Research.objects.filter(gateway=self).first() != None:
          self.research.save()
      return response


class Construction(models.Model):
    """A search construction consists of a [search] element and one or more search items"""

    # [1] Construction name
    name = models.CharField("Name of this search construction", max_length=MAX_TEXT_LEN)
    # [1] Main search item
    search = models.ForeignKey(SearchMain, blank=False, null=False)
    # [1] Every gateway has one or more constructions it may look for
    gateway = models.ForeignKey(Gateway, blank=False, null=False, related_name="constructions")

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

        # Delete the global variables
        cvar_set = self.constructionvariables.all()
        for cvar in cvar_set:
            cvar.delete()
        # Also delete the searchMain
        self.search.delete()
        # And then delete myself
        return super().delete(using, keep_parents)

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None, check_cvar = True):
      save_result = super().save(force_insert, force_update, using, update_fields)
      # Check and add/delete CVAR instances for this gateway
      if check_cvar:
          Gateway.check_cvar(self.gateway)
      # Return the result of normal saving
      return save_result

    def get_dvars(self):
        """Get a list of all data-dependant variables for this construction"""
        qs = ConstructionVariable.objects.filter(construction=self).order_by('variable__order')
        return qs

    def get_code(self, format):
        """Produce the Xuery code for the indicated format"""

        return ""

      
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
    gateway = models.ForeignKey(Gateway, blank=False, null=False, related_name="definitionvariables")

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
      # Perform the normal saving
      save_result = super().save(force_insert, force_update, using, update_fields)
      # Check and add/delete CVAR instances for this gateway
      Gateway.check_cvar(self.gateway)
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
        new_copy = VarDef(name=self.name, description=self.description, order=self.order, gateway=kwargs['gateway'])
        new_copy.save()
        # Return the new copy
        return new_copy

    def delete(self, using = None, keep_parents = False):
        """Deleting a VarDef means: also delete all the CVAR instances pointing to me"""

        # Delete the CVAR instances under me
        for var_inst in self.variablenames.all():
            var_inst.delete()
        # Now delete myself
        result = super().delete(using, keep_parents)
        # re-order the dvar collection under this gateway
        gateway.order_dvar()
        # Return the result
        return result


class GlobalVariable(Variable):
    """Each research project may have any number of global (static) variables"""

    # [1] Value of the variable
    value = models.TextField("Value")
    # [1] Link to the Gateway the variable belongs to
    gateway = models.ForeignKey(Gateway, blank=False, null=False, related_name="globalvariables")

    def __str__(self):
        # The default string-value of a global variable is its name
        return self.name

    def get_copy(self, **kwargs):
        # Test
        if kwargs == None or 'gateway' not in kwargs:
            return None
        # Make a clean copy
        new_copy = GlobalVariable(name=self.name, description=self.description, order=self.order, value=self.value, gateway=kwargs['gateway'])
        new_copy.save()
        # Return the new copy
        return new_copy

    def can_delete(self):
        # A global variable can only be deleted, if it is not referred to from functions anymore
        qs = Argument.objects.filter(gvar=self)
        # The gvar can be deleted if the queryset is empty
        return qs.count() == 0

    def delete(self, using = None, keep_parents = False):
        # Delete myself
        result = super().delete(using, keep_parents)
        # TODO: re-order the gvar collection
        gateway.order_gvar()
        # Return the deletion result
        return result


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


class Function(models.Model):
    """Realization of one function based on a definition"""

    # [1] Must point to a definition
    functiondef = models.ForeignKey(FunctionDef, null=False)
    # [0-1] A function belongs to a construction variable - but this is not necessarily the parent
    root = models.ForeignKey("ConstructionVariable", null=True, related_name="functionroot")
    # [0-1] Alternatively, a function belongs to a condition
    rootcond = models.ForeignKey("Condition", null=True, related_name="functioncondroot")
    # [0-1] A function MAY belong to a particular ARGUMENT, which then is its parent
    parent = models.ForeignKey("Argument", null=True, blank=True, related_name="functionparent")
    # [0-1] The output type of the function. May be unknown initially and then calculated
    type = models.CharField("Type", blank=True, choices=build_choice_list(SEARCH_TYPE), 
                              max_length=5, help_text=get_help(SEARCH_TYPE))
    # [1] The value that is the outcome of this function
    #     This is a JSON list, so can be bool, int, string of any number
    output = models.TextField("JSON value", null=False, blank=True, default="[]")

    def __str__(self):
        return "f_{}:{}".format(self.id,self.output)

    def get_copy(self, **kwargs):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Skip FK fields: functiondef, root
        # Copy all 12m fields
        copy_m2m(self, new_copy, "functionarguments")    # Argument
        # Return the new copy
        return new_copy

    def delete(self, using = None, keep_parents = False):
        # First delete any ARG elements pointing to me
        # qs = self.argument_set.all()
        qs = self.functionarguments.all()
        for arg in qs:
            arg.delete()
        # Now delete myself
        result = super().delete(using, keep_parents)
        # # Save the changes
        # self.save()
        return result

    @classmethod
    def create(cls, functiondef, functionroot, functioncondroot, parentarg):
        """Create a new instance of a function based on a 'function definition', binding it to a cvar or a condition"""
        with transaction.atomic():
            if parentarg == None:
                if functionroot != None:
                    inst = cls(functiondef=functiondef, root=functionroot)
                elif functioncondroot != None:
                    inst = cls(functiondef=functiondef, rootcond=functioncondroot)
                else:
                    # This should actually create an error...
                    inst = cls(functiondef=functiondef)
            else:
                # There is a parentarg
                if functionroot != None:
                    inst = cls(functiondef=functiondef, root=functionroot, parent=parentarg)
                elif functioncondroot != None:
                    inst = cls(functiondef=functiondef, rootcond=functioncondroot, parent=parentarg)
                else:
                    # This should actually create an error...
                    inst = cls(functiondef=functiondef, parent=parentarg)
            # Save this function
            inst.save()
            # Add all the arguments that are needed
            for argdef in functiondef.arguments.all():
                arg = Argument(argumentdef=argdef, argtype=argdef.argtype, 
                               functiondef=functiondef, function=inst)
                # Save this argument
                arg.save()
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
        iLine = 0
        id = self.id
        start_function = self.root.function
        lFunc = start_function.get_functions()
        for idx in range(len(lFunc)):
            if lFunc[idx].id == id:
                iLine = idx+1
                break
        return iLine

    def get_functions(self):
        """Get all the functions including myself and those descending under me"""

        func_this = self
        func_list = [func_this]
        # Walk all arguments
        for arg_this in func_this.functionarguments.all():
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
            # Get the information of this parent-argument
            info = {'level': iLevel, 
                    'arginfo': parentarg.get_info(),
                    'func_id': parentarg.function.id,
                    'arg_num': parentarg.function.functiondef.argnum,
                    'arg_order': parentarg.argumentdef.order,
                    'arg_id': arg_id,
                    'cvar_id': self.root.id,
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
        qs = self.functionarguments.all().order_by('argumentdef__order')
        return qs

          
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

    def __str__(self):
        return "argdef_{}".format(self.id)


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
    # [0-1] This argument may link to a Data-dependant Variable
    dvar = models.ForeignKey("VarDef", null=True)
    ## [0-1] This argument may link to a Constituent
    #constituent = models.ForeignKey("Constituent", null=True)
    # [0-1] This argument may link to a Hierarchical Relation
    relation = models.ForeignKey("Relation", null=True)
    # [0-1] This argument may link to a Function (not its definition)
    function = models.ForeignKey("Function", null=True, related_name ="functionarguments")
    # [0-1] If a function is needed, we need to have a link to its definition
    functiondef = models.ForeignKey(FunctionDef, null=True)

    def __str__(self):
        return "arg_{}".format(self.id)

    def get_copy(self, **kwargs):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Skip FK fields: argumentdef, functiondef
        # TODO: how to properly process: gvar, cvar??
        # Copy a potential function pointing to me
        copy_m2m(self, new_copy, "functionparent")    # Function
        # Return the new copy
        return new_copy

    def delete(self, using = None, keep_parents = False):
      # Check if there are any functions pointing to me
      func_child = self.functionparent.first()
      if func_child != None:
          func_child.delete()
      # Now delete myself
      result = super().delete(using, keep_parents)
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
        elif self.argtype == "axis":
            avalue = self.relation.name
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
        elif self.argtype == "axis":
            if self.relation != None:
                avalue = "r:{}".format(self.relation.name)
        return avalue


class Relation(models.Model):
    """Hierarchical relation such as the Xpath axes"""

    # [1] The descriptive name of this argument
    name = models.CharField("Name", max_length=MAX_TEXT_LEN)
    # [1] Xpath implementation
    xpath = models.TextField("Implementation", null=False, blank=False, default=".")

    def __str__(self):
        return "{}".format(self.name)
    

class ConstructionVariable(models.Model):
    """Each construction may provide its own value to the variables belonging to the gateway"""

    # [1] Link to the Construction the variable value belongs to
    construction = models.ForeignKey(Construction, blank=False, null=False, related_name="constructionvariables")
    # [1] Link to the name of this variable
    variable = models.ForeignKey(VarDef,  blank=False, null=False, related_name="variablenames")
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
        return "[{}|{}]".format(sConstruction, sVariable)

    def get_copy(self, **kwargs):
        # Make a clean copy of the CVAR, but don't save it yet
        new_copy = get_instance_copy(self, commit=False)
        # Set the construction and the variable correctly
        new_copy.construction = kwargs['construction']
        new_copy.variable = kwargs['variable']
        # Copy the function associated with the current CVAR
        if self.function != None:
            function = self.function.get_copy()
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

    def get_code(self, format):
        """Provide Xquery code for this cns var"""
        sCode = "concat('{}', '{}')".format(self.type, format)
        if self.type == "gvar":
            sCode = "$_{}".format(self.gvar.name)
        elif self.type == "fixed":
            sCode = "'{}'".format(self.svalue)
        elif self.type == "func":
            sCode = sCode
        return sCode

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
        return super().save(force_insert, force_update, using, update_fields)

    def delete(self, using = None, keep_parents = False):
        """Delete a CVAR"""

        # Delete all that is pointing to me
        # Check if this CVAR can be deleted
        qs = Argument.objects.filter(cvar=self)
        for arg_inst in qs:
            # Delete this argument
            arg_inst.delete()
        # Now delete myself
        return super().delete(using, keep_parents)

    def get_functions(self):
        """Get all the functions belonging to this construction variable"""

        func_list = []
        # Only works for the correct type
        if self.type == "calc":
            func_this = self.function
            if func_this != None:
                # Add function to list
                func_list.append(func_this)
                # Walk all arguments
                for arg_this in func_this.functionarguments.all():
                    # CHeck if this is a function argument
                    if arg_this.argtype == "func":
                        # Then add the function pointed to by the argument
                        arg_func = arg_this.functionparent.first()
                        if arg_func != None:
                            arg_func_list = arg_func.get_functions()
                            for func in arg_func_list:
                                func_list.append(func)
        return func_list

    
class Condition(models.Model):
    """Each research project may contain any number of conditions defining a search hit"""

    # [1] Condition name
    name = models.CharField("Name", max_length=MAX_TEXT_LEN)
    # [0-1] Description of the condition
    description = models.TextField("Description", blank=True)
    # [1] A condition is a boolean, and can be of two types: Function or Cvar
    condtype = models.CharField("Condition type", choices=build_abbr_list(SEARCH_CONDTYPE), 
                              max_length=5, help_text=get_help(SEARCH_CONDTYPE))
    # [0-1] One option for a condition is to be equal to the value of a data-dependant variable
    variable = models.ForeignKey(VarDef, null=True, related_name ="variablecondition")

    # [0-1] Another option for a condition is to be defined in a function
    function = models.OneToOneField(Function, null=True)
    # [0-1] If a function is needed, we need to have a link to its definition
    functiondef = models.ForeignKey(FunctionDef, null=True, related_name ="functiondefcondition")

    # [1] Every gateway has zero or more conditions it may look for
    gateway = models.ForeignKey(Gateway, blank=False, null=False, related_name="conditions")

    def __str__(self):
        return self.name

    def get_copy(self, **kwargs):
        """Make a copy of this condition"""

        # Test for the existence of 'gateway'
        if kwargs == None or 'gateway' not in kwargs:
            return None
        # If there is a function, copy it
        new_function = None
        if self.function != None:
            new_function = self.function.get_copy()
        new_copy = Condition(name=self.name, description=self.description,
                             condtype=self.condtype, cvar=self.cvar,
                             functiondef=self.functiondef,
                             function=new_function, gateway=kwargs['gateway'])
        # Return the new copy
        return new_copy

    def get_code(self, format):
        """Create and return the required Xquery"""
        sCode = ""
        if self.condtype == "dvar":
            if self.variable == None:
                # sCode = "$undefined_{}".format(self.name)
                sCode = ""
            else:
                # A variable has been defined
                sCode = "${}".format(self.variable.name)
        else:
            # This is a function
            sCode = "$TODO"
        return sCode
      
    def delete(self, using = None, keep_parents = False):
        """Delete all items pointing to me, then delete myself"""

        # Delete the function(s) pointing to me
        if self.function != None:
            self.function.delete()
        # NOTE: do not delete the functiondef, gateway or cvar -- those are independant of me
        # And then delete myself
        return super().delete(using, keep_parents)

      
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
    gateway = models.OneToOneField(Gateway, blank=False, null=False)
    # [1] Each research project has its owner: obligatory, but not to be selected by the user himself
    owner = models.ForeignKey(User, editable=False)
    # [0-1] create date and lastsave date
    created = models.DateTimeField(default=timezone.now)
    saved = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
      # Adapt the save date
      # self.saved = datetime.now()
      self.saved = timezone.now()
      response = super().save(force_insert, force_update, using, update_fields)
      return response

    def gateway_name(self):
        return self.gateway.name

    def delete(self, using = None, keep_parents = False):
        # Look for the gateway
        try:
            gateway = self.gateway
            gateway.delete()
        except:
            if self.gateway_id:
                gateway = Gateway.objects.filter(id=self.gateway_id)
                if gateway:
                    gateway.delete()
        # Delete all the sharegroup instances pointing to this research instance
        for grp in self.sharegroups.all():
            grp.delete()
        # Delete myself
        return super().delete(using, keep_parents)

    def username(self):
        return self.owner.username

    def get_copy(self, **kwargs):
        # Make a clean copy
        new_copy = get_instance_copy(self, commit=False)
        # Copy the FK contents
        copy_fk(self, new_copy, "gateway")
        # Adapt the name of the project to reflect that this is a copy
        lstQ = []
        # Make it user-independent...
        # lstQ.append(Q(owner=self.owner))
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

    def get_delete_url(self):
        """Produce an URL to be called when requesting to delete [self]"""

        return reverse('seeker_delete', kwargs={'object_id': self.id})

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

    def to_xquery(self, partId, sFormat, bRefresh):
        """Translate project into Xquery"""

        # Import the correct function
        from cesar.seeker.convert import ConvertProjectToXquery

        # Validate
        if partId == None or partId == "" or sFormat == None or sFormat == "":
            return None

        # Prepare data
        oData = {'targetType': self.targetType,
                 'format': sFormat,
                 'gateway': self.gateway}
        # First: check and see if there is no 'basket' yet for the combination of part/format
        part = Part.objects.filter(id=partId).first()
        lstQ = []
        lstQ.append(Q(research=self))
        lstQ.append(Q(format=sFormat))
        lstQ.append(Q(part=part))
        qs = Basket.objects.filter(*lstQ)
        if qs.count() == 0:
            # So: create one
            basket = Basket(research=self, part=part, format=sFormat, status="created", jobid="")
            # Create the Xquery code
            basket.codedef, basket.codeqry = ConvertProjectToXquery(oData)
            # Save the basket
            basket.save()
        else:
            # Return the existing one
            basket = qs[0]
            # Check if we have Xquery code and there is no 'error' status
            if bRefresh or basket.codedef == "" or basket.codeqry == "" or basket.status == "error":
                # Create the Xquery code
                basket.codedef, basket.codeqry = ConvertProjectToXquery(oData)
                # Save the basket
                basket.save()
        # Return the basket
        return basket

    def execute(self, partId, sFormat):
        """Send command to /crpp to start the project"""

        oErr = ErrHandle()
        # Import the correct function
        from cesar.seeker.convert import ConvertProjectToCrpx
        # Prepare reply
        oBack = {'status': 'ok', 'msg': ''}
        # Get the correct Basket
        try:
            bRefresh = True # Make sure that Xquery is calculated afresh
            basket = self.to_xquery(partId, sFormat, bRefresh)
            # Check on what was returned
            if basket == None:
                if partId == None or partId == "":
                    sMsg = "First specify a corpus (or a part of a corpus) to search in"
                else:
                    sMsg = "Something is wrong. Cesar is unable to execute"
                oBack['msg'] = sMsg
                oBack['status'] = 'error'
                return oBack
        except:
            oBack['msg'] = 'Failed to convert project to Xquery'
            oBack['status'] = 'error'
            return oBack
        # Add basket to the return object, provided all went well
        oBack['basket'] = basket
        # Create CRPX project
        basket.set_status("create_crpx")
        try:
            sCrpxName, sCrpxText = ConvertProjectToCrpx(basket)
        except:
            oBack['msg'] = 'Failed to convert project to Crpx'
            oBack['status'] = 'error'
            return oBack

        # Check what is returned
        if sCrpxName == "":
            # An error has returned
            oBack['status'] = 'error'
            oBack['msg'] = "/n".join(sCrpxText)
            return oBack

        # Send the CRPX to /crpp and execute it
        try:
            # Get the userid
            sUser = self.owner.username
            # First send over the CRP code
            basket.set_status("send_crpx")
            oCrpp = crpp_send_crp(sUser, sCrpxText, sCrpxName)
            if oCrpp['commandstatus'] == 'ok':
                basket.set_status("issue_exe")
                # Last information
                sLng = basket.part.corpus.get_lng_display()   # Language of the corpus
                sDir = basket.part.dir          # Directory where the part is located
                # Now start execution
                oCrpp = crpp_exe(sUser, sCrpxName, sLng, sDir)      
                if oCrpp['commandstatus'] == 'ok':   
                    # Get the status object
                    oExeStatus = oCrpp['status']
                    # NOTE: the exeStatus may be a string or an object (hmmm)
                    if oExeStatus == "error":
                        # The server is complaining, it seems
                        oBack['msg'] = 'The server gives an error'
                        if 'code' in oCrpp:
                            oBack['msg'] += "<br>Code: " + oCrpp['code']
                        if 'message' in oCrpp:
                            oBack['msg'] += "<br>Message: " + oCrpp['message']
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
                oBack['msg'] = 'Could not send CRP to /crpp'
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
    part = models.ForeignKey(Part, blank=False, null=False)
    # [1] The Xquery definitions (targeted for the corpus)
    codedef = models.TextField("Xquery definitions", blank=True)
    # [1] The Xquery code for the main query
    codeqry = models.TextField("Xquery main query", blank=True)
    # [1] The status of (a) code generation and (b) execution
    status = models.CharField("Status", max_length=MAX_TEXT_LEN)
    # [0-1] The jobid generated by /crpp
    jobid = models.CharField("Job identifier", max_length=MAX_NAME_LEN, blank=True)
    # [0-1] create date and lastsave date
    created = models.DateTimeField(default=timezone.now)
    saved = models.DateTimeField(null=True, blank=True)
    # [1] Each basket is linked to one research project
    research = models.ForeignKey(Research, blank=False, null=False, related_name="baskets")

    def __str__(self):
        # COmbine: research project name, research id, processing status
        return "{}_{}: {}".format(self.research.name, self.id, self.status)

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
        # Adapt the save date
        self.saved = timezone.now()
        response = super().save(force_insert, force_update, using, update_fields)
        return response

    def set_status(self, sStatus):
        self.status = sStatus
        self.save()
        return True

    def set_jobid(self, jobid):
        self.jobid = jobid
        self.save()
        return True

    def get_progress(self):
        """Issue a progress request for this job and return the status"""

        # Initialise the status
        oBack = {'commandstatus': 'ok'}
        oErr = ErrHandle()
        try:
            # Issue a status request
            sUser = self.research.owner.username
            oCrpp = crpp_status(sUser, self.jobid)
            if oCrpp['commandstatus'] == 'ok':
                for item in oCrpp:
                    if item != 'commandstatus':
                        oBack[item] = oCrpp[item]
            else:
                oBack['commandstatus'] = 'error'
                oBack['msg'] = oCrpp['message']

        except:
            oBack['commandstatus'] = "error"
            oBack['msg'] = oErr.DoError("get_progress error")

        # And then we return what we have
        return oBack

    def set_quantor(self, oResults):
        """Get or create a quantor and put all the results from [oResults] into it"""

        oErr = ErrHandle()
        try:
            # Get all quantors (if any) still attached to me
            qs = Quantor.objects.filter(basket=self)
            # Remove them
            qs.delete()

            # Preparation: get necessary instances
            instPart = self.part
            instFormat = choice_value(CORPUS_FORMAT, self.format)

            # Do all in one go
            with transaction.atomic():
                iNumQc = len(oResults['table'])
                # Create a completely new quantor
                quantor = Quantor(basket=self, searchTime=oResults['searchTime'],
                                  total=oResults['total'], qcNum=iNumQc)
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
                    for subnum in range(0, numsubcats):
                        # Get or create this subject
                        qsubcat = Qsubcat(qcline=qcline, 
                                          name=oQcResults['subcats'][subnum],
                                          count=oQcResults['counts'][subnum])
                        qsubcat.save()
                        subcats.append(qsubcat)
                    for hit in oQcResults['hits']:
                        # Find the text within the appropriate part/format
                        text = Text.find_text(instPart, instFormat, hit['file'])
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
 
            # Create KWIC material for each QC line
            for idx in range(0, iNumQc):
                self.set_kwic(idx+1)

            # REturn positively
            return True
        except:
            # Failure
            oErr.DoError('set_quantor could not read the hit information')
            return False

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

    def set_kwic(self, iQcLine):
        """Check if a KWIC table is available; otherwise make one"""

        oErr = ErrHandle()
        try:
            # Get the number of results from the associated QCline object
            lstQ = []
            lstQ.append(Q(quantor__basket = self))
            lstQ.append(Q(qc=iQcLine))
            oQcLine = QCline.objects.filter().first()
            if oQcLine == None:
                # No results can be retrieved
                return False
            quantor_count_for_this_qc = oQcLine.count

            # Get the /crpp/dbinfo count for this QC line
            sUser = self.research.owner
            sCrpName = self.research.name
            oDbInfoBack = crpp_dbinfo(sUser, sCrpName, iQcLine, -1, 0)
            if oDbInfoBack['commandstatus'] != 'ok':
                oErr.DoError("set_kwic: didn't get a positive reply from /crpp/dbinfo")
                # Cannot get a positive reply
                return False
            dbinfo_count_for_this_qc = oDbInfoBack['Size']

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
        return kwic.kwicfilters.all()



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
    # [1] There must be a link to the Basket the results belong to
    basket = models.ForeignKey(Basket, blank=False, null=False, related_name="kwiclines")

    def __str__(self):
        return "{}".format(self.qc)

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

    def apply_filter(self, oFilter=None):
        oErr = ErrHandle()
        # Combine all filters into a JSON object to be sent
        if oFilter == None:
            oFilter = self.get_filter()
        # Send to /crpp/dbinfo to get the correct amounts
        sUser = self.basket.research.owner.username
        sCrpName = self.basket.research.name
        iQcLine = self.qc
        oDbInfoBack = crpp_dbinfo(sUser, sCrpName, iQcLine, -1, 0, filter=oFilter)
        if oDbInfoBack['commandstatus'] != 'ok':
            oErr.DoError("set_kwic: didn't get a positive reply from /crpp/dbinfo")
            # Cannot get a positive reply
            return False
        # Adapt the hitcount
        self.hitcount = oDbInfoBack['Size']
        self.save()
        # REturn positively
        return True


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
    kwic = models.ForeignKey(Kwic, blank=False, null=False, related_name="kwicfilters")

    def __str__(self):
        return "{}".format(self.field)


class Quantor(models.Model):
    """QUantificational results of executing one basket"""

    # [1] A Quantor is linked to a basket
    basket = models.ForeignKey(Basket, blank=False, null=False)
    # [1] THe number of files (texts) that have been searched
    total = models.IntegerField("Number of files", default=0)
    # [1] Keep the number of milliseconds the search took
    searchTime = models.IntegerField("Search time (ms)", default=0)
    # [1] Need to know the number of QCs for this search
    qcNum = models.IntegerField("Number of query lines", default=1)

    def __str__(self):
        return "{}".format(self.count)

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
            response = super().delete(using, keep_parents)
        return response


class QCline(models.Model):

    # [1] A subcategory belongs to a particular QC of the quantor
    qc = models.IntegerField("QC number", default=1)
    # [1] The number of hits for this QC line
    count = models.IntegerField("Number of hits", default=0)
    # [1] Every QCline is linked to a Quantor with results
    quantor = models.ForeignKey(Quantor, blank=False, null=False, related_name="qclines")

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
    qcline = models.ForeignKey(QCline, blank=False, null=False, related_name="qsubcats")

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
    subcat = models.ForeignKey(Qsubcat, blank=False, null=False, related_name="qsubinfos")
    # [1] subcatinfo also links to a Text (which is under the part)
    text = models.ForeignKey(Text, blank=False, null=False)
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
    group = models.ForeignKey(Group, blank=False, null=False)
    # [1] THe permissions granted to this group
    permission = models.CharField("Permissions", choices=build_abbr_list(SEARCH_PERMISSION), 
                              max_length=5, help_text=get_help(SEARCH_PERMISSION))
    # [1] Each Research object can be shared with any number of groups
    research = models.ForeignKey(Research, blank=False, null=False, related_name="sharegroups")

    def __str__(self):
        return "{}-{}".format(self.group, self.permission)

