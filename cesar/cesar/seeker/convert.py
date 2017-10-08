"""Convert project into Xquery and convert code to CRPX"""
import json
import xml
from django.template import loader, Context
from cesar import utils
from cesar.seeker.models import Construction, ConstructionVariable

def ConvertProjectToXquery(oData):
    sCodeDef = ""
    sCodeQry = ""
    template_main = ""
    template_def = ""
    oErr = utils.ErrHandle()

    try:
        # Unpack the data from [oData]
        targetType = oData['targetType']
        gateway = oData['gateway']
        format = oData['format']

        # Determine which template to use
        if format == 'psdx':
            template_main = 'seeker/main_psdx.xq'
            template_def = 'seeker/def_psdx.xq'
        elif format == 'folia':
            template_main = 'seeker/main_folia.xq'
            template_def = 'seeker/def_folia.xq'
        
        # Is everything okay?
        if template_main != "":
            
            # Collect all relevant information
            gvars = gateway.globalvariables.all()
            # Search elements are the 'constructions'
            constructions = gateway.constructions.all()
            search_list = [{'name': item.name, 'value': item.search.value} for item in constructions]
            # The data-dependant variables need to be divided over the search elements
            dvar_list = []
            for var in gateway.definitionvariables.all():
                cvar_list = []
                for cons in constructions:
                    # Determine what the construction variable is
                    cvar = ConstructionVariable.objects.filter(construction=cons, variable=var).first()
                    oCvarInfo = {'grp': cons.name, 'code': cvar.get_code(format)}
                    cvar_list.append(oCvarInfo)
                # Add the cvar_list to the dvar_list
                oDvarInfo = {'name': var.name, 'cvar_list': cvar_list}
                dvar_list.append(oDvarInfo)
            # Also add the conditions
            cond_list = [cnd.get_code(format) for cnd in gateway.conditions.all()]

            context = dict(gvar_list=gvars, 
                           cons_list=constructions, 
                           search_list=search_list,
                           dvar_list=dvar_list,
                           cond_list=cond_list)

            # Action depends on the target type
            if targetType == "w":
                # Step #1: make the start of the main query
                sCodeQry = loader.get_template(template_main).render(context)
                sCodeDef = loader.get_template(template_def).render(context)
            elif targetType == "c":
                # TODO: make code for constituent-level queries
                todo = True

    except:
        # Show error message
        oErr.DoError("ConvertProjectToXquery error: ")
        # REset the values for definitions and query
        sCodeDef = ""
        sCodeQry = ""

    # Return what has been produced
    return sCodeDef, sCodeQry

def ConvertProjectToCrpx(oData):

    sCrpxName = ""
    sCrpxContent = ""
    return sCrpxName, sCrpxContent
