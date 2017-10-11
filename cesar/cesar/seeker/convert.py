"""Convert project into Xquery and convert code to CRPX"""
import json
import xml
import re
from django.template import loader, Context
from cesar import utils
from cesar.seeker.models import Construction, ConstructionVariable

def ConvertProjectToXquery(oData):
    """Convert the project oData.gateway of type oData.targetType into Xquery suitable for oData.format"""

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
            # search_list = [{'name': item.name, 'value': item.search.value} for item in constructions]
            search_list = gateway.get_search_list()
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
            cond_list = []
            for cnd in gateway.conditions.all():
                sCode = cnd.get_code(format)
                if sCode != "":
                    cond_list.append(sCode)

            context = dict(gvar_list=gvars, 
                           cons_list=constructions, 
                           search_list=search_list,
                           dvar_list=dvar_list,
                           cond_list=cond_list)

            # Action depends on the target type
            if targetType == "w":
                # Step #1: make the start of the main query
                sCodeQry = loader.get_template(template_main).render(context)
                sCodeQry = re.sub(r'\n\s*\n', '\n', sCodeQry).strip()
                # Step #2: create the definitions part
                sCodeDef = loader.get_template(template_def).render(context)
                sCodeDef = re.sub(r'\n\s*\n', '\n', sCodeDef).strip()
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

def ConvertProjectToCrpx(basket):
    """Convert the research project oDate.research_id to a CRPX file"""

    sCrpxName = ""
    sCrpxContent = ""
    template_crp = "seeker/crp.xml"

    try:
        # Access the research project and the gateway
        research = basket.research
        gateway = research.gateway

        # Get the name of the project
        sCrpxName = research.name

        # The format of what we process
        format = basket.format
        if format == "psdx":
            extension = ".psdx"
            project_type = "Xquery-psdx"
        elif format == "folia":
            extension = ".folia.xml"
            project_type = "Xquery-folia"
        else:
            extension = ""
            project_type = ""

        # The language and location of what we process
        lng = basket.part.corpus.get_lng_display()
        dir = basket.part.dir

        # Create a context for the template
        context = dict(gateway=gateway, 
                       research=research,
                       extension=extension,
                       lng=lng,
                       dir=dir,
                       project_type=project_type,
                       created=basket.created,
                       codedef=basket.codedef,
                       codeqry=basket.codeqry)
        # Convert template
        sCrpxContent = loader.get_template(template_crp).render(context)
        sCrpxContent = re.sub(r'\n\s*\n', '\n', sCrpxContent).strip()

    except:
        # Show error message
        oErr.DoError("ConvertProjectToCrpx error: ")

    return sCrpxName, sCrpxContent


