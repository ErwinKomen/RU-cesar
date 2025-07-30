"""Models for the Translation app."""

import json
from django.db import models
from django.utils import timezone
import requests
from requests.auth import HTTPBasicAuth


# ========= own application
from cesar.utils import ErrHandle

MAXPARAMLEN = 100
MAX_NAME_LEN = 50
MAX_STRING_LEN = 255

def get_crpp_date(dtThis):
    """Convert datetime to string"""

    # Model: yyyy-MM-dd'T'HH:mm:ss
    sDate = dtThis.strftime("%Y-%m-%dT%H:%M:%S")
    return sDate

# =================================== APP MODELS ===================================================


class Action(models.Model):
    """Action by a user of an application"""

    # [1] Application name
    appname = models.CharField("Application name", max_length=MAXPARAMLEN)
    # [1] User name within Cesax
    username = models.CharField("Application user", max_length=MAXPARAMLEN)
    # [1] Computer name used to run Cesax
    computer = models.CharField("Computer name", max_length=MAXPARAMLEN)
    # [0-1] Type of file (e.g. psdx, corpus) or language (xquery, penn-psd)
    ftype = models.CharField("File type", max_length=MAXPARAMLEN)
    # [0-1] Name of file or project involved
    fname = models.CharField("File name", max_length=MAXPARAMLEN)

    # [1] Date when this action was saved
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        sApp = self.appname
        sName = self.username
        if self.created:
            sDate = get_crpp_date(self.created)
        else:
            sDate = "-"
        msg = "{}/{}: {}".format(sApp, sName, sDate)
        return msg

    def get_value(self, key=None):
        """Given a key, provide its value, or NONE if it does not exist"""

        oErr = ErrHandle()
        value = None
        try:
            if key is None:
                value = self.__str__()
        except:
            msg = oErr.get_error_message()
            oErr.DoError("Action/get_value")
        return value






