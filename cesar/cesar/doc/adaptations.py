"""
Adaptations of the database that are called up from the (list)views in the DOC app.
"""

from django.db import transaction
import re
import json


# ======= imports from my own application ======
from cesar.utils import ErrHandle
from cesar.basic.models import Information
from cesar.doc.models import Expression, FrogLink

adaptation_list = {
    "doc_list": ["expressionfrogged"]
    }


def listview_adaptations(lv, **kwargs):
    """Perform adaptations specific for this listview"""

    oErr = ErrHandle()
    try:
        if lv in adaptation_list:
            for adapt in adaptation_list.get(lv):
                sh_done  = Information.get_kvalue(adapt)
                if sh_done == None or sh_done != "done":
                    # Do the adaptation, depending on what it is
                    method_to_call = "adapt_{}".format(adapt)
                    bResult, msg = globals()[method_to_call](**kwargs)
                    if bResult:
                        # Success
                        Information.set_kvalue(adapt, "done")
    except:
        msg = oErr.get_error_message()
        oErr.DoError("listview_adaptations")

# =========== Part of doc_list ==================

def adapt_expressionfrogged(**kwargs):
    oErr = ErrHandle()
    bResult = True
    msg = ""

    try:
        # Find out who I am
        username = kwargs.get('username', '')
        # Create a list of all current expressions
        lst_mwe = []
        lst_expression = []
        for oItem in Expression.objects.all().order_by('id').values('id', 'full'):
            lst_mwe.append(oItem['full'])
            lst_expression.append(oItem['id'])
        # Convert into a text
        sText = "\n".join(lst_mwe)
        # Get a list of lines with lemma's
        bFound, lst_lemmas = FrogLink.get_lemmas(username, sText)
        if bFound:
            if not lst_lemmas is None and len(lst_lemmas) == len(lst_mwe):
                for idx, lst_line in enumerate(lst_lemmas):
                    # Put the list of lemma's in the correct object
                    obj = Expression.objects.filter(id=lst_expression[idx]).first()
                    if obj is None:
                        iStop = 1
                    else:
                        # Found the right object
                        obj.frogged = json.dumps(lst_line)
                        obj.save()

            bResult = True
    except:
        bResult = False
        msg = oErr.get_error_message()
    return bResult, msg

